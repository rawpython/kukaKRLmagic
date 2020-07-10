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
    'procedure end':        generic_regexes.a_line_containing("END"),
    'function begin':       generic_regexes.line_begin + generic_regexes.global_def + "(DEFFCT +)" + "([^ ]+) +" + generic_regexes.function_name + " *\( *(" + generic_regexes.parameters_declaration + ")* *\)" + generic_regexes.line_end,  #creates a function parser
    'function end':         generic_regexes.a_line_containing("ENDFCT"),
}

         


class KRLModule():
    def __init__(project_folder, module_name):

simple_instructions_to_replace = {
    r'\$IN':  '$inputs',
    r'\$OUT':  '$outputs',
    r'\$':  'global_defs.',
    '#':    '',
    ';':    '#',
    '<>':   '!=',
    'B_EXOR':  '^',
    'B_AND':   '&',
    'B_OR':    '|',
    'EXOR':    '^',
    'NOT':  'not',
    'AND':  'and',
    'OR':   'or',
    '\[ *\]': '',
    '\t':   ' ',
    'async':'_async', #found in operate.dat
    'class':'_class', #found in operate.dat
    'sys':'_sys', #used somewhere. replacing to not be confused with python module _sys
    ', *,':   ', None,', #KRL syntax null parameters in function calls
    r'NOT *\(': 'global_def._not(', #KRL bit complement NOT(VALUE)
}

interrupt_declaration_template = """
def %(interrupt_name)s():
    if interrupt_flags[%(interrupt_number)s]:
        if %(condition)s:
            %(instruction)s
interrupts[%(interrupt_number)s] = %(interrupt_name)s"""

trigger_distance_declaration_template = """
def %(trigger_name)s():
    %(instruction)s
threading.Timer(%(delay)s, %(trigger_name)s).start()"""

trigger_path_declaration_template = """
#this should be scheduled at path=%(path)s, to be implemented
def %(trigger_name)s():
    %(instruction)s
threading.Timer(%(delay)s, %(trigger_name)s).start()"""

class Procedure():
    name = ""
    param_names = None
    callers_list = None
    calling_list = None
    def __init__(self, name, param_names, callers_list, calling_list):
        self.name = name
        self.param_names = param_names
        self.callers_list = callers_list
        self.calling_list = calling_list

class Function(Procedure):
    return_type_name = ""
    def __init__(self, return_type_name, *args):
        Procedure.__init__(self, *args)
        self.return_type_name = return_type_name


