import pandas as pd
import os
import pprint
import re # For handling different hyphens

# Define paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
output_dir = os.path.join(project_root, 'src', 'data')
output_py_path = os.path.join(output_dir, 'glide_path_allocations.py')

# --- Configuration ---
# Map filenames to risk level keys in the output dictionary
RISK_LEVEL_FILES = {
    "Low": "Low-Table 1.csv",
    "Below-Avg": "Below‑Avg-Table 1.csv", # Note the different hyphen
    "Moderate": "Moderate-Table 1.csv",
    "Above-Avg": "Above‑Avg-Table 1.csv", # Note the different hyphen
    "High": "High-Table 1.csv",
}

# Define expected columns based on Moderate-Table 1.csv
# Assuming Age Min/Max will be derived from 'Age range'
AGE_RANGE_COL = 'Age range'
AGE_MIN_COL = 'Age Min' # Will be created dynamically
AGE_MAX_COL = 'Age Max' # Will be created dynamically
ALLOCATION_COLS = [
    'Equity %', 'Real Assets %', 'Cash %', 'Bonds %', 'VTI', 'VUG', 'VBR',
    'VEA', 'VSS', 'VWO', 'VNQ', 'VNQI', 'BND', 'BNDX', 'VTIP'
]
# --- End Configuration ---

def parse_csv_files_to_dict(risk_files_map, base_path):
    """Reads multiple CSV files and converts them into a single nested dictionary."""
    all_allocations = {}

    for risk_level, filename in risk_files_map.items():
        file_path = os.path.join(base_path, filename)
        print(f"Processing: {filename} for Risk Level: {risk_level}")

        try:
            # Read CSV, skip first row ("Table 1"), use second row as header
            df = pd.read_csv(file_path, header=0, skiprows=[0])
        except FileNotFoundError:
            print(f"  Error: File not found at {file_path}. Skipping this risk level.")
            continue
        except Exception as e:
            print(f"  Error reading CSV file {file_path}: {e}. Skipping this risk level.")
            continue

        allocations_for_risk = {}
        required_cols = [AGE_RANGE_COL] + ALLOCATION_COLS

        # Check if all required columns exist
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"  Error: Missing required columns in {filename}: {', '.join(missing_cols)}")
            print(f"  Available columns: {', '.join(df.columns)}. Skipping this risk level.")
            continue

        # --- Data Processing Logic ---
        # Process 'Age range'
        if AGE_RANGE_COL in df.columns:
            try:
                # Replace different hyphens with standard hyphen before splitting
                age_str = df[AGE_RANGE_COL].astype(str).str.replace(r'[‑–—]', '-', regex=True)
                age_split = age_str.str.split('-', expand=True)
                df[AGE_MIN_COL] = pd.to_numeric(age_split[0].str.strip(), errors='coerce')
                df[AGE_MAX_COL] = pd.to_numeric(age_split[1].str.strip(), errors='coerce')
                df.dropna(subset=[AGE_MIN_COL, AGE_MAX_COL], inplace=True) # Drop rows where conversion failed
                df[AGE_MIN_COL] = df[AGE_MIN_COL].astype(int)
                df[AGE_MAX_COL] = df[AGE_MAX_COL].astype(int)
            except Exception as e:
                print(f"  Error processing '{AGE_RANGE_COL}' column in {filename}: {e}. Check format. Skipping.")
                continue
        else:
            print(f"  Error: Required column '{AGE_RANGE_COL}' not found in {filename}. Skipping.")
            continue

        # Convert allocation columns to numeric decimals (assuming values > 1 are percentages)
        for col in ALLOCATION_COLS:
             if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                # Check if they are likely percentages (e.g., > 1 or specified with '%')
                is_percentage = '%' in col or (df[col].notna() & (df[col].abs() > 1.0)).any()
                if is_percentage:
                     print(f"  Column '{col}' in {filename} looks like percentage. Converting to decimal.")
                     df[col] = df[col] / 100.0
                df.fillna({col: 0.0}, inplace=True) # Replace NaNs with 0.0

        # Extract data into dictionary for this risk level
        for index, row in df.iterrows():
            age_min = row[AGE_MIN_COL]
            age_max = row[AGE_MAX_COL]
            age_key = (age_min, age_max)

            if age_key not in allocations_for_risk:
                 allocations_for_risk[age_key] = {}
            else:
                 print(f"  Warning: Duplicate entry for Age Range {age_key} in {filename}. Overwriting.")

            allocation_details = {col: float(row[col]) for col in ALLOCATION_COLS}
            allocations_for_risk[age_key] = allocation_details

        all_allocations[risk_level] = allocations_for_risk
        print(f"  Successfully processed {filename}.")

    return all_allocations

def save_dict_to_py(data_dict, output_path):
    """Saves the dictionary to a Python file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# This file was automatically generated by scripts/parse_glide_path.py\n")
            f.write("# It contains allocation data parsed from multiple risk level CSVs.\n")
            f.write("# Do not edit this file manually.\n\n")
            f.write("GLIDE_PATH_ALLOCATIONS = ")
            pprint.pprint(data_dict, stream=f, indent=2, width=120)
            f.write("\n")
        print(f"\nSuccessfully saved combined allocation data to {output_path}")
    except Exception as e:
        print(f"\nError saving dictionary to {output_path}: {e}")

if __name__ == "__main__":
    print(f"Parsing multiple CSV files from directory: {project_root}")
    # Call the updated parsing function
    parsed_data = parse_csv_files_to_dict(RISK_LEVEL_FILES, project_root)

    if parsed_data:
        # Basic validation: Check if all risk levels were processed
        if len(parsed_data) == len(RISK_LEVEL_FILES):
             print("\nAll risk levels processed successfully.")
        else:
             print(f"\nWarning: Processed {len(parsed_data)} out of {len(RISK_LEVEL_FILES)} risk levels. Check errors above.")
        
        save_dict_to_py(parsed_data, output_py_path)
    else:
        print("\nParsing failed. No data was processed. Output file was not created.")
