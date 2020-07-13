import re
import os
import generic_regexes

"""
    This parses dat and src files
        analyzed instructions
"""

instructions_defs = {
    'meta instruction':     r"(?:^ *\&)",
    'dat begin':            generic_regexes.line_begin + "(DEFDAT +)" + generic_regexes.dat_name + "( +PUBLIC)?" + .line_end,       #creates a dat parser
    'dat end':              generic_regexes.a_line_containing("ENDDAT"),
    'procedure begin':      generic_regexes.line_begin + generic_regexes.global_def + "(DEF +)" + generic_regexes.function_name + " *\( *(" + generic_regexes.parameters_declaration + ")* *\)" + generic_regexes.line_end, #creates a procedure parser
    'function begin':       generic_regexes.line_begin + generic_regexes.global_def + "(DEFFCT +)" + "([^ ]+) +" + generic_regexes.function_name + " *\( *(" + generic_regexes.parameters_declaration + ")* *\)" + generic_regexes.line_end,  #creates a function parser
    'ext':                  generic_regexes.line_begin + "EXTP? +([^ \(]+) *\(",
    'extfct':               generic_regexes.line_begin + "EXTFCTP? +([^ ]+) +([^ \(]+) *\(",
    'signal decl':          generic_regexes.a_line_containing( generic_regexes.global_def + r"SIGNAL +([^ ]+) +((?:[^ \[]+)(?:\[ *[0-9]* *\])?)(?: +TO +((?:[^ \[]+)(?:\[ *[0-9]* *\])?))?" ),
}


def fread_lines(self, file_path_and_name):
    content = None
    with open(file_path_and_name, "r") as f:
        content = f.readlines()
    return content


class KRLModuleFileParser(KRLGenericParser):
    file_path_name = ''   # the str path and file

    def __init__(self, file_path_name):
        # read all instructions, parse and collect definitions
        self.file_path_name = file_path_name
        permissible_instructions = ['meta instruction', 'dat begin', 'dat end', 'procedure begin', 'function begin', 'ext', 'extfct', 'signal decl']
        permissible_instructions_dictionary = {k:v for k,v in d.iteritems() if k in permissible_instructions}
        KRLGenericParser.__init__(self, permissible_instructions_dictionary)
        file_lines = fread_lines(file_path_name)      
        translation_result, file_lines = self.parse(file_lines)

    def parse_single_instruction(code_line_original, code_line, instruction_name, match_groups):
        translation_result_tmp = []

        if instruction_name == 'meta instruction':
            continue

        if instruction_name == 'dat begin':
            continue

        if instruction_name == 'dat end':
            continue

        if instruction_name == 'procedure begin':
            param_list = code_line.split('(')[1].split(')')[0].split(',')
            param_names = [x.split(':')[0].strip() for x in param_list]
            param_names = [re.sub(array_index, '', x) for x in param_names]
            is_global = not match_groups[0] is None 
            procedure_name = match_groups[2]
            translation_result_tmp.append( "def " + procedure_name + "(" + ", ".join(param_names) + "):" )
            
            node = KRLProcedureParser( procedure_name, param_names )
            translation_result_child, file_lines = node.parse( file_lines )
            translation_result_tmp.append( generic_regexes.indent_lines(translation_result_child) )
            
        if instruction_name == 'function begin':
            param_list = code_line.split('(')[1].split(')')[0].split(',')
            param_names = [x.split(':')[0].strip() for x in param_list]
            param_names = [re.sub(array_index, '', x) for x in param_names]
            procedure_name = match_groups[3]
            is_global = not match_groups[0] is None 
            return_value_type_name = match_groups[2]
            translation_result_tmp.append( "def " + procedure_name + "(" + ", ".join(param_names) + "): #function returns %s"%return_value_type_name )

            node = KRLFunctionParser( procedure_name, param_names, return_value_type_name )
            translation_result_child, file_lines = node.parse( file_lines )
            translation_result_tmp.append( generic_regexes.indent_lines(translation_result_child) )
            
        if instruction_name == 'ext':
            procedure_name = match_groups[0]
            r = re.search(line_begin+"EXTP", code_line, re.IGNORECASE)
            module_name = procedure_name #normally a function imported by EXT has the same name of the module in which it is contained. This seems not valid for EXTP
            if not r is None:
                module_name = 'kuka_internals'
            translation_result_tmp.append( "from %s import %s"%( module_name, procedure_name ) )

        if instruction_name == 'extfct':
            return_type, function_name = match_groups[0], match_groups[1]
            r = re.search(line_begin+"EXTFCTP", code_line, re.IGNORECASE)
            module_name = procedure_name #normally a function imported by EXT has the same name of the module in which it is contained. This seems not valid for EXTP
            if not r is None:
                module_name = 'kuka_internals'
            translation_result_tmp.append( "from %s import %s"%( module_name, procedure_name ) )

        if instruction_name == 'signal decl':
            is_global, signal_name, signal_start, signal_end = *match_groups[0]
            is_global = not is_global is None
            if signal_end is None:
                translation_result_tmp.append(("global_defs." if is_global else "") + "%s = signal(%s)"%(signal_name, signal_start))
            else:
                translation_result_tmp.append(("global_defs." if is_global else "") + "%s = signal(%s, %s)"%(signal_name, signal_start, signal_end))
        
        return translation_result_tmp, file_lines 
            

class KRLModule():
    name = ''
    module_dat = None   # KRLDat instance
    module_src = None   # KRLSrc instance
    def __init__(module_name, dat_path_and_file = '', src_path_and_file = ''):
        if len(dat_path_and_file):
            self.module_dat = KRLModuleFileParser(dat_path_and_file)

        if len(src_path_and_file):
            self.module_src = KRLModuleFileParser(src_path_and_file)

