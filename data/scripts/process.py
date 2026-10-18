"""Prepare the processed CSV. Run process-data from the project root."""

import argparse

import pandas as pd
from pathlib import Path

def load_combined_data(data_path=None):
    """
    Load the combined raw data from a CSV file.

    Returns:
        pd.DataFrame: A DataFrame containing the combined raw data.
    """
    if data_path is None:
        data_path = Path("data/raw/combined_raw_data.csv")
    return pd.read_csv(data_path)

def _filter_locations(df, locations):
    """
    Filter the DataFrame to include only rows with specified locations.

    Args:
        df (pd.DataFrame): The input DataFrame.
        locations (list): A list of location names to filter by.

    Returns:
        pd.DataFrame: A filtered DataFrame containing only the specified locations.
    """
    return df[df['area_name_en'].isin(locations)]

def _filter_years(df, years):
    """
    Filter the DataFrame to include only rows with specified years.

    Args:
        df (pd.DataFrame): The input DataFrame.
        years (list): A list of years to filter by.

    Returns:
        pd.DataFrame: A filtered DataFrame containing only the specified years.
    """
    df['instance_date'] = pd.to_datetime(df['instance_date'], errors="coerce")
    return df[df['instance_date'].dt.year.isin(years)]

def _selected_columns(df, columns):
    """
    Select specific columns from the DataFrame.

    Args:
        df (pd.DataFrame): The input DataFrame.
        columns (list): A list of column names to select.

    Returns:
        pd.DataFrame: A DataFrame containing only the selected columns.
    """
    return df[columns]

def _rename_column(df, old_name, new_name):
    """
    Rename a column in the DataFrame.

    Args:
        df (pd.DataFrame): The input DataFrame.
        old_name (str): The current name of the column to rename.
        new_name (str): The new name for the column.

    Returns:
        pd.DataFrame: A DataFrame with the specified column renamed.
    """
    return df.rename(columns={old_name: new_name})

def process_data(df, locations, years, columns):
    """
    Process the DataFrame by filtering locations, years, and selecting specific columns.

    Args:
        df (pd.DataFrame): The input DataFrame.
        locations (list): A list of location names to filter by.
        years (list): A list of years to filter by.
        columns (dict): A dictionary mapping old column names to new column names.

    Returns:
        pd.DataFrame: A processed DataFrame after applying all filters and selections.
    """
    df_filtered_locations = _filter_locations(df, locations)
    df_filtered_years = _filter_years(df_filtered_locations, years)
    df_selected_columns = _selected_columns(df_filtered_years, columns.keys())
    for old_name, new_name in columns.items():
        df_selected_columns = _rename_column(df_selected_columns, old_name, new_name)
    return df_selected_columns

def save_processed_data(df, data_path=None, filename="processed_data.csv"):
    """
    Save the processed DataFrame to a CSV file.

    Args:
        df (pd.DataFrame): The DataFrame to save.
        data_path (Path): The path to the output CSV file.
        filename (str): The name of the output CSV file. Defaults to "processed_data.csv".
    """
    if data_path is None:
        data_path = Path("data/processed") / filename
    if not data_path.parent.exists():
        data_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(data_path, index=False)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/raw/combined_raw_data.csv"),
        help="Raw CSV path (default: data/raw/combined_raw_data.csv)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/processed_data.csv"),
        help="Processed CSV path (default: data/processed/processed_data.csv)",
    )
    args = parser.parse_args()

    # Load the combined raw data
    df = load_combined_data(data_path=args.input)

    # Define the locations, years, and columns to filter/select
    locations = ['Marsa Dubai',
                 'Business Bay',
                 'Al Barsha South Fourth',
                 'Al Thanayah Fifth',
                 'Burj Khalifa',
                 'Jabal Ali First']
    years = [2023, 2024, 2025, 2026]
    columns = {'actual_worth':'value',
                'area_name_en':'area_name',
                'building_name_en':'building_name',
                'has_parking':'has_parking',
                'instance_date':'transaction_date',
                'nearest_landmark_en':'nearest_landmark',
                'nearest_mall_en':'nearest_mall',
                'nearest_metro_en':'nearest_metro',
                'trans_group_en':'transaction_group',
                'property_sub_type_en':'property_sub_type',
                'property_type_en':'property_type',
                'rooms_en':'rooms',
                'procedure_area':'area',
                'reg_type_en':'registration_type',
                'transaction_id':'transaction_id',
                'master_project_en':'master_project'
    } 

    # Process the data
    processed_df = process_data(df, locations, years, columns)
    save_processed_data(processed_df, data_path=args.output)
    # Display the length of the processed DataFrame
    print(f"Length of processed DataFrame: {len(processed_df)}")


if __name__ == "__main__":  
    main()
