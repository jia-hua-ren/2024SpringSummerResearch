import os
import subprocess
import sys

def run_script_on_files(base_directory, python_script):
    """
    Traverse directories starting from base_directory and run python_script on each .c or .cpp file.
    """
    for root, dirs, files in os.walk(base_directory):
        for file in files:
            if file.endswith('.c') or file.endswith('.cpp'):
                file_path = os.path.join(root, file)
                print(f"Processing file: {file_path}")
                # Run the Python script with the file path as an argument
                result = subprocess.run(['python', python_script, file_path], capture_output=True, text=True)
                # Print the output and error from the script
                print(result.stdout)
                if result.stderr:
                    print(f"Error: {result.stderr}")

def main():
    if len(sys.argv) != 3:
        print("Usage: python run_on_files.py <directory> <python-script>")
        sys.exit(1)

    base_directory = sys.argv[1]
    python_script = sys.argv[2]

    if not os.path.isdir(base_directory):
        print(f"Error: The directory '{base_directory}' does not exist.")
        sys.exit(1)

    if not os.path.isfile(python_script):
        print(f"Error: The Python script '{python_script}' does not exist.")
        sys.exit(1)

    run_script_on_files(base_directory, python_script)

if __name__ == "__main__":
    main()
