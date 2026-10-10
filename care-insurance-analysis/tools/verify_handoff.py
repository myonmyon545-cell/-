"""One-off handoff checks. Does not open raw data or approve an Excel release."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

SHA256 = re.compile(r"^[0-9a-f]{64}$")
SHA1 = re.compile(r"^[0-9a-f]{40}$")
STATES = {"valid", "held", "missing", "not_applicable", "provided_substitute"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value):
    require(type(value) in (int, float) and math.isfinite(value), "finite number required")
    return value


def fingerprint(package):
    content = json.dumps(package, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def candidate_identity(candidate):
    require(isinstance(candidate, dict), "candidate identity required")
    require(bool(candidate.get("id")) and candidate.get("version") is not None,
            "candidate id/version required")
    require(bool(SHA256.fullmatch(candidate.get("sha256", ""))), "candidate sha256 required")


def metrics_by_id(package):
    rows = package.get("metrics", [])
    require(isinstance(rows, list) and rows, "nonempty metrics required")
    result = {}
    for row in rows:
        key = row.get("id")
        require(isinstance(key, str) and key and key not in result, "duplicate/missing metric id")
        result[key] = row
    return result


def dependency_order(rows):
    done, active, order = set(), set(), []

    def visit(key):
        require(key in rows, "unknown dependency: " + key)
        require(key not in active, "dependency cycle: " + key)
        if key in done:
            return
        active.add(key)
        for parent in rows[key].get("depends_on", []):
            visit(parent)
        active.remove(key)
        done.add(key)
        order.append(key)

    for key in rows:
        visit(key)
    return order


def check_package(package, expected_revision=None, expected_inputs=None, workbook=None):
    require(package.get("schema") == "care_candidate/v1", "candidate schema mismatch")
    if expected_revision is not None:
        require(package.get("plan_revision") == expected_revision, "plan revision mismatch")
    candidate_identity(package.get("candidate"))
    hashes = package.get("input_hashes", {})
    require(isinstance(hashes, dict) and hashes, "input hashes required")
    for key, value in hashes.items():
        require(bool(SHA256.fullmatch(value)), "invalid input hash: " + key)
        if expected_inputs is not None:
            require(key in expected_inputs and expected_inputs[key] == value, "input hash mismatch: " + key)
    require("S01" in hashes, "main input S01 required")
    for field in ("definitions_sha256", "template_sha256"):
        require(bool(SHA256.fullmatch(package.get(field, ""))), field + " required")
    require(bool(SHA1.fullmatch(package.get("code_commit", ""))), "fixed code commit required")
    rows = metrics_by_id(package)
    required = package.get("required_metrics", [])
    require(isinstance(required, list) and required and len(required) == len(set(required)), "required metric inventory required")
    require(set(required).issubset(rows), "required metric missing")
    valid, held = 0, 0
    for key in dependency_order(rows):
        row = rows[key]
        status = row.get("status")
        require(status in STATES, key + ": unknown status")
        for field in ("population", "unit", "period", "source_ref"):
            require(bool(row.get(field)), key + ": metadata missing: " + field)
        require(bool(SHA256.fullmatch(row.get("evidence_sha256", ""))), key + ": evidence hash missing")
        if status != "valid":
            require(bool(row.get("reason")), key + ": missing hold/absence reason")
            if status in {"missing", "not_applicable"}:
                require(row.get("value") is None, key + ": absence must not be numeric zero")
            held += 1
            continue
        require(all(rows[p].get("status") == "valid" for p in row.get("depends_on", [])), key + ": depends on a held/absent metric")
        value = number(row.get("value"))
        kind = row.get("kind")
        if kind == "count":
            require(value >= 0 and value == int(value), key + ": count is not a nonnegative integer")
            if "parts" in row:
                parts = row["parts"]
                require(isinstance(parts, list) and parts, key + ": empty count parts")
                require(all(number(p) >= 0 and p == int(p) for p in parts), key + ": invalid count part")
                require(sum(parts) == value, key + ": total mismatch")
        elif kind in {"ratio", "mean"}:
            numerator, denominator = number(row.get("numerator")), number(row.get("denominator"))
            require(denominator > 0, key + ": zero/negative denominator")
            if kind == "ratio":
                require(0 <= numerator <= denominator, key + ": ratio numerator out of range")
            require(abs(value - numerator / denominator) <= 1e-10, key + ": recalculation mismatch")
        elif kind == "difference_pp":
            parents = row.get("depends_on", [])
            require(len(parents) == 2, key + ": difference needs two ordered parents")
            require(all(rows[p].get("kind") == "ratio" for p in parents), key + ": difference needs ratio inputs")
            expected = 100 * (rows[parents[0]]["value"] - rows[parents[1]]["value"])
            require(abs(value - expected) <= 1e-8, key + ": pp mismatch")
        elif kind == "provided":
            require(bool(row.get("verification_scope")), key + ": provided value needs scope")
        else:
            raise ValueError(key + ": unknown computation kind")
        valid += 1
    if workbook is not None:
        require(hashlib.sha256(Path(workbook).read_bytes()).hexdigest() == package["candidate"]["sha256"], "workbook hash mismatch")
    return {"valid_metrics": valid, "held_or_absent": held,
            "candidate_fingerprint": fingerprint(package), "scope": "mechanical checks; independent source/layout review still required"}


def impacted_metrics(old, new):
    """Return the transitive change scope; global changes invalidate all reuse."""
    before, after = metrics_by_id(old), metrics_by_id(new)
    global_keys = ("input_hashes", "definitions_sha256", "template_sha256", "code_commit", "plan_revision", "required_metrics")
    if any(old.get(k) != new.get(k) for k in global_keys):
        return set(after)
    changed = {k for k in after if k not in before or after[k] != before[k]}
    # A changed parent invalidates downstream values, comparisons and explanations.
    for key in dependency_order(after):
        if set(after[key].get("depends_on", [])) & changed:
            changed.add(key)
    return changed


def check_evaluation(report, package):
    require(report.get("role") == "20", "independent evaluator role required")
    if report.get("status") != "completed":
        return "evaluation_pending"
    require(report.get("candidate_fingerprint") == fingerprint(package), "stale evaluation fingerprint")
    require(report.get("candidate") == package["candidate"], "evaluation candidate identity mismatch")
    require(report.get("verdict") in {"PASS", "FAIL", "HELD"}, "evaluation verdict required")
    return report["verdict"]


def check_repository(root):
    root = Path(root)
    state = json.loads((root / "STATE.json").read_text(encoding="utf-8"))
    plan = (root / "PLAN.md").read_text(encoding="utf-8")
    revision = state["plan_revision"]
    require("revision: '" + revision + "'" in plan, "PLAN/STATE revision mismatch")
    require(state["writer"] == "00", "STATE writer must be 00")
    reports = {}
    change = state.get("plan_change", {})
    previous = change.get("previous_revision")
    transition = change.get("current_revision") == revision and previous != revision
    retained = change.get("retained_historical_report_blobs", {})
    for role in ("10", "20", "30"):
        report_bytes = (root / "reports" / (role + ".json")).read_bytes()
        report = json.loads(report_bytes)
        require(report.get("schema") == "care_handoff/v1" and report.get("role") == role, "report role/schema mismatch")
        if report.get("plan_revision") != revision:
            require(transition and report.get("plan_revision") == previous,
                    "report plan revision mismatch")
            blob = hashlib.sha1(b"blob " + str(len(report_bytes)).encode("ascii")
                                + b"\0" + report_bytes).hexdigest()
            require(retained.get(role) == blob,
                    "historical report changed without current revision: " + role)
        reports[role] = report
    path = root / "checks" / "candidate.json"
    if not path.exists():
        if transition and change.get("retained_candidate"):
            return {"handoff": "METADATA_ONLY", "analysis": "REVISED_PLAN_AWAITING_NEW_CANDIDATE",
                    "scope": "candidate package unavailable here; no numerical or release approval"}
        require(not any(reports[r].get("status") == "completed" and reports[r].get("task_id") in {"T06", "T07", "T08"} for r in reports), "candidate missing despite completed output/evaluation")
        return {"handoff": "PASS", "analysis": "NOT_STARTED_OR_NO_CANDIDATE", "scope": "metadata only; not analysis approval"}
    package = json.loads(path.read_text(encoding="utf-8"))
    expected = {k: v["sha256"] for k, v in state["inputs"].items() if "sha256" in v}
    if package.get("plan_revision") != revision:
        require(transition and package.get("plan_revision") == previous,
                "candidate plan revision mismatch")
        saved = change.get("retained_candidate", {})
        require(package.get("candidate") == {k: saved[k] for k in ("id", "version", "sha256")},
                "historical candidate identity mismatch")
        historical = check_package(package, previous, expected)
        require(historical["candidate_fingerprint"] == saved.get("candidate_fingerprint"),
                "historical candidate fingerprint mismatch")
        require(reports["10"].get("candidate_fingerprint") == historical["candidate_fingerprint"],
                "historical work report fingerprint mismatch")
        require(reports["10"].get("candidate") == package["candidate"],
                "historical work report candidate mismatch")
        require(str(state.get("outputs", {}).get("candidate", {}).get("release_status", "")).startswith("not_released"),
                "historical candidate must not be released")
        verdict = check_evaluation(reports["20"], package)
        return {"handoff": "PASS", "analysis": "REVISED_PLAN_AWAITING_NEW_CANDIDATE",
                "retained_plan_revision": previous, "retained_evaluation": verdict,
                "current_plan_revision": revision,
                "scope": "historical package checked; new plan implementation/evaluation not performed"}
    if "S10" in expected:
        require(package.get("input_hashes", {}).get("S10") == expected["S10"],
                "current candidate must include fixed S10 input hash")
    result = check_package(package, revision, expected)
    require(reports["10"].get("plan_revision") == revision,
            "current candidate needs current work report")
    require(reports["10"].get("candidate_fingerprint") == result["candidate_fingerprint"], "work report candidate fingerprint mismatch")
    require(reports["10"].get("candidate") == package["candidate"], "work report candidate identity mismatch")
    if reports["20"].get("plan_revision") != revision:
        result["independent_evaluation"] = "evaluation_pending_plan_revision"
    else:
        result["independent_evaluation"] = check_evaluation(reports["20"], package)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        print(json.dumps(check_repository(args.root), ensure_ascii=False))
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(json.dumps({"verdict": "FAIL", "reason": str(error)}, ensure_ascii=False))
        raise SystemExit(1)


if __name__ == "__main__":
    main()

