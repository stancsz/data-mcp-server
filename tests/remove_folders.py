import shutil
import os
import glob

def remove_folders_by_pattern(pattern):
    folders = glob.glob(pattern)
    removed_any = False
    for folder in folders:
        if os.path.isdir(folder):
            shutil.rmtree(folder)
            print(f"Removed folder: {folder}")
            removed_any = True
    if not removed_any:
        print("No matching folders found.")

if __name__ == "__main__":
    pattern = "tests/dummy project__*__test__"
    remove_folders_by_pattern(pattern)
