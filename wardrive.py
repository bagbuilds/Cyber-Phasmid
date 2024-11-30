import os
import shutil
import subprocess
import glob
import pandas as pd
from datetime import datetime
import folium

# Configuration Variables

# Kismet Configuration
KISMET_START_COMMAND = 'kismet'  # Command to start Kismet
KISMET_OPTIONS = '--override wardrive'  # Additional options to pass to Kismet at startup
KISMET_PROCESS_NAME = 'kismet'  # Process name for Kismet
KISMET_WORKING_DIR = '/home/kali/wardrive'  # Directory where Kismet operates and saves files

# Directories
DEFAULT_WIGLECSV_DIR = KISMET_WORKING_DIR  # Default directory where Kismet saves wiglecsv files
ARCHIVE_DIR = '/home/kali/archive/wardrive'  # Directory to archive wiglecsv files

# Output File
OUTPUT_FILE_PATH = '/home/kali/wardrive/dataset.csv'  # Path to save the final dataset

# Data Processing Variables

# Columns for sorting
STRING_COLUMN_NAME = 'AuthMode'  # Name of the column containing string values
STRING_COLUMN_ORDER = ['value1', 'value2']  # Ordered list of possible string values (can be any number)

NUMERIC_COLUMN_NAME = 'RSSI'  # Name of the column containing numeric values

# Duplicate Filtering
DUPLICATE_COLUMN_NAME = 'MAC'  # Name of the column to check for duplicates
DUPLICATE_NUMERIC_COLUMN = 'RSSI'  # Numeric column to determine which duplicate to keep

# Deletion Criteria
DELETE_COLUMN_1 = 'SSID'  # Name of the first column for deletion criteria
DELETE_COLUMN_2 = 'MAC'  # Name of the second column for deletion criteria
PREDEFINED_DELETE_VALUES = ['00:00:00:00:00:00', 'my-access-point', 'AA:AA:AA:AA:AA:AA']  # Default values to delete if no input is given

# Archiving Option
ARCHIVE_BY_FILE_DATE = True  # True to archive based on file creation date, False to use current date

# Map Option
CUSTOM_MAP_SERVER = False # Use a custom map server
CUSTOM_TILES = 'http://localhost:8080/styles/basic/512/{z}/{x}/{y}.png'
CUSTOM_TILES_ATTR = 'tileserver-gl'
CUSTOM_TILES_NAME = 'basic'

# Variables for Map Creation
MAP_STRING_COLUMN = 'SSID'  # Name of the column containing strings for marker names
MAP_LATITUDE_COLUMN = 'CurrentLatitude'  # Name of the column containing latitude values
MAP_LONGITUDE_COLUMN = 'CurrentLongitude'  # Name of the column containing longitude values
MAP_OUTPUT_FILE = '/home/kali/wardrive/map.html'  # Path to save the generated map

def start_kismet():
    """Starts the Kismet process with optional parameters in the specified working directory."""
    command = f"{KISMET_START_COMMAND} {KISMET_OPTIONS}"
    try:
        subprocess.Popen(command.split(), cwd=KISMET_WORKING_DIR)
        print(f"Kismet started in directory: {KISMET_WORKING_DIR}")
    except Exception as e:
        print(f"Failed to start Kismet: {e}")

def stop_kismet():
    """Stops the Kismet process."""
    try:
        subprocess.run(['pkill', '-f', KISMET_PROCESS_NAME])
        print("Kismet stopped.")
    except Exception as e:
        print(f"Failed to stop Kismet: {e}")

def copy_and_delete_wiglecsv(source_dir, destination_dir):
    """
    Copies wiglecsv files from source to destination, organizes them into date-based subdirectories,
    and deletes the originals.
    """
    if not destination_dir:
        print("Archive directory (ARCHIVE_DIR) is not set. Please set ARCHIVE_DIR in the configuration variables.")
        return []

    files_copied = []
    # Get list of wiglecsv files
    wiglecsv_files = glob.glob(os.path.join(source_dir, '*.wiglecsv'))

    if not wiglecsv_files:
        print("No wiglecsv files found to archive.")
        return files_copied

    for file in wiglecsv_files:
        # Determine the date for archiving
        if ARCHIVE_BY_FILE_DATE:
            # Use the file's creation time
            timestamp = os.path.getctime(file)
        else:
            # Use the current time
            timestamp = datetime.now().timestamp()

        # Format the date as YY-MM-DD
        date_folder = datetime.fromtimestamp(timestamp).strftime('%y-%m-%d')

        # Create the destination subdirectory if it doesn't exist
        dest_subdir = os.path.join(destination_dir, date_folder)
        os.makedirs(dest_subdir, exist_ok=True)

        # Copy the file to the destination subdirectory
        shutil.copy(file, dest_subdir)
        # Delete the original file
        os.remove(file)
        files_copied.append(file)

    print(f"Copied and deleted {len(files_copied)} wiglecsv files into date-based subdirectories.")
    return files_copied

