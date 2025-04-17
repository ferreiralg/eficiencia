import pandas as pd
import glob
import os

# Get the current directory
current_directory = os.getcwd()

# Find all CSV files in the current directory
csv_files = glob.glob(os.path.join(current_directory, '*.csv'))

# Exclude the script itself if it happens to be a CSV (unlikely but safe)
script_name = os.path.basename(__file__)
if script_name in csv_files:
    csv_files.remove(script_name)

if not csv_files:
    print("No CSV files found in the current directory.")
else:
    print(f"Found {len(csv_files)} CSV files to process:")
    for f in csv_files:
        print(f"- {os.path.basename(f)}")

    # List to hold DataFrames
    all_dataframes = []

    # Read each CSV file
    for file in csv_files:
        try:
            # Read CNES as string to preserve leading zeros and allow padding
            df = pd.read_csv(file, delimiter=',', decimal='.', dtype={'CNES': str})
            all_dataframes.append(df)
            print(f"Successfully read {os.path.basename(file)}")
        except Exception as e:
            print(f"Error reading {os.path.basename(file)}: {e}")

    # Concatenate all DataFrames if any were successfully read
    if all_dataframes:
        combined_df = pd.concat(all_dataframes, ignore_index=True)

        # Pad CNES with leading zeros to 7 digits
        if 'CNES' in combined_df.columns:
            combined_df['CNES'] = combined_df['CNES'].astype(str).str.zfill(7)
        else:
            print("Warning: 'CNES' column not found. Skipping padding.")

        # Drop the 'Erro' column if it exists
        if 'Erro' in combined_df.columns:
            combined_df = combined_df.drop(columns=['Erro'])
            print("Dropped 'Erro' column.")
        else:
            print("Warning: 'Erro' column not found. Skipping drop.")

        # Define the output Excel file name
        output_filename = 'resultado_eficiencia.xlsx'
        output_path = os.path.join(current_directory, output_filename)

        # Save the combined DataFrame to an Excel file
        try:
            # index=False prevents writing the DataFrame index as a column
            combined_df.to_excel(output_path, index=False, engine='openpyxl')
            print(f"\nSuccessfully combined CSV files into {output_filename}")
        except Exception as e:
            print(f"\nError writing to Excel file {output_filename}: {e}")
    else:
        print("\nNo dataframes were created. Cannot generate Excel file.") 