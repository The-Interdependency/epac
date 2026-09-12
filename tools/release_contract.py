"""Source-derived EPAC package metadata, license gate, and release manifest.

Used by the release builder and pre-execution replay gate. Python 3.10 uses the
hash-pinned parser in requirements-replay.txt; newer Python uses stdlib tomllib.
"""
# === MODULE_BUILD ===
# id: epac_source_release_contract
#   module_name: release_contract
#   module_kind: instrument
#   summary: derives exact package metadata and release dispositions from candidate source
#   owner: The Interdependency
#   public_surface: internal build and replay helper
#   internal_surface: validate_core_metadata, release_license, expected_release_manifest
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: tests/test_distribution_replay.py
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: epac_release_metadata_matches_source
#   given: exact Git source and its artifact hashes
#   then: source metadata and every release manifest field must match, and unresolved license status blocks release qualification
#   class: provenance
# === END CONTRACTS ===
from email.parser import BytesParser
import fnmatch
import hashlib

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
    if tomllib.__version__ != "2.4.1":
        raise RuntimeError("install the hash-pinned requirements-replay.txt parser")


def require(value, message):
    if not value:
        raise ValueError(message)


def project_from_source(source):
    return tomllib.loads(source["pyproject.toml"].decode())


def validate_core_metadata(source, archived, payload, info):
    project = project_from_source(source)
    declared = project["project"]
    require(not declared.get("scripts") and not declared.get("gui-scripts")
            and not declared.get("entry-points"), "entry points require an updated package contract")
    patterns = declared.get("license-files", ("LICEN[CS]E*", "COPYING*", "NOTICE*", "AUTHORS*"))
    license_names = {name for name in source if any(fnmatch.fnmatchcase(name, pattern) for pattern in patterns)}
    metadata = BytesParser().parsebytes(payload[info + "METADATA"])
    expected = {
        "Metadata-Version": ["2.4"], "Name": [declared["name"]], "Version": [declared["version"]],
        "Summary": [declared["description"]], "Author": [", ".join(a["name"] for a in declared["authors"])],
        "Requires-Python": [declared["requires-python"]], "Description-Content-Type": ["text/markdown"],
        "License-File": sorted(license_names),
        "Dynamic": ["license-file"] if license_names else [],
        "Requires-Dist": list(declared.get("dependencies", [])),
        "Provides-Extra": list(declared.get("optional-dependencies", {})),
    }
    for extra, requirements in declared.get("optional-dependencies", {}).items():
        expected["Requires-Dist"].extend(value + '; extra == "' + extra + '"' for value in requirements)
    if isinstance(declared.get("license"), str):
        expected["License-Expression"] = [declared["license"]]
    expected = {key: values for key, values in expected.items() if values}
    require(set(metadata.keys()) == set(expected), "unexpected core metadata fields")
    for key, values in expected.items():
        require(sorted(metadata.get_all(key, [])) == sorted(values), "core metadata differs from source: " + key)
    require(payload[info + "METADATA"].split(b"\n\n", 1)[1] == source[declared["readme"]],
            "metadata description differs from source")
    require(payload[info + "METADATA"] == archived["PKG-INFO"] == archived["interdependency_epac.egg-info/PKG-INFO"],
            "source and wheel core metadata differ")
    return project, license_names


def release_license(source):
    require(source.get("LICENSE", b"").strip(), "owner-selected LICENSE is required before release qualification")
    require("LICENSE_STATUS.md" not in source,
            "remove the unresolved LICENSE_STATUS.md as part of the owner-selected license transition")
    declared = project_from_source(source)["project"]
    require(isinstance(declared.get("license"), str) and declared["license"].strip(),
            "record the owner-selected SPDX license expression in pyproject.toml")
    require(declared.get("license-files") == ["LICENSE"], "release license-files must explicitly select LICENSE")
    return declared["license"]


def expected_release_manifest(source, commit, tree, epoch, artifacts):
    expression = release_license(source)
    versions = {}
    for line in source["requirements-build.txt"].decode().splitlines():
        name, version = line.split("==")
        require(name and version and name not in versions, "invalid pinned build toolchain")
        versions[name] = version
    return {
        "schema": "epac.release-candidate", "version": 1,
        "source_commit": commit, "source_tree": tree, "source_date_epoch": str(epoch),
        "build_toolchain": versions,
        "python_runtime": {"implementation": "cpython", "version": "3.11.15"},
        "compressor": {"implementation": "zlib", "compile_version": "1.3.1", "runtime_version": "1.3.1"},
        "license_expression": expression,
        "license_sha256": hashlib.sha256(source["LICENSE"]).hexdigest(),
        "ucns_source_lock_sha256": hashlib.sha256(source["data/ucns-source-lock.json"]).hexdigest(),
        "artifacts_sha256": dict(artifacts),
        "acceptance": "candidate; clean replay and stack acceptance required",
        "empirical_status_transfer": False,
    }


def reject_duplicate_keys(pairs):
    """Decode every JSON object without silently accepting repeated names."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate release-manifest key: " + key)
        result[key] = value
    return result
