from __future__ import annotations

from data_quant.registry.legacy_catalog import LEGACY_SCRIPT_NAMES, catalog, legacy_script_dir


def test_all_64_public_legacy_scripts_are_cataloged_and_exist() -> None:
    entries = catalog()
    assert len(LEGACY_SCRIPT_NAMES) == 64
    assert len(entries) == 64
    assert len({entry["diagnostic_id"] for entry in entries}) == 64
    directory = legacy_script_dir()
    assert directory is not None
    for entry in entries:
        assert (directory / str(entry["legacy_script"])).is_file()
        assert entry["artifact_type"]
        assert entry["available"] is True
        assert entry["execution_mode"] == "legacy_cli"
