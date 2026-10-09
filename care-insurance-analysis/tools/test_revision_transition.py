import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from test_verify_handoff import package
from verify_handoff import check_repository, fingerprint


class RevisionTransitionTests(unittest.TestCase):
    def fixture(self, root):
        p = package()
        reports = {
            r: {"schema": "care_handoff/v1", "role": r, "plan_revision": "2.2",
                "status": "completed" if r == "20" else "candidate_saved",
                "candidate": p["candidate"], "candidate_fingerprint": fingerprint(p),
                "verdict": "FAIL" if r == "20" else "PROPOSAL_ONLY"}
            for r in ("10", "20", "30")
        }
        (root / "reports").mkdir()
        (root / "checks").mkdir()
        blobs = {}
        for role, report in reports.items():
            b = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode()
            (root / "reports" / (role + ".json")).write_bytes(b)
            blobs[role] = hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()
        state = {
            "writer": "00", "plan_revision": "2.3", "inputs": {"S01": {"sha256": "a" * 64}},
            "outputs": {"candidate": {"release_status": "not_released"}},
            "plan_change": {"previous_revision": "2.2", "current_revision": "2.3",
                            "retained_historical_report_blobs": blobs,
                            "retained_candidate": {**p["candidate"], "candidate_fingerprint": fingerprint(p)}}
        }
        self.write(root / "STATE.json", state)
        self.write(root / "checks/candidate.json", p)
        (root / "PLAN.md").write_text("revision: '2.3'\n", encoding="utf-8")
        return state, p, reports

    def write(self, path, value):
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def test_old_failure_stays_old_and_pending(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); self.fixture(root)
            r = check_repository(root)
            self.assertEqual(r["analysis"], "REVISED_PLAN_AWAITING_NEW_CANDIDATE")
            self.assertEqual(r["retained_evaluation"], "FAIL")

    def test_old_report_must_not_be_rewritten(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); _, _, reports = self.fixture(root)
            reports["20"]["verdict"] = "PASS"
            self.write(root / "reports/20.json", reports["20"])
            with self.assertRaisesRegex(ValueError, "historical report changed"): check_repository(root)

    def test_missing_package_is_not_analysis_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); self.fixture(root); (root / "checks/candidate.json").unlink()
            r = check_repository(root)
            self.assertEqual(r["handoff"], "METADATA_ONLY")
            self.assertNotIn("valid_metrics", r)

    def test_new_candidate_waits_for_new_evaluation(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); _, p, reports = self.fixture(root)
            p["plan_revision"] = "2.3"; p["candidate"]["version"] = 2
            self.write(root / "checks/candidate.json", p)
            reports["10"].update(plan_revision="2.3", candidate=p["candidate"],
                                 candidate_fingerprint=fingerprint(p))
            self.write(root / "reports/10.json", reports["10"])
            r = check_repository(root)
            self.assertEqual(r["independent_evaluation"], "evaluation_pending_plan_revision")

    def test_unapproved_revision_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); state, _, _ = self.fixture(root)
            state.pop("plan_change"); self.write(root / "STATE.json", state)
            with self.assertRaisesRegex(ValueError, "revision mismatch"): check_repository(root)

    def test_new_plan_cannot_omit_supplement_hash(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); state, p, reports = self.fixture(root)
            state["inputs"]["S10"] = {"sha256": "d" * 64}
            self.write(root / "STATE.json", state)
            p["plan_revision"] = "2.3"; p["candidate"]["version"] = 2
            self.write(root / "checks/candidate.json", p)
            reports["10"].update(plan_revision="2.3", candidate=p["candidate"],
                                 candidate_fingerprint=fingerprint(p))
            self.write(root / "reports/10.json", reports["10"])
            with self.assertRaisesRegex(ValueError, "fixed S10 input hash"):
                check_repository(root)
            p["input_hashes"]["S10"] = "d" * 64
            self.write(root / "checks/candidate.json", p)
            reports["10"]["candidate_fingerprint"] = fingerprint(p)
            self.write(root / "reports/10.json", reports["10"])
            self.assertEqual(check_repository(root)["independent_evaluation"],
                             "evaluation_pending_plan_revision")

    def test_old_candidate_cannot_be_released(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); state, _, _ = self.fixture(root)
            state["outputs"]["candidate"]["release_status"] = "final"
            self.write(root / "STATE.json", state)
            with self.assertRaisesRegex(ValueError, "must not be released"): check_repository(root)

    def test_changed_historical_candidate_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); _, p, _ = self.fixture(root)
            p["candidate"]["version"] = 9; self.write(root / "checks/candidate.json", p)
            with self.assertRaisesRegex(ValueError, "historical candidate identity"): check_repository(root)

    def test_changed_historical_values_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); _, p, _ = self.fixture(root)
            p["metrics"][0]["source_ref"] = "S01:changed"
            self.write(root / "checks/candidate.json", p)
            with self.assertRaisesRegex(ValueError, "historical candidate fingerprint"): check_repository(root)


if __name__ == "__main__":
    unittest.main()
