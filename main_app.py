#!/usr/local/bin/python
# -*- coding: latin-1 -*-

import os
from os import *
#import parser_file
import parser_module
import remi
import remi.gui as gui
from remi import start, App
import threading
import global_defs
import parser_instructions

def _i(module_name): #import
    return '#include "%s.h"\n'%module_name


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

        print("Processing kuka internals, please wait...")
        
        parser_module.KRLModule('global_defs_user', '', src_path_and_file=self.all_files['global_defs_user.src'], imports_to_prepend = _i('kuka_internals')),
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
        
        print("Kuka internals, please wait...")
        """
        self.modules.extend( [
                parser_module.KRLModule('sample_program', self.r1_files['sample_program.dat'], src_path_and_file=self.r1_files['sample_program.src'], imports_to_prepend = _i('global_defs') + _i('config') + _i('operate_r1'))
        ])
        """
        self.modules.extend( [
                parser_module.KRLModule('scd1000', self.r1_files['scd1000.dat'], src_path_and_file=self.r1_files['scd1000.src'], imports_to_prepend = _i('global_defs') + _i("assert") + _i('config') + _i('operate_r1') + _i('global_defs_user')),
                #parser_module.KRLModule('sample_program', self.r1_files['sample_program.dat'], src_path_and_file=self.r1_files['sample_program.src'], imports_to_prepend = _i('global_defs') + _i('config') + _i('operate_r1') + _i('global_defs_user')),
            ])
        """
                parser_module.KRLModule('geometrylib', self.r1_files['geometrylib.dat'], src_path_and_file=self.r1_files['geometrylib.src'], imports_to_prepend = _i('global_defs') + _i('config') + _i('operate_r1')),
                parser_module.KRLModule('sds7000', self.r1_files['sds7000.dat'], src_path_and_file=self.r1_files['sds7000.src'], imports_to_prepend = _i('global_defs') + _i('config') + _i('operate_r1') + _i('geometrylib'))
        """
        
        
    def get_module(self, name):
        for m in self.modules:
            if m.name == name:
                return m

        return None

    def scandir(self, root_dir, dirs, files):
        for f in os.scandir(root_dir):
            if f.is_dir():
                dirs[f.name] = f.path
                self.scandir(f.path, dirs, files)
            if f.is_file():
                files[f.name] = f.path


class MyApp(App):
    def __init__(self, *args):
        res_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'res')
        #static_file_path can be an array of strings allowing to define
        #  multiple resource path in where the resources will be placed
        super(MyApp, self).__init__(*args, static_file_path=res_path)

    def idle(self):
        #idle loop, you can place here custom code
        # avoid to use infinite iterations, it would stop gui update
        pass

    def main(self):
        #creating a container VBox type, vertical (you can use also HBox or Widget)
        main_container = gui.VBox(style={'margin':'0px auto'})

        #reset global definitions
        parser_instructions.init_user_global_def()

        project = KRLProject( os.path.dirname(os.path.abspath(__file__)) )

        main_container.append(project.get_module('scd1000'))
        #main_container.append(project.get_module('sample_program'))
        #main_container.append(project.get_module('geometrylib'))
        #main_container.append(project.get_module('sds7000'))
        #m = project.get_module('bas')
        #main_container.append(m)

        # The interrupts use the main thread, so the robot program have to be executed in the main thread
        # maybe another process have to be created 
        #global_defs.robot_interpreter_thread = threading.Thread(target=self.run_program, daemon=False)
        #global_defs.robot_interpreter_thread.start()
        #self.run_program()
        #global_defs.submit_interpreter_thread = None
        
        # returning the root widget
        return main_container

    def run_program(self):
        import sample_program
        sample_program.sample_program()


if __name__ == "__main__":
    # starts the webserver
    start(MyApp, address='127.0.0.1', port=8083, start_browser=True, username=None, password=None, update_interval=0.005)
