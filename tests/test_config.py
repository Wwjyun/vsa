import pytest

from vsa.config import ConfigurationError, load_classification_rules, load_product_stages


def test_packaged_resources_load_independently_of_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    products = load_product_stages()
    rules = load_classification_rules()

    assert products["Product A"][:4] == ("STAGE1", "LOSS1", "STAGE2", "LOSS2")
    assert "ok" in rules["good"]


def test_product_resource_schema_error_is_explicit(monkeypatch):
    monkeypatch.setattr("vsa.config._load_resource_json", lambda _name: {"Demo": "STAGE1"})
    with pytest.raises(ConfigurationError, match="at least one stage"):
        load_product_stages()
