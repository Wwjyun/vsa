import os

import pandas as pd


def flip_csv_files(input_folder):
    for file_name in os.listdir(input_folder):
        if file_name.startswith("convert_") and file_name.endswith(".csv"):
            file_path = os.path.join(input_folder, file_name)
            df = pd.read_csv(file_path)
            df["Col"] = df["Col"].max() - df["Col"]
            df.to_csv(file_path, index=False)
            print(f"Flipped {file_name} horizontally.")
