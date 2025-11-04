import csv
import os
from pathlib import PureWindowsPath
from datetime import datetime


# Global path to save the Lynx CSV files
LYNX_ROOT_PATH = PureWindowsPath('Y:\\MethodManager4\\Momentum_Input\\')
# LYNX_ROOT_PATH = ('/Users/flavia/PycharmProjects/growth_profile_watcher/output/') # used for testing


def create(plate_data, plate_info, process_name):
    """
    Create a Lynx CSV file to dispense volumes based on normalized OD values.
    :param plate_data: List of dictionaries containing plate growth data.
    :param plate_info: List of dictionaries containing plate_type, plate_id, num_rows, and num_columns.
    :param process_name: Name of the process.
    :return: Path to the created Lynx CSV file.
    """
    # Extract plate information
    plate_id = plate_info[0]['plate_id']
    num_rows = plate_info[0]['num_rows']
    num_columns = plate_info[0]['num_columns']

    main_plate_id = plate_id.split("_")[0]

    # Define output CSV file name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename_sample = f"Sample_{main_plate_id}.csv"
    # output_filename_sample = f"Sample_{main_plate_id}_{timestamp}.csv"
    output_filename_media = f"Media_{main_plate_id}.csv"
    # output_filename_media = f"Media_{main_plate_id}_{timestamp}.csv"
    output_filepath_sample = os.path.join(LYNX_ROOT_PATH, output_filename_sample)
    output_filepath_media = os.path.join(LYNX_ROOT_PATH, output_filename_media)

    # Extract the last entry of plate data for OD values
    last_entry = plate_data[-1]
    wells_growth = last_entry['wells_growth']

    # Define parameters
    target_od = 3 # max OD value ideally close to 3
    target_volume = 25  # µL when OD is max value 1:100 of total volume 2500 µL
    max_dispense_volume = 300  # µL maximum dispense volume
    min_dispense_volume = 10  # µL minimum dispense volume

    # Lists to hold calculated volumes
    dispense_volumes_sample = []
    dispense_volumes_media = []

    for od in wells_growth:
        try:
            od_value = float(od)
            if od_value == 0:
                # Handle zero OD: assign max sample volume (300µL) and 0µL media
                sample_volume = max_dispense_volume
            else:
                # Calculate sample dispense volume based on OD
                sample_volume = (target_volume / od_value) * target_od
                # Ensure the sample volume is within the allowed range
                sample_volume = max(min(sample_volume, max_dispense_volume), min_dispense_volume)

            # Calculate media dispense volume to top up to 300µL total
            # The second file is based on the first:
            # Total Volume (300µL) = Sample Volume + Media Volume
            media_volume = max_dispense_volume - sample_volume

            # Store calculated volumes
            dispense_volumes_sample.append(sample_volume)
            dispense_volumes_media.append(media_volume)
        except ValueError:
            # Handle invalid OD values (e.g., empty strings): Max sample, 0 media
            dispense_volumes_sample.append(max_dispense_volume)
            dispense_volumes_media.append(0.0)

    # --- Prepare and Write Sample Dispense CSV ---
    header = [f"VI;{num_columns};{num_rows}"] + [str(i) for i in range(1, num_columns + 1)]
    lynx_data_sample = [header]

    # Add rows for each plate row (A, B, C, ...)
    for row_index in range(num_rows):
        row_label = chr(65 + row_index)  # Convert to A, B, C, etc.
        row_data = [row_label] + [
            f"{dispense_volumes_sample[row_index * num_columns + col]:.2f}"
            for col in range(num_columns)
        ]
        lynx_data_sample.append(row_data)

    # Write to Lynx Sample CSV file
    with open(output_filepath_sample, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(lynx_data_sample)

    # --- Prepare and Write Media Dispense CSV ---
    lynx_data_media = [header]  # Use the same header for the media file

    # Add rows for each plate row (A, B, C, ...)
    for row_index in range(num_rows):
        row_label = chr(65 + row_index)  # Convert to A, B, C, etc.
        row_data = [row_label] + [
            f"{dispense_volumes_media[row_index * num_columns + col]:.2f}"
            for col in range(num_columns)
        ]
        lynx_data_media.append(row_data)

    # Write to Lynx Media CSV file
    with open(output_filepath_media, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(lynx_data_media)

    # print(f"Lynx Sample CSV file created: {output_filepath_sample}")
    # print(f"Lynx Media CSV file created: {output_filepath_media}")

    return output_filepath_sample, output_filepath_media