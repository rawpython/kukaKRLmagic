"""
given a base directory
    it searches for all files/modules and calls the file_parser to translate KRL into python language

    special files like $config.dat and sps.sub have to be managed differently
"""

import os
import parser_file

def run_fast_scandir(root_dir, dirs, files, ext):    # dir: str, ext: list
    for f in os.scandir(root_dir):
        if f.is_dir():
            dirs[f.name] = f.path
            run_fast_scandir(f.path, dirs, files, ext)
        if f.is_file():
            #if os.path.splitext(f.name)[1].lower() in ext:
            files[f.name] = f.path

dirs = {}
files = {}
run_fast_scandir(os.path.dirname(os.path.abspath(__file__)), dirs, files, [".jpg"])
#print(dirs)
print(files)

#parse $config.dat e produrre il globals.py preliminare al quale si appenderanno le definizioni successive dei diversi moduli
parser_file.parse(files['$config.dat'], os.path.dirname(os.path.abspath(__file__)) + "/system_vars.py", "w+")
parser_file.parse(files['sds7000.dat'], os.path.dirname(os.path.abspath(__file__)) + "/sds7000.py", "w+")
parser_file.parse(files['sds7000.src'], os.path.dirname(os.path.abspath(__file__)) + "/sds7000.py", "a+")
#parse modulename.dat
#parse modulename.src
#parse sps.sub


