# Cyber-Phasmid
<h1> hostapd.conf</h1>
Configuration file for hostapd tested on Raspberry Pi 4
<h1>Physical Switch</h1>
Python script to enable and disable hostapd. If the access point is configured using NetworkManager, you need to uncomment the commented sections of the code and comment out the parts related to hostapd. While NetworkManager simplifies access point configuration, it may cause lag during remote connections because it continues to use the WiFi module for network scanning, even when set up as an access point.
<h1>Wardrive with Kismet</h1>
Python script to streamline starting and stopping Kismet with the default configuration file for wardriving mode.
It is possible to specify which adapters to use and which GPS device to enable directly at the start of Kismet by adding the appropriate options to the KISMET_OPTIONS variable, or through Kismet's configuration files.

Features:
- Option 1: Start Kismet.
- Option 2: Stop Kismet.
- Option 3: Archive files from Kismet's working directory into the directory defined by the ARCHIVE_DIR variable. This process organizes files into a folder structure based on their creation date.
- Option 4: Merge recorded wiglecsv files into a single deduplicated CSV file. During execution, the script allows for the removal of specific MAC addresses or SSIDs either interactively or as predefined values set within the script.
- Option 5: Generate a map displaying markers for each recorded access point.

Configuration:
The script requires initial setup by editing key variables at the beginning of the script. The most important variables are:

- KISMET_WORKING_DIR: Path to Kismet's working directory.
- ARCHIVE_DIR: Directory where archived files will be stored.
- OUTPUT_FILE_PATH: Path for the generated output file.
- PREDEFINED_DELETE_VALUES: Predefined MAC addresses or SSIDs to exclude.

The script is fully commented to facilitate understanding of its functionality. Refer to the comments for detailed explanations.

For a demonstration, watch the [YouTube video](https://youtu.be/FhOUriX0iL8).
