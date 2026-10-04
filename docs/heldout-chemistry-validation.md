# Held-out chemistry validation

Purpose: test EPAC against chemistry facts without feeding those facts into EPAC construction.

Runtime effects are limited to reading caller-supplied evidence and the packaged oracle and returning in-memory results. The module writes no files or network messages; callers control persistence as shown below. The source declares its runtime boundary, documentation, capabilities, dependency edges, and existing owner.

The operation inventory retains all nine public held-out functions as `AMBIGUOUS`, with a separate mapping reason for each operation. Their relation to the frozen 27-state construction and ability to distinguish same-B states have not been measured. Validation integrity does not establish boundary non-relevance or transfer chemistry standing.

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

Validation-plan fields are deliberately narrow so oracle-shaped data cannot cross into the prediction side:

- `domain` is either `null` or one nonempty canonical string; objects, arrays, numbers, blank strings, and padded strings are rejected;
- `exact` and `set-equality` comparators accept only `kind`;
- `numeric-tolerance` accepts only `kind` and `absolute_tolerance`; a supplied tolerance must be a number or `null`, so nested oracle fields, strings, and booleans cannot cross through that slot;
- an unknown comparator kind may be preregistered with `kind` only and will score `UNRESOLVED`;
- any additional comparator field is rejected before the plan is committed or verified.

Prediction and programmatic oracle values must use the JSON container/type model: `null`, booleans, numbers, strings, arrays/lists, and string-keyed objects/mappings. Python-only coercible values such as tuples are rejected before commitment or evidence hashing, including when nested. This keeps an in-memory commitment semantically identical to the same commitment after documented JSON persistence/reload. Non-finite Python floats remain admissible only so the comparator can classify them `UNRESOLVED`; they never produce a numeric success.

Numeric-tolerance comparison keeps integers as integers and uses exact rational arithmetic over accepted finite JSON decimal values, so large integer distinctions are not collapsed by an intermediate float conversion. Non-finite operands or tolerances remain `UNRESOLVED`.

Provenance `authority` and `locator` must both be nonempty strings after trimming; blank or null identities are `UNRESOLVED`. All evidence loaders reject duplicate JSON object keys at every nesting level, including identical duplicates and escaped spellings of the same key. Reload plans with `load_validation_plan(path)` and commitments with `load_prediction_commitment(path, validation_plan=plan)`: these verify envelopes and digests, and the latter also verifies the plan binding and prediction-ID membership before returning. Missing predictions remain admissible and score `UNRESOLVED`; extra predictions are rejected. `verify_commitment()` alone checks only the envelope, not plan membership. Raw `json.loads` discards duplicate-key evidence and must not be used to reload externally supplied plans or commitments.

In a source checkout, `load_packaged_oracle()` prefers the sibling `data/heldout_chemistry_oracle.json`; in an installed distribution it reads the `epac_data` package resource. Loading a plan or commitment never loads oracle data.

The reserved `hmmm` provenance identity (ignoring surrounding whitespace and case) is unresolved, just like a blank or null identity. It cannot produce a scored success.

The same reserved sentinel is rejected as a prediction `source_identity` during freezing, commitment verification, reloading, and comparison, including envelopes with a recomputed matching digest. Supply a resolved EPAC head or receipt identity before freezing predictions.

Case identifiers and non-null domains must also be resolved identities: the reserved `hmmm` sentinel is rejected in plans, predictions, oracle comparisons, and preserved receipts, including externally reconstructed envelopes with matching digests. An omitted domain remains `null`; it is not replaced by an unknown identity string.

Within prediction or expected evidence, a reserved `hmmm` string (ignoring case and surrounding whitespace) or a non-finite number makes the case `UNRESOLVED` before any comparator runs. This applies recursively to arrays and object keys/values, even when the other operand has a different type, length, or keys. Explicitly unknown evidence cannot establish agreement or disagreement, and the receipt loader enforces the same classification.

Every loader also requires decimal/exponent JSON numbers to preserve their exact decimal value when parsed and serialized back to JSON. Ordinary round-trip values such as `0.1` and `1.007825` remain supported; precision-losing literals such as `9007199254740993.0`, finite-number overflow, and underflow are rejected before hashing or scoring. Integer tokens retain Python's exact integer handling. This is a decimal-value round-trip check, not a claim that decimal fractions have exact binary encodings. Explicit non-finite Python JSON extensions retain the existing `UNRESOLVED` comparison policy.

All numeric comparison uses exact rational interpretations of the committed JSON decimal values, including nested exact/set equality and tolerance arithmetic. For example, `1e23` means exactly `100000000000000000000000`, not the nearby integer represented by its in-memory binary float. Programmatic floats use their canonical JSON decimal representation, so direct and persisted scoring agree.

Strings and object keys must contain valid Unicode scalar values. Loaders and programmatic normalization reject unpaired surrogates with `ValueError` before hashing or returning loaded evidence. Valid non-ASCII text, including JSON-escaped surrogate pairs that decode to a Unicode scalar, retains the same canonical UTF-8 digest.

Reload preserved receipts with `load_validation_receipt(path)`. It rejects duplicate keys, invalid envelopes and digest fields, repeated case IDs, inconsistent result statuses or counts, and a mismatched `receipt_sha256`. It also checks scored statuses against the evidence carried in each result. These checks establish internal integrity; an unkeyed checksum does not authenticate a custodian or prevent replacement of the entire evidence chain. Preserve externally trusted digests or independently controlled custody when that stronger claim matters.

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
    load_prediction_commitment,
    load_validation_receipt,
    load_validation_plan,
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
    plan = load_validation_plan(root / "plan.json")

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
    commitment = load_prediction_commitment(
        root / "prediction.json", validation_plan=plan
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
    preserved = load_validation_receipt(root / "receipt.json")

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
