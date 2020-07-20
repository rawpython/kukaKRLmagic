"""
given a base directory
    it searches for all files/modules and calls the file_parser to translate KRL into python language

    special files like $config.dat and sps.sub have to be managed differently
"""

import os
#import parser_file
import parser_module

def _i(module_name): #import
    return "import %s\nfrom %s import *\n"%(module_name, module_name)

class KRLProject():
    dirs = None     # a dictionary of dict[path_name_str] = path_str
    all_files = None    # dict[file_name_str] = path_str + filename_str
    r1_files = None    # dict[file_name_str] = path_str + filename_str
    steu_files = None    # dict[file_name_str] = path_str + filename_str
    modules = None  # a dictionary[module_name_str] = KRLModule_instance
    def __init__(self, project_folder):
        #creates a dictionary of files with related folder
        self.dirs = {}
        self.all_files = {}
        self.r1_files = {}
        self.steu_files = {}
        self.modules = []
        self.scandir(project_folder, self.dirs, self.all_files)
        self.scandir(self.dirs['R1'], {}, self.r1_files)
        self.scandir(self.dirs['STEU'], {}, self.steu_files)

        self.modules.extend( [
            
            parser_module.KRLModule('kuka_internals', self.all_files['kuka_internals.dat'], src_path_and_file=self.all_files['kuka_internals.src'], imports_to_prepend = _i('global_defs')),
            parser_module.KRLModule('operate', self.r1_files['operate.dat'], src_path_and_file='', imports_to_prepend = _i('global_defs') + _i('kuka_internals')),
            parser_module.KRLModule('operate_r1', self.r1_files['operate_r1.dat'], src_path_and_file='', imports_to_prepend = _i('global_defs') + _i('operate')),
            parser_module.KRLModule('steu_option', self.steu_files['$option.dat'], src_path_and_file='', imports_to_prepend = _i('global_defs') + _i('operate')),
            parser_module.KRLModule('machine_dat', self.r1_files['$machine.dat'], src_path_and_file='', imports_to_prepend = _i('global_defs') + _i('operate')),
            parser_module.KRLModule('robcor_dat', self.r1_files['$robcor.dat'], src_path_and_file='', imports_to_prepend = _i('global_defs') + _i('operate') + _i('operate_r1')),
            parser_module.KRLModule('p00', self.r1_files['p00.dat'], src_path_and_file=self.r1_files['p00.src'], imports_to_prepend = _i('global_defs') + _i('operate')),
            parser_module.KRLModule('p00_subm', '', src_path_and_file=self.r1_files['p00_subm.src'], imports_to_prepend = _i('global_defs')),
            parser_module.KRLModule('config', self.r1_files['$config.dat'], src_path_and_file='', imports_to_prepend = _i('global_defs') + _i('operate') + _i('operate_r1') + _i('p00') + _i('p00_subm')),
            parser_module.KRLModule('collmonlib', self.r1_files['collmonlib.dat'], src_path_and_file=self.r1_files['collmonlib.src'], imports_to_prepend = _i('global_defs') + _i('config') + _i('robcor_dat') + _i('machine_dat') + _i('steu_option')),
            parser_module.KRLModule('bas', '', src_path_and_file=self.r1_files['bas.src'], imports_to_prepend = _i('global_defs') + _i('config') + _i('robcor_dat') + _i('machine_dat') + _i('steu_option') + _i('collmonlib')),
            
            parser_module.KRLModule('ir_stopm', '', src_path_and_file=self.r1_files['ir_stopm.src'], imports_to_prepend = _i('global_defs')),
            parser_module.KRLModule('sample_program', self.r1_files['sample_program.dat'], src_path_and_file=self.r1_files['sample_program.src'], imports_to_prepend = _i('global_defs') + _i('config') + _i('operate_r1')) ])

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

project = KRLProject( os.path.dirname(os.path.abspath(__file__)) )

import sample_program
sample_program.sample_program()
