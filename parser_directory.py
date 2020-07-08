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

#parse $config.dat e produrre il config.py preliminare al quale si appenderanno le definizioni successive dei diversi moduli
parser_file.parse(files['basics.dat'], os.path.dirname(os.path.abspath(__file__)) + "/basics_dat.py", "w+", import_config=False)
parser_file.parse(files['$machine.dat'], os.path.dirname(os.path.abspath(__file__)) + "/machine_dat.py", "w+", import_config=False)
parser_file.parse(files['$robcor.dat'], os.path.dirname(os.path.abspath(__file__)) + "/robcor_dat.py", "w+", import_config=False)
parser_file.parse(files['p00.dat'], os.path.dirname(os.path.abspath(__file__)) + "/p00_dat.py", "w+", import_config=True)
parser_file.parse(files['p00.src'], os.path.dirname(os.path.abspath(__file__)) + "/p00.py", "w+", import_config=True)

parser_file.parse(files['$config.dat'], os.path.dirname(os.path.abspath(__file__)) + "/config.py", "w+", import_config=False)
parser_file.parse(files['sds7000.dat'], os.path.dirname(os.path.abspath(__file__)) + "/sds7000_dat.py", "w+", import_config=True)
parser_file.parse(files['sds7000.src'], os.path.dirname(os.path.abspath(__file__)) + "/sds7000.py", "w+", import_config=True)

import basics_dat
from sds7000_dat import *
import sds7000
sds7000.sds7000()

#parse modulename.dat
#parse modulename.src
#parse sps.sub


