#!/bin/bash

# Check if a directory path is provided as an argument
if [ -z "$1" ]; then
    echo "Usage: $0 /path/to/directory"
    exit 1
fi

# Specify the directory
DIRECTORY="$1"

# Check if the provided argument is a valid directory
if [ ! -d "$DIRECTORY" ]; then
    echo "Error: $DIRECTORY is not a valid directory"
    exit 1
fi

# Loop through each file in the directory
for FILE in "$DIRECTORY"/*; do
    if [ -f "$FILE" ]; then
        echo "Generating tests for $FILE"
        # Run your command on the file

	output="$(/utbot/utbot_distr/utbot_run_system.sh cli generate -p "$DIRECTORY" snippet --file-path "$FILE" 2>&1)"
    	echo "$output"
	mkdir -p ""$DIRECTORY"/compileerror/"
	if [[ "$output" =~ "recipe for target 'build'" ]]; then
		mv "$FILE" "$DIRECTORY"/compileerror/
	fi
    fi
done