def load_wiglecsv_files(option):
    """Loads wiglecsv files based on the user's choice."""
    files_to_load = []

    if option == 'last_session':
        # Get all wiglecsv files from the default directory
        files_to_load = glob.glob(os.path.join(DEFAULT_WIGLECSV_DIR, '*.wiglecsv'))
    elif option == 'archived':
        # Get all wiglecsv files from the archive directory
        if ARCHIVE_DIR:
            files_to_load = glob.glob(os.path.join(ARCHIVE_DIR, '**', '*.wiglecsv'), recursive=True)
        else:
            print("Archive directory (ARCHIVE_DIR) is not set.")
            return None
    elif option == 'all':
        # Get files from both default and archive directories
        files_to_load = glob.glob(os.path.join(DEFAULT_WIGLECSV_DIR, '*.wiglecsv'))
        if ARCHIVE_DIR:
            files_to_load += glob.glob(os.path.join(ARCHIVE_DIR, '**', '*.wiglecsv'), recursive=True)
        else:
            print("Archive directory (ARCHIVE_DIR) is not set. Only loading files from the default directory.")
    else:
        print("Invalid option selected.")
        return None

    if not files_to_load:
        print("No files found to load.")
        return None

    dataset = merge_wiglecsv_files(files_to_load)
    return dataset

def merge_wiglecsv_files(file_list):
    """Merges multiple wiglecsv files into a single DataFrame."""
    data_frames = []
    for file in file_list:
        try:
            df = pd.read_csv(file, header=1)  # Use second line as header
            data_frames.append(df)
        except Exception as e:
            print(f"Failed to read {file}: {e}")
    if data_frames:
        merged_dataset = pd.concat(data_frames, ignore_index=True)
        print(f"Merged {len(data_frames)} files into a single dataset.")
        return merged_dataset
    else:
        print("No data frames to merge.")
        return pd.DataFrame()



def remove_empty_rows(dataset):
    """
    Removes rows where DELETE_COLUMN_1 or DELETE_COLUMN_2 have empty or null values.
    """
    columns_to_check = [DELETE_COLUMN_1, DELETE_COLUMN_2]

    # Check if the specified columns exist in the dataset
    missing_columns = [col for col in columns_to_check if col not in dataset.columns]
    if missing_columns:
        print(f"Columns not found in the dataset: {', '.join(missing_columns)}")
        return dataset

    # Replace empty strings with NaN
    dataset[columns_to_check] = dataset[columns_to_check].replace('', pd.NA)

    # Remove rows with empty or null values in the specified columns
    initial_count = len(dataset)
    dataset = dataset.dropna(subset=columns_to_check)
    final_count = len(dataset)
    removed_count = initial_count - final_count

    print(f"Removed {removed_count} rows with empty values in columns: {', '.join(columns_to_check)}.")
    return dataset

def filter_duplicates(dataset):
    """Removes duplicate entries in a specified column, keeping the one with the highest numeric value."""
    if DUPLICATE_COLUMN_NAME not in dataset.columns or DUPLICATE_NUMERIC_COLUMN not in dataset.columns:
        print("Specified columns for duplicate filtering not found in the dataset.")
        return dataset

    # Convert numeric column to appropriate data type if necessary
    dataset[DUPLICATE_NUMERIC_COLUMN] = pd.to_numeric(dataset[DUPLICATE_NUMERIC_COLUMN], errors='coerce')

    # Drop duplicates, keeping the entry with the highest numeric value
    dataset_filtered = dataset.sort_values(DUPLICATE_NUMERIC_COLUMN, ascending=False)
    dataset_filtered = dataset_filtered.drop_duplicates(subset=DUPLICATE_COLUMN_NAME, keep='first')

    print("Filtered duplicates based on specified columns.")
    return dataset_filtered

