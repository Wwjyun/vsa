import os
import json
import pandas as pd

def load_classification_rules(rules_file):
    with open(rules_file, 'r') as f:
        return json.load(f)

def convert_defect_type(defect_data, good_defects):
    converted_defects = []
    for _, defect in defect_data.iterrows():
        if defect['DefectType'] in good_defects:
            converted_defects.append(1)  # Good defect
        else:
            converted_defects.append(0)  # Bad defect
    return converted_defects

def convert_csv_files(input_folder, rules_file, user_selected_good=None):
    rules = load_classification_rules(rules_file)
    
    for file_name in os.listdir(input_folder):
        if file_name.endswith('.csv'):
            input_file = os.path.join(input_folder, file_name)
            defect_data = pd.read_csv(input_file)

            if 'Col' not in defect_data.columns or 'Row' not in defect_data.columns or 'DefectType' not in defect_data.columns:
                print(f"Skipping {file_name}: Missing required columns.")
                continue
            
            defect_data['ConvertedDefectType'] = convert_defect_type(defect_data, user_selected_good)
            
            if 'No' in defect_data.columns:
                converted_data = defect_data[['No', 'Col', 'Row', 'ConvertedDefectType']]
            else:
                converted_data = defect_data[['Col', 'Row', 'ConvertedDefectType']]
                
            output_file = os.path.join(input_folder, f"convert_{file_name}")
            converted_data.to_csv(output_file, index=False)
            print(f"Converted {file_name} and saved to {output_file}")
