import os

import pandas as pd


def calculate_change(folder1, folder2):
    changes = {}
    for file_name in os.listdir(folder1):
        if file_name.startswith("convert_") and file_name.endswith(".csv"):
            file_name_original = file_name[len("convert_") :]
            file1_path = os.path.join(folder1, file_name)
            file2_path = os.path.join(folder2, f"convert_{file_name_original}")

            if os.path.exists(file2_path):
                df1 = pd.read_csv(file1_path)
                df2 = pd.read_csv(file2_path)

                merged_df = pd.merge(df1, df2, on=["Row", "Col"], suffixes=("_1", "_2"))

                # 只计算“好的变成坏的”情况
                merged_df["Change"] = (merged_df["ConvertedDefectType_1"] == 1) & (
                    merged_df["ConvertedDefectType_2"] == 0
                )

                total = len(merged_df)
                changed = merged_df["Change"].sum()

                changes[file_name_original] = changed / total if total > 0 else 0

    return changes


def save_changes_to_txt(changes, save_path):
    with open(save_path, "w") as f:
        for file, change in changes.items():
            f.write(f"{file}: {change:.2%}\n")
    print(f"Change ratios saved to {save_path}")
