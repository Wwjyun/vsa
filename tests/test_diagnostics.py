from vsa import __version__
from vsa.diagnostics import diagnostic_summary


def test_diagnostics_contains_versions_but_not_data_root(monkeypatch):
    monkeypatch.setenv("VSA_DATA_ROOT", r"D:\sensitive\production")
    summary = diagnostic_summary()

    assert f"VSA: {__version__}" in summary
    assert "Python:" in summary
    assert "sensitive" not in summary
