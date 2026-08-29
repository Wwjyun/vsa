import shutil


def download_folder(source_folder, target_folder):
    try:
        shutil.copytree(source_folder, f"{target_folder}/{source_folder.split('/')[-1]}")
    except Exception as e:
        print(f"Error copying folder: {e}")