def delete_entries(dataset):
    """Deletes entries based on user input or predefined values in specified columns."""
    print("\nDeletion Options:")
    print(f"1. Delete based on column '{DELETE_COLUMN_1}'")
    print(f"2. Delete based on column '{DELETE_COLUMN_2}'")
    choice = input("Select an option (1/2): ")

    if choice == '1':
        column_name = DELETE_COLUMN_1
    elif choice == '2':
        column_name = DELETE_COLUMN_2
    else:
        print("Invalid selection. Skipping deletion.")
        return dataset

    if column_name not in dataset.columns:
        print(f"Column '{column_name}' not found in the dataset.")
        return dataset

    # Get values to delete from user input
    values_to_delete_input = input(f"Enter values to delete from '{column_name}' (comma-separated), or leave empty to use predefined values: ")
    if values_to_delete_input.strip():
        values_to_delete = [value.strip() for value in values_to_delete_input.split(',')]
    else:
        values_to_delete = PREDEFINED_DELETE_VALUES

    # Delete entries
    initial_count = len(dataset)
    dataset = dataset[~dataset[column_name].isin(values_to_delete)]
    final_count = len(dataset)
    deleted_count = initial_count - final_count

    print(f"Deleted {deleted_count} entries based on values in '{column_name}'.")
    return dataset

def sort_dataset(dataset, string_column_order):
    """Sorts the dataset based on specified string and numeric columns."""
    if dataset.empty:
        print("Dataset is empty.")
        return dataset

    # Check if specified columns exist in the dataset
    if STRING_COLUMN_NAME not in dataset.columns or NUMERIC_COLUMN_NAME not in dataset.columns:
        print("Specified columns for sorting not found in the dataset.")
        return dataset

    # Create a categorical type for the string column based on the specified order
    dataset[STRING_COLUMN_NAME] = pd.Categorical(
        dataset[STRING_COLUMN_NAME],
        categories=string_column_order,
        ordered=True
    )

    # Sort the dataset
    dataset_sorted = dataset.sort_values(
        by=[STRING_COLUMN_NAME, NUMERIC_COLUMN_NAME],
        ascending=[True, True]
    )

    print("Dataset sorted based on the provided string column order.")
    return dataset_sorted

def save_and_open_dataset(dataset, file_path):
    """Saves the dataset to disk and opens it with the default application."""
    try:
        dataset.to_csv(file_path, index=False)
        print(f"Dataset saved to {file_path}.")
        if os.name == 'nt':
            os.startfile(file_path)
        else:
            subprocess.run(['xdg-open', file_path])
    except Exception as e:
        print(f"Failed to save or open dataset: {e}")

def create_map():
    """Creates an OpenStreetMap with markers from the dataset using folium."""
    # Load wiglecsv files
    print("\nLoad Options for Map Creation:")
    print("a. Load last session files")
    print("b. Load archived files")
    print("c. Load all files")
    option = input("Select an option (a/b/c): ")
    if option == 'a':
        dataset = load_wiglecsv_files('last_session')
    elif option == 'b':
        dataset = load_wiglecsv_files('archived')
    elif option == 'c':
        dataset = load_wiglecsv_files('all')
    else:
        print("Invalid option.")
        return

    if dataset is not None:
        # Remove rows with empty values in specified columns
        dataset = remove_empty_rows(dataset)

        # Filter duplicates
        dataset = filter_duplicates(dataset)

        # Delete specified entries
        dataset = delete_entries(dataset)

        # Check if required columns for the map exist
        required_columns = [MAP_STRING_COLUMN, MAP_LATITUDE_COLUMN, MAP_LONGITUDE_COLUMN]
        missing_columns = [col for col in required_columns if col not in dataset.columns]
        if missing_columns:
            print(f"The following required columns are missing from the dataset: {', '.join(missing_columns)}")
            return

        # Convert latitude and longitude to numeric types
        dataset[MAP_LATITUDE_COLUMN] = pd.to_numeric(dataset[MAP_LATITUDE_COLUMN], errors='coerce')
        dataset[MAP_LONGITUDE_COLUMN] = pd.to_numeric(dataset[MAP_LONGITUDE_COLUMN], errors='coerce')

        # Drop rows with invalid coordinates
        dataset = dataset.dropna(subset=[MAP_LATITUDE_COLUMN, MAP_LONGITUDE_COLUMN])

        if dataset.empty:
            print("No data available to create the map after processing.")
            return

        # Create a map centered at the mean location
        mean_lat = dataset[MAP_LATITUDE_COLUMN].mean()
        mean_lon = dataset[MAP_LONGITUDE_COLUMN].mean()
        if CUSTOM_MAP_SERVER:
            folium_map = folium.Map(location=[mean_lat, mean_lon], zoom_start=12, tiles=None)
            folium.TileLayer(
                tiles=CUSTOM_TILES,
                attr=CUSTOM_TILES_ATTR,
                name=CUSTOM_TILES_NAME,
                overlay=False,
                control=True,
            ).add_to(folium_map)
            folium.LayerControl().add_to(folium_map)
        else:
            folium_map = folium.Map(location=[mean_lat, mean_lon], zoom_start=12)


        # Add markers to the map
        for idx, row in dataset.iterrows():
            folium.CircleMarker(
                location=[row[MAP_LATITUDE_COLUMN], row[MAP_LONGITUDE_COLUMN]],
                radius=2,
                color='red',
                popup=['SSID:',str(row[MAP_STRING_COLUMN])]
            ).add_to(folium_map)

        # Save the map to an HTML file
        folium_map.save(MAP_OUTPUT_FILE)
        print(f"Map has been created and saved to {MAP_OUTPUT_FILE}.")

        # Open the map in the default web browser
        try:
            if os.name == 'nt':
                os.startfile(MAP_OUTPUT_FILE)
            else:
                subprocess.run(['xdg-open', MAP_OUTPUT_FILE])
        except Exception as e:
            print(f"Could not open the map file automatically: {e}")
    else:
        print("Dataset could not be loaded.")

