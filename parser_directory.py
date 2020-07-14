"""
given a base directory
    it searches for all files/modules and calls the file_parser to translate KRL into python language

    special files like $config.dat and sps.sub have to be managed differently
"""

import os
#import parser_file
import parser_module

class KRLProject():
    dirs = None     # a dictionary of dict[path_name_str] = path_str
    files = None    # dict[file_name_str] = path_str + filename_str
    modules = None  # a dictionary[module_name_str] = KRLModule_instance
    def __init__(self, project_folder):
        #creates a dictionary of files with related folder
        self.dirs = {}
        self.files = {}
        self.scandir(project_folder, self.dirs, self.files)
        module = parser_module.KRLModule('config', self.files['$config.dat'], src_path_and_file='')

    def scandir(self, root_dir, dirs, files):
        for f in os.scandir(root_dir):
            if f.is_dir():
                dirs[f.name] = f.path
                self.scandir(f.path, dirs, files)
            if f.is_file():
                files[f.name] = f.path


#parse $config.dat e produrre il config.py preliminare al quale si appenderanno le definizioni successive dei diversi moduli
"""
parser_file.parse(files['kuka_internals.dat'], os.path.dirname(os.path.abspath(__file__)) + "/kuka_internals.py", "w+", imports_to_prepend='')
parser_file.parse(files['operate.dat'], os.path.dirname(os.path.abspath(__file__)) + "/operate.py", "w+", imports_to_prepend='')
parser_file.parse(files['operate_r1.dat'], os.path.dirname(os.path.abspath(__file__)) + "/operate_r1.py", "w+", imports_to_prepend='import operate\nfrom operate import *')
parser_file.parse(files['$machine.dat'], os.path.dirname(os.path.abspath(__file__)) + "/machine_dat.py", "w+", imports_to_prepend='')
parser_file.parse(files['$robcor.dat'], os.path.dirname(os.path.abspath(__file__)) + "/robcor_dat.py", "w+", imports_to_prepend='')
parser_file.parse(files['p00.dat'], os.path.dirname(os.path.abspath(__file__)) + "/p00_dat.py", "w+", imports_to_prepend='')
parser_file.parse(files['p00.src'], os.path.dirname(os.path.abspath(__file__)) + "/p00.py", "w+", imports_to_prepend='')
parser_file.parse(files['p00_subm.src'], os.path.dirname(os.path.abspath(__file__)) + "/p00_subm.py", "w+", imports_to_prepend='')

parser_file.parse(files['bas.src'], os.path.dirname(os.path.abspath(__file__)) + "/bas.py", "w+", imports_to_prepend='import config\nfrom config import *')
parser_file.parse(files['$config.dat'], os.path.dirname(os.path.abspath(__file__)) + "/config.py", "w+", imports_to_prepend='import operate\nfrom operate import *\nimport operate_r1\nfrom operate_r1 import *')
parser_file.parse(files['ir_stopm.src'], os.path.dirname(os.path.abspath(__file__)) + "/ir_stopm.py", "w+", imports_to_prepend='')
parser_file.parse(files['sample_program.dat'], os.path.dirname(os.path.abspath(__file__)) + "/sample_program.py", "w+", imports_to_prepend='import config\nfrom config import *')
parser_file.parse(files['sample_program.src'], os.path.dirname(os.path.abspath(__file__)) + "/sample_program.py", "a+", imports_to_prepend='')
import kuka_internals
"""
#import sample_program
#sample_program.sample_program()

project = KRLProject( os.path.dirname(os.path.abspath(__file__)) )