def parse(filename_in, filename_out, write_mode, imports_to_prepend=''):
    fin = open(filename_in, "r")
    lines = fin.readlines()
    fin.close()

    fout = open(filename_out, write_mode)
    fout.write("import global_defs\nfrom global_defs import *\n")
    fout.write(imports_to_prepend + "\n")
    
    code_block_dictionary = {}
    actual_code_block = None

    indent = 0
    indent_var = 0
    out_line = []
    uuid = 0 #a unique number to be incremented when used
    pass_to_be_added = False #it indicates if a pass instruction have to be added to empty procedures or functions
    switch_value_list = list() #takes mem of the switch value actually in process

    for code_line in lines:

        #this is only for debugging for breackpoint at certain instruction
        if "E6POS pstart, pend" in code_line:
            print("")

        #spaces are removed to keep the indentation consistent in all the code, as required by Python
        code_line = code_line.strip()
        #since KRL is case insensitive, and Python is case sensitive, the code is transformed to lower making it all the variable names equal in the code
        code_line = code_line.lower()

        #common keywords are replaced as per Python spelling, i.e. TRUE becomes True
        for k,v in simple_instructions_to_replace.items():
            code_line = re.sub(k, v, code_line, flags=re.IGNORECASE)
        
        #this should remove end of line comment
        endofline_comment_to_append = re.search(line_end, code_line).span()
        endofline_comment_to_append = code_line[endofline_comment_to_append[0]:endofline_comment_to_append[1]]
        code_line = code_line.replace(endofline_comment_to_append, "")

        #replace strings "..." with r"..." to skip python special sequences
        code_line_new = ''
        while True:
            r = re.search(re_string, code_line) 
            if r is None:
                break
            code_line_new = code_line_new + code_line[0:r.span()[0]]
            code_line_new = code_line_new + 'r' + code_line[r.span()[0]:r.span()[1]]
            code_line = code_line[r.span()[1]:]
        code_line = code_line_new + code_line

        #replace binary numbers
        result = re.search(re_binary_number,code_line)
        if not result is None:
            value = result.groups()[0]
            code_line = code_line.replace(code_line[result.span()[0]:result.span()[1]], "0b%s"%value) 

        #replace { } bracket defined structs
        if '{' in code_line:
            if '}' in code_line:
                #"{E6POS: X 0, Y 0, Z 0, A 0, B 0, C 0}"
                #re.search(line_begin + r"(\{[: _-\+\$a-zA-Z0-9]+\})" + line_end)
                while True:
                    reg = r"\{ *([^ :\(\)\{\}\,]+) *:"
                    items = re.search(reg, code_line)
                    """
                    >>> re.search(r"\{ *([_\-\+\$a-zA-Z0-9]+) *:", "{E6POS: x 1, y 2 ,z 0, f { E6AXIS : a1 10, a2 1, a3 40 }}").groups()
                    ('E6POS',)
                    """
                    if items is None:
                        break
                    items = items.groups()
                    code_line = re.sub( reg, items[0] + "(",  code_line )
                code_line = code_line.replace('}', ')')
                code_line = code_line.replace('{', 'generic_struct(')
                #putting = after field name
                while True:
                    fields_and_values = re.search('[:\(\{\=,)]{1} *([^:,\(\{="\)\} ]+) ([^\)=\},; ]+)', code_line)
                    if fields_and_values is None:
                        break
                    field_and_value = code_line[fields_and_values.span()[0]+1:fields_and_values.span()[1]]
                    field_and_value = field_and_value.strip()
                    #replace the first occurrence of the found field, with the field replacing the first space occurrence with equal = sign 
                    code_line = code_line.replace(field_and_value, field_and_value.replace(' ', '=', 1), 1)


        out_line = [code_line]
        indent_var = 0

        result = None 
        instruction_name = ""
        if re.search(re_comment, code_line) is None:
            for k,v in instructions_defs.items():
                result = re.search(v, code_line, re.IGNORECASE) 
                if not result is None:
                    instruction_name = k
                    break

        if not (instruction_name in ('procedure begin', 'function begin', 'ext', 'extfct')):
            #replacing geometric addition operator :
            while True:
                geoadd = re.search(re_geometric_addition_operator, code_line)
                is_not_a_string = (re.search(re_string_python, code_line) == None)
                if (not geoadd is None) and is_not_a_string:
                    span = geoadd.span()
                    operands = geoadd.groups()[0]
                    operands = operands.split(':')
                    to_be_replaced = code_line[span[0]:span[1]]
                    code_line = code_line.replace(to_be_replaced, "_geometric_addition_operator(%s, %s)"%(operands[0], operands[1]))
                else:
                    break
            out_line = [code_line]


        if not (instruction_name in ('procedure end', 'function end', '', 'case', 'default', 'else', 'endif', 'variable declaration')):
            pass_to_be_added = False

        if instruction_name == 'meta instruction':
            continue
        
        if instruction_name == 'dat begin':
            continue

        if instruction_name == 'dat end':
            continue
        
        if instruction_name == 'continue':
            out_line = ['global_defs.robot.do_not_stop_ADVANCE_on_next_IO()']

        if instruction_name == 'signal decl':
            is_global, signal_name, signal_start, signal_end = result.groups()
            is_global = not is_global is None
            if signal_end is None:
                out_line = [("global_defs." if is_global else "") + "%s = signal(%s)"%(signal_name, signal_start)]
            else:
                out_line = [("global_defs." if is_global else "") + "%s = signal(%s, %s)"%(signal_name, signal_start, signal_end)]

        if instruction_name == 'wait sec':
            t = result.groups()[0]
            out_line = ['time.sleep(%s)'%t]

        if instruction_name == 'wait for':
            condition = result.groups()[0]
            out_line = ['while not (%s):time.sleep(0.1)'%condition]

        if instruction_name == 'interrupt decl':
            is_global, interrupt_number, condition, instruction = result.groups()
            is_global = not is_global is None 
            interrupt_declaration = interrupt_declaration_template%{'interrupt_number':interrupt_number, 'condition':condition, 'instruction':instruction, 'interrupt_name':'_interrupt%s'%interrupt_number}
            out_line = [*interrupt_declaration.split('\n')]
            #out_line = ['interrupts[%s] = """if %s:%s""" '%(interrupt_number, condition, instruction)] #to be evaluated cyclically with eval
        if instruction_name == 'interrupt on':
            interrupt_number = result.groups()[0]
            out_line = ['interrupt_flags[%s] = True'%interrupt_number]
        if instruction_name == 'interrupt off':
            interrupt_number = result.groups()[0]
            out_line = ['interrupt_flags[%s] = False'%interrupt_number]

        if instruction_name == 'trigger distance':
            distance, delay, instruction = result.groups()
            trigger_func_name = 'trigger_func%s'%uuid
            uuid = uuid + 1
            trigger_declaration = trigger_distance_declaration_template%{'trigger_name':trigger_func_name, 'instruction':instruction, 'delay':delay}
            out_line = [*trigger_declaration.split('\n')]
            
            
        if instruction_name == 'trigger path':
            path, delay, instruction = result.groups()
            trigger_func_name = 'trigger_func%s'%uuid
            uuid = uuid + 1
            trigger_declaration = trigger_path_declaration_template%{'trigger_name':trigger_func_name, 'instruction':instruction, 'delay':delay, 'path':path}
            out_line = [*trigger_declaration.split('\n')]

        if instruction_name == 'procedure begin':
            param_list = code_line.split('(')[1].split(')')[0].split(',')
            param_names = [x.split(':')[0].strip() for x in param_list]
            param_names = [re.sub(array_index, '', x) for x in param_names]
            is_global = not result.groups()[0] is None 
            procedure_name = result.groups()[2]
            out_line = ["def " + procedure_name + "(" + ", ".join(param_names) + "):"]
            indent_var = 1
            actual_code_block = Procedure(procedure_name, param_names, [], [])
            code_block_dictionary[procedure_name] = actual_code_block
            pass_to_be_added = True
        if instruction_name == 'procedure end':
            indent_var = -1
            out_line = ["pass"] if pass_to_be_added else None

        if instruction_name == 'function begin':
            param_list = code_line.split('(')[1].split(')')[0].split(',')
            param_names = [x.split(':')[0].strip() for x in param_list]
            param_names = [re.sub(array_index, '', x) for x in param_names]
            is_global = not result.groups()[0] is None 
            return_value_type_name = result.groups()[2]
            out_line = ["def " + result.groups()[3] + "(" + ", ".join(param_names) + "): #function returns %s"%return_value_type_name]
            indent_var = 1

            """
            re.search(re_function_decl,"DEFFCT bool potato_cips( CAP:OUT , CIOP:OUT)").groups()
            (None, 'DEFFCT ', 'bool', 'potato_cips', 'CIOP:OUT', 'CIOP', 'OUT')
            """
            actual_code_block = Function( return_value_type_name,procedure_name, param_names, [], [])
            code_block_dictionary[procedure_name] = actual_code_block
            pass_to_be_added = True
        if instruction_name == 'function end':
            indent_var = -1
            out_line = None
            out_line = ["pass"] if pass_to_be_added else None
        if instruction_name == 'function return':
            value = result.groups()[0]
            out_line = ["return" if value is None else ("return " + value)]

        if instruction_name == 'ext':
            procedure_name = result.groups()[0]
            r = re.search(line_begin+"EXTP", code_line, re.IGNORECASE)
            module_name = procedure_name #normally a function imported by EXT has the same name of the module in which it is contained. This seems not valid for EXTP
            if not r is None:
                module_name = 'kuka_internals'
            out_line = ["from %s import %s"%(module_name,procedure_name)]


        if instruction_name == 'extfct':
            return_type, function_name = result.groups()
            r = re.search(line_begin+"EXTFCTP", code_line, re.IGNORECASE)
            module_name = procedure_name #normally a function imported by EXT has the same name of the module in which it is contained. This seems not valid for EXTP
            if not r is None:
                module_name = 'kuka_internals'
            out_line = ["from %s import %s"%(module_name,procedure_name)]

        if instruction_name == 'if begin':
            """
            re.search(re_if_than, 'if VARSTATE("Zmultiplier")==#INITIALIZED then', re.IGNORECASE).groups()
            ('VARSTATE("Zmultiplier")==#INITIALIZED',)
            """
            condition = result.groups()[0].strip()
            out_line = ["if " + condition + ":"]
            indent_var = 1
            pass_to_be_added = True
        if instruction_name == 'else':
            out_line = []
            if pass_to_be_added:
                out_line = ['    pass']
            indent = indent - 1
            out_line.append("else:")
            indent_var = 1
            pass_to_be_added = True
        if instruction_name == 'if end':
            out_line = None
            if pass_to_be_added:
                out_line = ['    pass']
            indent_var = -1
            pass_to_be_added = False


        if instruction_name == 'switch':
            switch_value_list.append(result.groups()[0])
            out_line = None
            first_switch_instruction = True
        if instruction_name == 'case':
            out_line = []
            if pass_to_be_added:
                out_line = ['    pass']
            case_value = result.groups()[0]

            condition = "%s == %s:"%(switch_value_list[len(switch_value_list)-1], case_value)
            if ',' in case_value:
                case_values = case_value.split(',')
                condition = ' or '.join(['%s == %s'%(switch_value_list[len(switch_value_list)-1], x) for x in case_values]) + ':'

            if first_switch_instruction:
                out_line.append("if " + condition)
            else:
                indent = indent - 1
                out_line.append("elif " + condition)
            indent_var = indent_var + 1
            first_switch_instruction = False
            pass_to_be_added = True
        if instruction_name == 'default':
            out_line = []
            if pass_to_be_added:
                out_line = ['    pass']
            indent = indent - 1
            out_line.append("else:")
            indent_var = indent_var + 1
        if instruction_name == 'endswitch':
            switch_value_list.pop()
            out_line = None
            indent_var = -1
            pass_to_be_added = False


        if instruction_name == 'for begin':
            """
            re.search(re_for, "for $potato=1 to 20 step +1", re.IGNORECASE).groups()
            ('$potato=1', '20', '+1')
            """
            initialization = result.groups()[0].strip()
            initialization_variable = initialization.split('=')[0].strip()
            initialization_value = initialization.split('=')[1].strip()
            value_end = result.groups()[1].strip()
            step = result.groups()[2]
            if not step is None: 
                out_line = ["for %s in range(%s, %s, %s):"%(initialization_variable, initialization_value, value_end, step.strip())]
            else:
                out_line = ["for %s in range(%s, %s):"%(initialization_variable, initialization_value, value_end)]
            indent_var = 1
        if instruction_name == 'for end':
            out_line = None
            indent_var = -1

        if instruction_name == 'repeat':
            out_line = ["while True:"]
            indent_var = 1
        if instruction_name == 'until':
            condition = result.groups()[0].strip()
            indent_var = -1
            out_line = ["if %s:"%condition]
            out_line.append("    " + "break")

        if instruction_name == 'exit':
            out_line = ["break"]

        if instruction_name == 'halt':
            out_line = ["assert(False) # halt"]

        if instruction_name == 'lin':
            position = result.groups()[0].strip().lower()
            position = position.replace(" c_dis", ", c_dis")
            position = position.replace(" c_ptp", ", c_ptp")
            position = position.replace(" c_ori", ", c_ori")
            out_line = ["global_defs.robot.lin(%s)"%position]

        if instruction_name == 'ptp':
            position = result.groups()[0].strip().lower()
            position = position.replace(" c_dis", ", c_dis")
            position = position.replace(" c_ptp", ", c_ptp")
            position = position.replace(" c_ori", ", c_ori")
            out_line = ["global_defs.robot.ptp(%s)"%position]

        if instruction_name == 'circ':
            position = result.groups()[0].strip().lower()
            position = position.replace(" c_dis", ", c_dis")
            position = position.replace(" c_ptp", ", c_ptp")
            position = position.replace(" c_ori", ", c_ori")
            out_line = ["global_defs.robot.circ(%s)"%position]

        #it is required to parse variable declaration
        #    variables that are procedure parameters don't need to be declared
        #    multiple variables can be declared in one line
        #    variables can be arrays

        if instruction_name == 'variable declaration':
            """
            re.search(re_variable_decl, "global decl e6POS potato[ 123], cips", re.IGNORECASE).groups()
            ('global ', 'decl ', 'e6POS', 'potato[ 123]', 'cips')
            >>>
            """
            is_global = not result.groups()[0] is None 
            type_name = result.groups()[2]
            variables_names = code_line.split(type_name, maxsplit=1)[1] #result.groups()[3].split(',')
            variables_names = re.split(r" *, *(?!\]|[0-9])", variables_names) #split with a comma not inside an index definition [,]
            variables_names = [x.strip() for x in variables_names]
            out_line = []
            for var in variables_names:
                #if the variable is not declared as parameter, declare it in procedure/function body
                if actual_code_block is None or (not re.sub(array_index, '', var) in actual_code_block.param_names):
                    #check if it is an array
                    array_item_count = re.search(array_index, var)
                    #just for debugging breakpoint
                    if not array_item_count is None:
                        size = array_item_count.groups()[0]
                        var = var.replace(size, '')
                        out_line.append(("global_defs." if is_global else "")+"%s = multi_dimensional_array(%s, %s)"%(var,type_name,size))
                        #[int()]*10
                        #[0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    else:
                        out_line.append(("global_defs." if is_global else "")+"%s = %s()"%(var,type_name))
                else:
                    #if the variable decl is a function parameter it have to be not declared again
                    # and we discard also an end of line comment
                    endofline_comment_to_append = ""

        if instruction_name == 'variable assignment':
            result = re.search(instructions_defs['variable assignment'], code_line, re.IGNORECASE)
            elements = result.groups()
            #(None, 'decl ', 'circ_type', 'def_circ_typ', 'system_constants.base')
            print(elements)
            is_global = not elements[0] is None 
            is_decl = not elements[1] is None
            type_name = elements[2]
            if not type_name is None: 
                type_name = type_name.strip()
                out_line = ["%s = %s(%s)"%(elements[3].strip(), type_name, elements[4].strip())]
            else:
                out_line = ["%s = %s"%(elements[3].strip(), elements[4].strip())]

        if instruction_name == 'struc declaration':
            """
            >>> re.search(re_structure_decl, "STRUC E6POS REAL X, Y, Z, A, B, C, E1, E2, E3, E4, E5, E6, S, T", re.IGNORECASE).groups()
            (None, 'STRUC ', 'E6POS', 'REAL X', 'REAL', 'X', ', T', 'T', None, 'T')
            >>>
            """
            is_global = not result.groups()[0] is None 
            struc_name = result.groups()[2]
            variables_names = code_line.split(struc_name, maxsplit=1)[1]
            variables_names = [x.strip() for x in variables_names.split(',')]
            variables_names_with_types = {}
            type_name = ""
            for x in variables_names:
                #remove multiple spaces
                while "  " in x:
                    x = x.replace("  ", " ")
                if " " in x:
                    #type name
                    type_name, var_name = x.split(" ") 
                    variables_names_with_types[var_name] = type_name
                else:
                    variables_names_with_types[x] = type_name

            #now we create a class
            # class struc_name():
            #   var_name = type_name()

            out_line = ["class %s(generic_struct):"%struc_name]

            #if the variable (struc field) is an array, we replace the type with a multi_dimensional_array 
            for var, type_name in variables_names_with_types.items():
                array_item_count = re.search(array_index, var)
                #just for debugging breakpoint
                if not array_item_count is None:
                    size = array_item_count.groups()[0]
                    var = var.replace(size, '')
                    type_name = "multi_dimensional_array(%s, %s)"%(type_name,size)
                    out_line.append("    %s = %s"%(var,type_name))
                else:
                    out_line.append("    %s = %s()"%(var,type_name))
            
            if is_global:
                out_line.append("global_defs.%s = %s"%(struc_name, struc_name))
        
        if instruction_name == 'enum':
            is_global = not result.groups()[0] is None 
            enum_name = result.groups()[1].strip()
            elements = code_line.split(enum_name)[1]
            element_list = elements.split(',')
            i = 1
            element_list_with_values = []
            for elem in element_list:
                elem = elem.strip()
                element_list_with_values.append("%s=%s"%(elem, i))
                i = i + 1
            out_line = ['%s = enum(%s, "%s", %s)'%(enum_name, 'global_defs' if is_global else 'sys.modules[__name__]', enum_name, ', '.join(element_list_with_values))]
            


        if not out_line is None and len(out_line)>0:
            if '[,]' in out_line[0]:
                out_line[0] = re.sub('\[,\]', '[:]', out_line[0])

            out_line[0] = out_line[0] + endofline_comment_to_append
            fout.writelines( ["    " * indent + x + '\n' for x in out_line] )
        else:
            if len(endofline_comment_to_append)>0:
                fout.write(endofline_comment_to_append + '\n')
        indent = indent + indent_var

    if pass_to_be_added:
        fout.write("    " * indent + 'pass\n')

    fout.close()

            