def main():
    """Main function to interact with the user and execute the desired operations."""
    while True:
        print("\nMenu:")
        print("1. Start Kismet")
        print("2. Stop Kismet")
        print("3. Archive wiglecsv Files")
        print("4. Load and Process wiglecsv Files")
        print("5. Create Map from Dataset")
        print("6. Exit")
        choice = input("Select an option: ")

        if choice == '1':
            start_kismet()
        elif choice == '2':
            stop_kismet()
        elif choice == '3':
            if not ARCHIVE_DIR:
                print("Archive directory (ARCHIVE_DIR) is not set. Please set ARCHIVE_DIR in the configuration variables before archiving files.")
            else:
                copy_and_delete_wiglecsv(DEFAULT_WIGLECSV_DIR, ARCHIVE_DIR)
        elif choice == '4':
            print("\nLoad Options:")
            print("a. Load last session files")
            print("b. Load archived files")
            print("c. Load all files")
            option = input("Select an option (a/b/c): ")
            if option == 'a':
                dataset = load_wiglecsv_files('last_session')
            elif option == 'b':
                dataset = load_wiglecsv_files('archived')
            elif option == 'c':
                dataset = load_wiglecsv_files('all')
            else:
                print("Invalid option.")
                continue

            if dataset is not None:
                # Remove rows with empty values in specified columns
                dataset = remove_empty_rows(dataset)

                # Filter duplicates
                dataset = filter_duplicates(dataset)

                # Delete specified entries
                dataset = delete_entries(dataset)

                # Prompt to choose the sorting option
                print("\nSorting Options:")
                print("1. Use predefined string column order")
                print("2. Automatically generate string column order (alphabetical)")
                sorting_choice = input("Select an option (1/2): ")

                if sorting_choice == '1':
                    if not STRING_COLUMN_ORDER:
                        print("Predefined string column order is empty. Generating automatically.")
                        string_column_order = sorted(dataset[STRING_COLUMN_NAME].unique())
                    else:
                        string_column_order = STRING_COLUMN_ORDER
                elif sorting_choice == '2':
                    # Automatically generate the list of unique strings and sort alphabetically
                    string_column_order = sorted(dataset[STRING_COLUMN_NAME].unique())
                else:
                    print("Invalid selection. Defaulting to predefined order.")
                    if not STRING_COLUMN_ORDER:
                        print("Predefined string column order is empty. Generating automatically.")
                        string_column_order = sorted(dataset[STRING_COLUMN_NAME].unique())
                    else:
                        string_column_order = STRING_COLUMN_ORDER

                # Sort the dataset with the chosen order
                dataset_sorted = sort_dataset(dataset, string_column_order)

                # Save and open the dataset
                save_and_open_dataset(dataset_sorted, OUTPUT_FILE_PATH)
        elif choice == '5':
            create_map()
        elif choice == '6':
            print("Exiting the program.")
            break
        else:
            print("Invalid selection. Please try again.")

if __name__ == '__main__':
    main()
