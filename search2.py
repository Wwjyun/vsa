import os
import subprocess

def open_image_from_search(option,number, code, no, button_name):
    folder_path = f"D:/Database-PC/{option}/roi/{number}/{button_name}/{code}"
    file_path = os.path.join(folder_path, f"{no}.tiff")
    
    if os.path.isfile(file_path):
        if os.name == 'nt':  # For Windows
            os.startfile(file_path)
        elif os.name == 'posix':  # For macOS and Linux
            subprocess.call(('open', file_path))
        else:
            print(f"Unsupported OS: {os.name}")
    else:
        print(f"File not found: {file_path}")
