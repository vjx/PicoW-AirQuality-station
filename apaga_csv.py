import os

def delete_csv_files():
    files = os.listdir()
    for file in files:
        if file.endswith(".csv"):
            try:
                os.remove(file)
                print(f"Deleted: {file}")
            except OSError as e:
                print(f"Error deleting {file}: {e}")

# Run the function
delete_csv_files()
