import copy
import unittest
from verify_handoff import check_package, check_evaluation, fingerprint, impacted_metrics

H = "a" * 64


def package():
    common = {"status": "valid", "population": "first-insured", "unit": "ratio",
              "period": "2025-01", "source_ref": "S01:test", "evidence_sha256": H}
    rows = [dict(common, id="city", kind="ratio", value=5125/32297, numerator=5125, denominator=32297),
            dict(common, id="reference", kind="ratio", value=0.2, numerator=1, denominator=5),
            dict(common, id="difference", kind="difference_pp", unit="pp",
                 value=100*(5125/32297-0.2), depends_on=["city", "reference"]),
            dict(common, id="total", kind="count", unit="cases", value=1787,
                 parts=[66,255,198,432,259,190,230,157])]
    return {"schema": "care_candidate/v1", "plan_revision": "2.2",
            "candidate": {"id": "test-only", "version": 1, "sha256": H},
            "input_hashes": {"S01": H}, "definitions_sha256": H, "template_sha256": H,
            "code_commit": "b"*40, "required_metrics": [r["id"] for r in rows], "metrics": rows}


class HandoffTests(unittest.TestCase):
    def test_valid_values(self):
        self.assertEqual(check_package(package())["valid_metrics"], 4)

    def test_fractional_count(self):
        p=package(); p["metrics"][3]["value"]=1787.1
        with self.assertRaisesRegex(ValueError, "integer"): check_package(p)

    def test_original_total_error(self):
        p=package(); p["metrics"][3]["value"]=66
        with self.assertRaisesRegex(ValueError, "total mismatch"): check_package(p)

    def test_zero_denominator(self):
        p=package(); p["metrics"][0]["denominator"]=0
        with self.assertRaisesRegex(ValueError, "denominator"): check_package(p)

    def test_wrong_population_ratio(self):
        p=package(); p["metrics"][0]["value"]=5125/1787
        with self.assertRaisesRegex(ValueError, "recalculation"): check_package(p)

    def test_duplicate_id(self):
        p=package(); p["metrics"][1]["id"]="city"
        with self.assertRaisesRegex(ValueError, "duplicate"): check_package(p)

    def test_missing_required(self):
        p=package(); p["metrics"].pop()
        with self.assertRaisesRegex(ValueError, "required metric missing"): check_package(p)

    def test_cycle(self):
        p=package(); p["metrics"][0]["depends_on"]=["difference"]
        with self.assertRaisesRegex(ValueError, "cycle"): check_package(p)

    def test_nan(self):
        p=package(); p["metrics"][0]["value"]=float("nan")
        with self.assertRaisesRegex(ValueError, "finite"): check_package(p)

    def test_held_propagates(self):
        p=package(); p["metrics"][0].update(status="held", reason="unverified input")
        with self.assertRaisesRegex(ValueError, "held/absent"): check_package(p)
        p["metrics"][2].update(status="held", reason="held parent")
        self.assertEqual(check_package(p)["held_or_absent"], 2)

    def test_missing_is_not_zero(self):
        p=package(); p["metrics"][3].update(status="missing", reason="not provided", value=0)
        with self.assertRaisesRegex(ValueError, "numeric zero"): check_package(p)

    def test_stale_evaluation(self):
        p=package(); report={"role":"20", "status":"completed", "candidate":p["candidate"],
                             "candidate_fingerprint":fingerprint(p), "verdict":"PASS"}
        self.assertEqual(check_evaluation(report,p),"PASS")
        p["candidate"]["version"]=2
        with self.assertRaisesRegex(ValueError, "stale"): check_evaluation(report,p)

    def test_transitive_change_scope(self):
        old=package(); new=copy.deepcopy(old); new["metrics"][0]["source_ref"]="S01:new-cell"
        self.assertEqual(impacted_metrics(old,new), {"city","difference"})

    def test_global_change_invalidates_all(self):
        old=package(); new=copy.deepcopy(old); new["input_hashes"]["S01"]="c"*64
        self.assertEqual(impacted_metrics(old,new), set(old["required_metrics"]))

    def test_wrong_input_hash(self):
        with self.assertRaisesRegex(ValueError, "input hash mismatch"):
            check_package(package(), expected_inputs={"S01":"c"*64})


if __name__ == "__main__":
    unittest.main()
