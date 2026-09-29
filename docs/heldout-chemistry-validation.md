# Held-out chemistry validation

Purpose: test EPAC against chemistry facts without feeding those facts into EPAC construction.

## Boundary

The selection boundary is committed before EPAC predictions are produced or revealed:

1. Choose stable case IDs, domains, and comparator rules only; do not include expected values or provenance.
2. Call `freeze_validation_plan(...)` and persist the returned plan commitment.
3. Run EPAC construction and produce predictions only for IDs in that frozen plan.
4. Call `freeze_predictions(..., source_identity=<exact EPAC head/receipt>, validation_plan=<persisted plan>)` and persist the prediction commitment.
5. Only then reveal/load a held-out oracle containing the same case IDs, domains, and comparator rules plus expected values and provenance.
6. Call `compare_after_freeze(commitment, oracle, validation_plan=<persisted plan>)`.
7. Preserve the receipt and its `SURVIVED / FALSIFIED / UNRESOLVED` results.

The flow is:

`frozen validation plan → EPAC derivation → frozen prediction → held-out oracle → comparator → evidence receipt`

The chemistry app is a **discovery/reference surface**, not an EPAC construction dependency and not the sole authority. Facts used for scoring carry an authority plus locator. Missing predictions, absent expected values, missing/null provenance, unsupported comparisons, and non-finite numeric comparisons are `UNRESOLVED`; they are never silently counted as success. Duplicate oracle IDs or drift in the frozen case inventory/domain/comparator contract are rejected before scoring.

The checked-in `data/heldout_chemistry_oracle.json` is intentionally empty as a distributable comparison-side resource and smoke-test default. Its emptiness does **not** prove independent case selection. The anti-selection control is the persisted validation-plan commitment that binds case identity and comparator rules before the prediction commitment exists. Stronger chronology or independent custody can be supplied by an external evidence store without changing EPAC construction.

Recommended stable IDs include `element:H:valence`, `element:O:oxidation`, `isotope:H-1:mass`, and `reaction:<canonical-id>:products`. The corpus can grow across isotope behavior, oxidation/valence, reaction outcomes, and element properties without changing EPAC construction code.

## Comparator and evidence input rules

Validation-plan comparator fields are closed in v1 so expected labels cannot be smuggled into the prediction side:

- `exact` and `set-equality` accept only `kind`;
- `numeric-tolerance` accepts only `kind` and `absolute_tolerance`;
- an unknown comparator kind may be preregistered with `kind` only and will score `UNRESOLVED`;
- any additional comparator field is rejected before the plan is committed or verified.

Numeric-tolerance comparison keeps integers as integers and uses exact rational arithmetic over accepted finite Python numeric values, so large integer distinctions are not collapsed by an intermediate float conversion. Non-finite operands or tolerances remain `UNRESOLVED`.

Provenance `authority` and `locator` must both be nonempty strings after trimming; blank or null identities are `UNRESOLVED`. File-based oracle loading rejects duplicate JSON object keys at any nesting level rather than accepting parser-dependent evidence. In a source checkout, `load_packaged_oracle()` prefers the sibling `data/heldout_chemistry_oracle.json`; in an installed distribution it reads the `epac_data` package resource.

## Runnable end-to-end example

This runs from a source checkout or the installed distribution. It persists and reloads both commitments before revealing a synthetic held-out value, exercises packaged-oracle loading, then persists the evidence receipt.

```bash
python - <<'PY'
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from epac_heldout_validation import (
    compare_after_freeze,
    freeze_predictions,
    freeze_validation_plan,
    load_oracle,
    load_packaged_oracle,
)

with TemporaryDirectory() as tmp:
    root = Path(tmp)

    plan = freeze_validation_plan([
        {
            "id": "example:scalar",
            "domain": "example",
            "comparison": {"kind": "exact"},
        }
    ])
    (root / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
    plan = json.loads((root / "plan.json").read_text(encoding="utf-8"))

    # Replace this literal with an EPAC-derived prediction in a real run.
    predictions = {"example:scalar": 7}
    commitment = freeze_predictions(
        predictions,
        source_identity="epac@example-exact-head-or-receipt",
        validation_plan=plan,
    )
    (root / "prediction.json").write_text(
        json.dumps(commitment), encoding="utf-8"
    )
    commitment = json.loads(
        (root / "prediction.json").read_text(encoding="utf-8")
    )

    # The package ships an empty comparison-side resource; loading it works
    # identically from a checkout or installed wheel.
    packaged = load_packaged_oracle()
    assert packaged["schema"] == "epac.heldout-chemistry-oracle"

    # Reveal/write held-out evidence only after the two commitments above.
    oracle = {
        "schema": "epac.heldout-chemistry-oracle",
        "version": "v1",
        "cases": [{
            "id": "example:scalar",
            "domain": "example",
            "comparison": {"kind": "exact"},
            "expected": 7,
            "provenance": {
                "authority": "example-authority",
                "locator": "example:7",
            },
        }],
    }
    (root / "oracle.json").write_text(json.dumps(oracle), encoding="utf-8")
    oracle = load_oracle(root / "oracle.json")

    receipt = compare_after_freeze(
        commitment,
        oracle,
        validation_plan=plan,
    )
    (root / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
    preserved = json.loads((root / "receipt.json").read_text(encoding="utf-8"))

    assert preserved["counts"] == {
        "SURVIVED": 1,
        "FALSIFIED": 0,
        "UNRESOLVED": 0,
    }
    assert preserved["validation_plan_sha256"] == plan["plan_sha256"]
    assert preserved["prediction_commitment_sha256"] == commitment["commitment_sha256"]
    assert len(preserved["oracle_sha256"]) == 64
    assert len(preserved["receipt_sha256"]) == 64
    print(preserved["counts"])
PY
```

## Failure definition

- **SURVIVED**: frozen prediction satisfies the preregistered comparator.
- **FALSIFIED**: frozen prediction is comparable and disagrees.
- **UNRESOLVED**: the comparison cannot honestly decide.

The receipt binds the frozen validation plan, frozen prediction commitment, revealed oracle digest, and detached result evidence.

## hmmm

The module proves its own ordering and digest relationships; it does not by itself prove that a human or external curator lacked access to predictions before creating the plan. If that stronger claim matters, persist the plan digest in an independently controlled/timestamped evidence system before EPAC derivation.
