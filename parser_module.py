import re
import os
import generic_regexes
import parser_instructions
import flow_chart_graphics

"""
    This parses dat and src files
        analyzed instructions
"""

def fread_lines(file_path_and_name):
    content = None
    with open(file_path_and_name, "r") as f:
        content = f.readlines()
    return content


class KRLModuleSrcFileParser(parser_instructions.KRLGenericParser):
    file_path_name = ''   # the str path and file
    
    def __init__(self, file_path_name):
        # read all instructions, parse and collect definitions
        self.indent_comments = False
        self.file_path_name = file_path_name
        permissible_instructions = ['procedure begin', 'function begin']
        permissible_instructions_dictionary = {k:v for k,v in parser_instructions.instructions_defs.items() if k in permissible_instructions}
        parser_instructions.KRLGenericParser.__init__(self, permissible_instructions_dictionary)

    def parse_single_instruction(self, code_line_original, code_line, instruction_name, match_groups, file_lines):
        translation_result_tmp = []

        if instruction_name == 'procedure begin':
            param_list = code_line.split('(')[1].split(')')[0].split(',')
            param_names = [x.split(':')[0].strip() for x in param_list]
            param_names = [re.sub(generic_regexes.index_3d, '', x) for x in param_names]
            is_global = not match_groups[0] is None 
            procedure_name = match_groups[2]
            translation_result_tmp.append("@global_defs.interruptable_function_decorator")
            translation_result_tmp.append( "def " + procedure_name + "(" + ", ".join(param_names) + "):" )
            
            node = parser_instructions.KRLProcedureParser( procedure_name, param_names )
            self.append(node)
            _translation_result_tmp, file_lines = node.parse(file_lines)
            self.draw()
            if len(_translation_result_tmp):
                translation_result_tmp.extend(_translation_result_tmp)
            
        if instruction_name == 'function begin':
            param_list = code_line.split('(')[1].split(')')[0].split(',')
            param_names = [x.split(':')[0].strip() for x in param_list]
            param_names = [re.sub(generic_regexes.index_3d, '', x) for x in param_names]
            procedure_name = match_groups[3]
            is_global = not match_groups[0] is None 
            return_value_type_name = match_groups[2]
            translation_result_tmp.append("@global_defs.interruptable_function_decorator")
            translation_result_tmp.append( "def " + procedure_name + "(" + ", ".join(param_names) + "): #function returns %s"%return_value_type_name )

            node = parser_instructions.KRLFunctionParser( procedure_name, param_names, return_value_type_name )
            self.append(node)
            _translation_result_tmp, file_lines = node.parse(file_lines)
            self.draw()
            if len(_translation_result_tmp):
                translation_result_tmp.extend(_translation_result_tmp)
        
        _translation_result_tmp, file_lines = parser_instructions.KRLGenericParser.parse_single_instruction(self, code_line_original, code_line, instruction_name, match_groups, file_lines)
        if len(_translation_result_tmp):
            translation_result_tmp.extend(_translation_result_tmp)

        return translation_result_tmp, file_lines 


class KRLModuleDatFileParser(parser_instructions.KRLGenericParser):
    file_path_name = ''   # the str path and file
    
    def __init__(self, file_path_name):
        # read all instructions, parse and collect definitions
        self.indent_comments = False
        self.file_path_name = file_path_name
        permissible_instructions = ['dat begin', 'dat end', 'enum definition', 'struc declaration']
        permissible_instructions_dictionary = {k:v for k,v in parser_instructions.instructions_defs.items() if k in permissible_instructions}
        parser_instructions.KRLGenericParser.__init__(self, permissible_instructions_dictionary)
        permissible_instructions = ['variable declaration', 'variable assignment']
        permissible_instructions_dictionary = {k:v for k,v in parser_instructions.instructions_defs.items() if k in permissible_instructions}
        self.permissible_instructions_dictionary.update(permissible_instructions_dictionary)
        
    def parse_single_instruction(self, code_line_original, code_line, instruction_name, match_groups, file_lines):
        translation_result_tmp = []

        if instruction_name == 'dat begin':
            return translation_result_tmp, file_lines

        if instruction_name == 'dat end':
            return translation_result_tmp, file_lines

        _translation_result_tmp, file_lines = parser_instructions.KRLGenericParser.parse_single_instruction(self, code_line_original, code_line, instruction_name, match_groups, file_lines)
        if len(_translation_result_tmp):
            translation_result_tmp.extend(_translation_result_tmp)

        return translation_result_tmp, file_lines 
            

class KRLModule(flow_chart_graphics.FlowInstruction):
    name = ''
    module_dat = None   # KRLDat instance
    module_src = None   # KRLSrc instance
    def __init__(self, module_name, dat_path_and_file = '', src_path_and_file = '', imports_to_prepend = ''):
        flow_chart_graphics.FlowInstruction.__init__(self)
        self.name = module_name
        if len(dat_path_and_file):
            self.module_dat = KRLModuleDatFileParser(dat_path_and_file)
            self.append(self.module_dat)
            file_lines = fread_lines(dat_path_and_file)
            translation_result, file_lines = self.module_dat.parse(file_lines)
            self.draw()
            with open(os.path.dirname(os.path.abspath(__file__)) + "/%s.py"%self.name, 'w+') as f:
                f.write(imports_to_prepend)
                for l in translation_result:
                    f.write(l + '\n')
            
        if len(src_path_and_file):
            has_dat = not (self.module_dat is None)
            self.module_src = KRLModuleSrcFileParser(src_path_and_file)
            self.append(self.module_src)
            file_lines = fread_lines(src_path_and_file)
            translation_result, file_lines = self.module_src.parse(file_lines)
            self.draw()
            with open(os.path.dirname(os.path.abspath(__file__)) + "/%s.py"%self.name, ('a+' if has_dat else 'w+')) as f:
                if not has_dat:
                    f.write(imports_to_prepend)
                for l in translation_result:
                    f.write(l + '\n')
