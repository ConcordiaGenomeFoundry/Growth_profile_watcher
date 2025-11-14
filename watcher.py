import time
import os
import sys
import csv
import momentum_xml
import lynx_csv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# File extensions to process. Set to None or empty list to process all files.
FILE_EXTENSIONS = ['.csv']


def extract_csv_plate_info_growth(csv_path):
    """
    Extract plate information and growth data from a CSV file.
    :param csv_path: Path to the CSV file.
    """

    with open(csv_path, mode='r') as file:
        reader = csv.reader(file)
        rows = list(reader)

        # Extract plate type (line 5, column 2)
        plate_type = rows[3][1]  # Line 5 is index 4 (0-based indexing)

        # Extract number of columns in the plate (line 6, column 2)
        num_columns = int(rows[4][1])  # Line 6 is index 5 (0-based indexing)

        # Extract number of rows in the plate (line 7, column 2)
        num_rows = int(rows[5][1])  # Line 7 is index 6

        # Extract plate id (line 10, column 2)
        plate_id = rows[8][1]  # Line 10 is index 9

        # Create a list to hold plate information
        plate_info = []
        plate_info.append({"plate_type": plate_type, "num_columns": num_columns, "num_rows": num_rows, "plate_id": plate_id})

        # Extract plate growth data starting from line 35
        plate_data = []
        for row in rows[35:]:  # Line 35 is index 34
            if not row or len(row) < num_rows * num_columns + 1:
                continue
            time = row[0]  # First column is time
            wells = row[1:num_rows*num_columns+1]  # Remaining columns are plate wells (excluding the last column)
            plate_data.append({"time": time, "wells_growth": wells})

        # Print extracted information
        # print(f"Number of Columns: {num_columns}")
        # print(f"Number of Rows: {num_rows}")
        # print(f"Plate Type: {plate_type}")
        # print(f"Plate ID: {plate_id}")
        # print(f"Plate Data: {plate_data[-1]}")

        return plate_info, plate_data


def verify_growth_last_row(plate_info, plate_data, threshold):
    """
    Verify if a percentage of wells (threshold) growth data is higher than saturation_OD and return the time
    when it happened.
    :param plate_info: Dictionary containing plate information such as plate_id, plate_type, num_rows, and num_columns.
    :param plate_data: List of dictionaries containing time and wells growth data.
    :param threshold: Percentage threshold (e.g., 0.7 for 70%).
    :return: Time when the threshold is met, or None if not met.
    """
    # Extract plate information
    num_columns = plate_info[0]['num_columns']
    num_rows = plate_info[0]['num_rows']
    plate_id = plate_info[0]['plate_id']
    plate_type = plate_info[0]['plate_type']
    saturation_OD = 3  # Define saturation OD value

    # Check the last entry in plate_data
    entry = plate_data[-1]  # Access the last entry
    wells_growth = entry['wells_growth']
    count_well_OD_above_saturation = sum(1 for value in wells_growth if float(value) >= saturation_OD)
    print(f"Count of wells with growth > {saturation_OD} at time {entry['time']}: {count_well_OD_above_saturation}")

    if count_well_OD_above_saturation >= (num_rows*num_columns)*threshold:
        print(
            f"Time: {entry['time']}, Total of well OD above {saturation_OD}: {count_well_OD_above_saturation}, Threshold: {threshold*100} at {plate_id} ({plate_type})")
        return entry['time']

    print(f"No time found where at least {threshold*100} of wells growth data is higher than {saturation_OD}.")
    return None


# --- File Processing Logic ---
def process_csv_file(file_path, process_name, threshold):
    """
    Process the newly modified file.
    :param file_path: Path to the modified file.
    """
    print(f"\n--- Processing new file: {file_path} ---")
    try:
        # Process the CSV file
        plate_info, plate_data = extract_csv_plate_info_growth(file_path)

        # Verify wells growth
        time_of_growth = verify_growth_last_row(plate_info, plate_data, threshold)

        print(f"Successfully processed: {file_path}")

        if time_of_growth: # If a valid time is returned
            '''Create a worklist for Momentum XML'''

            print(f"\n--- Create CSV Dispense list for Lynx ---")
            dispense_filename_sample, dispense_filename_media = lynx_csv.create(plate_data, plate_info, process_name)

            print(f"\n--- Create XML worklist for Momentum ---")
            momentum_xml.create(plate_data, plate_info, process_name, dispense_filename_sample, dispense_filename_media)

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}. It might have been moved or deleted quickly.")
    except Exception as e:
        print(f"An error occurred while processing {file_path}: {e}")
    finally:
        print(f"\n--- Finished processing: {file_path} ---\n")


# --- Watchdog Event Handler ---
class NewFileHandler(FileSystemEventHandler):
    """
    Custom event handler for watchdog to detect file creation events.
    """
    def __init__(self, watched_file, process_name):
        super().__init__()
        self.watched_file = watched_file
        self.process_name = process_name
        self.threshold = 0.7 # Example threshold value

    def on_created(self, event):
        """
        Called when a file is created.
        """
        watched_file_normalized = os.path.abspath(self.watched_file)
        event_file_normalized = os.path.abspath(event.src_path)

        if not event.is_directory and event_file_normalized == watched_file_normalized:  # Ensure it's the specific file
            file_extension = os.path.splitext(self.watched_file)[1].lower()
            if FILE_EXTENSIONS is None or file_extension in [ext.lower() for ext in FILE_EXTENSIONS]:
                process_csv_file(event.src_path, self.process_name, self.threshold)

    def on_modified(self, event):
        """
        Called when a file is modified.
        """
        watched_file_normalized = os.path.abspath(self.watched_file)
        event_file_normalized = os.path.abspath(event.src_path)

        if not event.is_directory and event_file_normalized == watched_file_normalized:
            process_csv_file(event.src_path, self.process_name, self.threshold)


# --- Main Script Execution ---
def start_watching(watched_file, process_name):
    """
    Start watching the specified folder for new files.
    :param watched_file: The watch file is pass by the user in the main function.
    :return: None
    """
    # Extract the parent directory of the file
    parent_dir = os.path.dirname(watched_file)

    event_handler = NewFileHandler(watched_file, process_name)
    observer = Observer()
    observer.schedule(event_handler, parent_dir, recursive=False) # Set recursive=True to watch subdirectories

    observer.start()
    try:
        while True:
            time.sleep(1) # Keep the main thread alive
    except KeyboardInterrupt:
        observer.stop()
        print(f"\nStopped watching file: {watched_file}")
    observer.join()
