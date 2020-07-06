"""
given a base directory
    it searches for all files/modules and calls the file_parser to translate KRL into python language

    special files like $config.dat and sps.sub have to be managed differently
"""

import os


def run_fast_scandir(root_dir, dirs, files, ext):    # dir: str, ext: list
    dirs.append(root_dir)
    for f in os.scandir(root_dir):
        if f.is_dir():
            dirs.append(f.path)
            run_fast_scandir(f.path, dirs, files, ext)
        if f.is_file():
            #if os.path.splitext(f.name)[1].lower() in ext:
            files.append(f.path)

dirs = []
files = []

run_fast_scandir('./', dirs, files, [".jpg"])
#print(dirs)
print('\n'.join(files))
