import json

import pandas as pd

from convert import convert_csv_files


def test_convert_uses_rules_file_when_no_manual_selection_is_given(tmp_path):
    source = tmp_path / "sample.csv"
    pd.DataFrame(
        {
            "No": [1, 2],
            "Col": [0, 1],
            "Row": [0, 0],
            "DefectType": ["ok", "scratch"],
        }
    ).to_csv(source, index=False)
    rules = tmp_path / "rules.json"
    rules.write_text(json.dumps({"good": ["ok"]}), encoding="utf-8")

    convert_csv_files(tmp_path, rules)

    converted = pd.read_csv(tmp_path / "convert_sample.csv")
    assert converted["ConvertedDefectType"].tolist() == [1, 0]
