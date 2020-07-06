import re
import os

# https://www.w3schools.com/python/python_regex.asp

# this "(?:group content)" is a non capturing group, it finds the related group content but discards
re_meta = r"""(?:^ *\&)"""
line_begin = r"""(?:^ *)"""
line_end = r"""(?: *#+.*)?$"""    #here sharp # is used instead of dot comma ; to define a line ending with comment, this is because the dot comma are replaced with sharp before parsing
variable_name = r"""([\$a-z_A-Z]{1}[a-z_A-Z0-9\.]*(?:\[ *[0-9]* *\])?)"""
type_name = r"""([a-z_A-Z]{1}[a-z_A-Z0-9]*)"""
int_or_real_number = r"""((?:\+|-)?[0-9]+(?:\.[0-9]+)?)"""
string = r"""(".*")"""
num_or_string = int_or_real_number + "|" + string
variable_or_int_value = "(%s|%s)"%(int_or_real_number, variable_name)
structure_value = r"""\{( *""" + variable_name + " *(" + num_or_string +")"  + """ *,{0,1})+\}"""
num_or_string_or_struct = num_or_string + "|" + structure_value
_global = "(GLOBAL +)?"
_exit = line_begin + "EXIT" + line_end
_halt = line_begin + "HALT" + line_end

re_binary_number = "'b([0-1]+)'"

re_variable_assignment = line_begin + _global + "(DECL +)?" + variable_name + " +" + variable_name + " *= *([^#]+)" + line_end
types = ['bool', 'char', 'int', 'real', 'frame', 'axis', 'pos', 'e6pos', 'e6axis']
re_variable_decl = line_begin + _global + """(DECL +)?(?:""" + type_name + """) +((?:""" + variable_name + ")(?: *, *" + variable_name + ")*)" + line_end
#re.search(re_variable_decl, "global decl e6POS potato[ 123], cip, ciop", re.IGNORECASE).groups()
#('global ', 'decl ', 'e6POS', 'potato[ 123], cip, ciop', 'potato[ 123]', 'ciop')


#re_variable_decl = line_begin + _global + """(DECL +)?(?:""" + type_name + """) +(?:""" + variable_name + ")" +  "(?: *, *" + variable_name + ")*" + line_end
#re.search(re_variable_decl, "global decl e6POS potato[ 123], cips", re.IGNORECASE).groups()
#('global ', 'decl ', 'e6POS', 'potato[ 123]', 'cips')
 

#STRUC E6POS REAL X, Y, Z, A, B, C, E1, E2, E3, E4, E5, E6, INT S, T
struc_name = variable_name
re_structure_decl = line_begin + _global + "(STRUC +)%s +([^ ,]+) +"%(struc_name,)
"""
>>> re.search(re_structure_decl, "STRUC E6POS REAL X, Y, Z, A, B, C, E1, E2, E3, E4, E5, E6, S, T", re.IGNORECASE).groups()
(None, 'STRUC ', 'E6POS', 'REAL X', 'REAL', 'X', ', T', 'T', None, 'T')
"""

function_name = variable_name
param_decl = variable_name + "(?: *\: *)" + "(IN|OUT)" + "(?: *, *)?"
re_procedure_begin = line_begin + _global + """(DEF +)""" + function_name + """ *\( *(""" + param_decl + """)* *\)""" + line_end
re_procedure_end = line_begin + "END" + line_end
"""
re.search(re_procedure_decl, "GLOBAL DEF potato_cips( CAP:OUT , CIOP:OUT)").groups()
('GLOBAL ', 'DEF ', 'potato_cips', 'CIOP:OUT', 'CIOP', 'OUT')
"""

re_function_begin = line_begin + _global + """(DEFFCT +)""" + "([^ ]+) +" + function_name + """ *\( *(""" + param_decl + """)* *\)""" + line_end
re_function_end = line_begin + "ENDFCT" + line_end
re_function_return = line_begin + "return +" + "(.+)?" + line_end
"""
re.search(re_function_decl,"DEFFCT bool potato_cips( CAP:OUT , CIOP:OUT)").groups()
(None, 'DEFFCT ', 'bool', 'potato_cips', 'CIOP:OUT', 'CIOP', 'OUT')
"""

re_function_call = line_begin + variable_name + " *\( *(.*) *\)" + line_end

re_if_then = line_begin + "if +" + "(.+)" + " +then" + line_end
re_else = line_begin + "else" + line_end
re_endif = line_begin + "endif" + line_end

re_for = line_begin + "for +" + "(.+)" + " +to +(.+)( +step +(.+))? *" + line_end
re_endfor = line_begin + "endfor" + line_end

re_while = line_begin + "while +" + "(.+)" + line_end
re_endwhile = line_begin + "endwhile" + line_end

re_repeat = line_begin + "repeat" + line_end
re_until = line_begin + "until +(.+)" + line_end

re_loop = line_begin + "loop" + line_end
re_endloop = line_begin + "endloop" + line_end

re_interrupt_decl = line_begin + _global + "interrupt +decl +" + int_or_real_number + " +(.+) + do +(.+)" + line_end  
re_interrupt_on = line_begin + "interrupt +on +" + int_or_real_number + line_end
re_interrupt_off = line_begin + "interrupt +off +" + int_or_real_number + line_end

re_trigger_distance = line_begin + "when + distance *= *(0|1) +delay *= *" + int_or_real_number + " +do +(.+)" + line_end
#trigger when distance=0|1 delay=10 do (assignment or function call)

re_trigger_path = line_begin + "when + path *= *" + int_or_real_number + " +delay *= *" + int_or_real_number + " +do +(.+)" + line_end
#trigger when path=0|1 <onstart> delay=10 do (assignment | function call)

#LIN
re_lin = line_begin + "lin +(.+)" + line_end

#PTP
re_ptp = line_begin + "ptp +(.+)" + line_end
#re.search(re_ptp, "ptp banana c_dis", re.IGNORECASE).groups()
#('banana c_dis',)

#CIRC
re_circ = line_begin + "circ +(.+)" + line_end

#switch
#    case
#    default
#endswitch

#defdat name puplic
#enddat
dat_name = variable_name
re_dat_begin = line_begin + """(DEFDAT +)""" + dat_name + "( +PUBLIC)?" + line_end
re_dat_end = line_begin + "ENDDAT" + line_end

#ext funcname(params)

instructions_defs = {
    'meta instruction':     re_meta,
    'exit':                 _exit,
    'halt':                 _halt,
    'dat begin':            re_dat_begin,
    'dat end':              re_dat_end,
    'procedure begin':      re_procedure_begin,
    'procedure end':        re_procedure_end,
    'function begin':       re_function_begin,
    'function end':         re_function_end,
    'function return':      re_function_return,
    'lin':                  re_lin,
    'ptp':                  re_ptp,
    'circ':                 re_circ,
    'struc declaration':    re_structure_decl,
    'if begin':             re_if_then,
    'else':                 re_else,
    'if end':               re_endif,
    'for begin':            re_for,
    'for end':              re_endfor,
    'while begin':          re_while,
    'while end':            re_endwhile,
    'repeat':               re_repeat,
    'until':                re_until,
    'loop begin':           re_loop,
    'loop end':             re_endloop,
    'interrupt decl':       re_interrupt_decl,
    'interrupt on':         re_interrupt_on,
    'interrupt off':        re_interrupt_off,
    'trigger distance':     re_trigger_distance,
    'trigger path':         re_trigger_path,
    'variable assignment':  re_variable_assignment,
    'variable declaration': re_variable_decl,
    'function call':        re_function_call
}

simple_instructions_to_replace = {
    r'\$':  'system_vars.',
    '#':    'system_constants.',
    ';':    '#',
    '<>':   '!=',
    'B_EXOR':  '^',
    'B_AND':   '&',
    'B_OR':    '|',
    'EXOR':    '^',
    'NOT':  'not',
    'AND':  'and',
    'OR':   'or',
}


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


def parse(filename_in, filename_out, write_mode):
    fin = open(filename_in, "r")
    lines = fin.readlines()
    fin.close()

    fout = open(filename_out, write_mode)
    fout.write("from global_defs import *\n")

    code_block_dictionary = {}
    actual_code_block = None

    indent = 0
    indent_var = 0
    out_line = []
    for code_line in lines:

        #this is only for debugging for breackpoint at certain instruction
        if "INT DEF_OV_PRO=100" in code_line:
            print("")

        #spaces are removed to keep the indentation consistent in all the code, as required by Python
        code_line = code_line.strip()
        #since KRL is case insensitive, and Python is case sensitive, the code is transformed to lower making it all the variable names equal in the code
        code_line = code_line.lower()

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
                    fields_and_values = re.search('[:\(\{\=,)]{1}([^:,\(\{="\)\} ]+) ([^\)=\},; ]+)', code_line)
                    if fields_and_values is None:
                        break
                    field_and_value = code_line[fields_and_values.span()[0]+1:fields_and_values.span()[1]]
                    #replace the first occurrence of the found field, with the field replacing the first space occurrence with equal = sign 
                    code_line = code_line.replace(field_and_value, field_and_value.replace(' ', '=', 1), 1)
                """
                prepend = code_line[:code_line.index('(')+1]
                params = code_line[code_line.index('(')+1:code_line.rindex(')')]
                append = code_line[code_line.rindex(')')-1:]
                params = params.split(",")
                params_reworked = []
                for param in params:
                    reg = r"^ *([_\-\+\$a-zA-Z0-9]+) +"
                    param = param.strip()
                    items = re.search(reg, param)
                    if items is None:
                        params_reworked.append(param)
                        continue
                    items = items.groups()
                    param_name = items[0]
                    params_reworked.append(param.replace(param_name, param_name + " ="))
                """
                """
                >>> re.search(r"\{ *([_\-\+\$a-zA-Z0-9]+) *:", "{E6POS: x 1, y 2 ,z 0, f { E6AXIS : a1 10, a2 1, a3 40 }}").groups()
                ('E6POS',)
                """
                #code_line = prepend + ",".join(params_reworked) + append



        #common keywords are replaced as per Python spelling, i.e. TRUE becomes True
        for k,v in simple_instructions_to_replace.items():
            code_line = re.sub(k, v, code_line, flags=re.IGNORECASE)
        out_line = [code_line]
        indent_var = 0

        result = None 
        instruction_name = ""
        for k,v in instructions_defs.items():
            result = re.search(v, code_line, re.IGNORECASE) 
            if not result is None:
                instruction_name = k
                break

        if instruction_name == 'meta instruction':
            continue
        
        if instruction_name == 'dat begin':
            continue

        if instruction_name == 'dat end':
            continue

        if instruction_name == 'procedure begin':
            param_list = code_line.split('(')[1].split(')')[0].split(',')
            param_names = [x.split(':')[0].strip() for x in param_list]
            procedure_name = result.groups()[2]
            out_line = ["def " + procedure_name + "(" + ", ".join(param_names) + "):"]
            indent_var = 1
            actual_code_block = Procedure(procedure_name, param_names, [], [])
            code_block_dictionary[procedure_name] = actual_code_block
        if instruction_name == 'procedure end':
            indent_var = -1
            out_line = None

        if instruction_name == 'function begin':
            param_list = code_line.split('(')[1].split(')')[0].split(',')
            param_names = [x.split(':')[0].strip() for x in param_list]
            return_value_type_name = result.groups()[2]
            out_line = ["def " + result.groups()[3] + "(" + ", ".join(param_names) + "): #function returns %s"%return_value_type_name]
            indent_var = 1

            """
            re.search(re_function_decl,"DEFFCT bool potato_cips( CAP:OUT , CIOP:OUT)").groups()
            (None, 'DEFFCT ', 'bool', 'potato_cips', 'CIOP:OUT', 'CIOP', 'OUT')
            """
            actual_code_block = Function( return_value_type_name,procedure_name, param_names, [], [])
            code_block_dictionary[procedure_name] = actual_code_block
        if instruction_name == 'function end':
            indent_var = -1
            out_line = None
        if instruction_name == 'function return':
            value = result.groups()[0]
            out_line = ["return" if value is None else ("return " + value)]

        if instruction_name == 'if begin':
            """
            re.search(re_if_than, 'if VARSTATE("Zmultiplier")==#INITIALIZED then', re.IGNORECASE).groups()
            ('VARSTATE("Zmultiplier")==#INITIALIZED',)
            """
            condition = result.groups()[0].strip()
            out_line = ["if " + condition + ":"]
            indent_var = 1
        if instruction_name == 'else':
            indent = indent - 1
            out_line = ["else:"]
            indent_var = 1
        if instruction_name == 'if end':
            out_line = None
            indent_var = -1

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
            out_line = ["lin(%s)"%position]

        if instruction_name == 'ptp':
            position = result.groups()[0].strip().lower()
            position = position.replace(" c_dis", ", c_dis")
            position = position.replace(" c_ptp", ", c_ptp")
            out_line = ["ptp(%s)"%position]

        if instruction_name == 'circ':
            position = result.groups()[0].strip().lower()
            position = position.replace(" c_dis", ", c_dis")
            position = position.replace(" c_ptp", ", c_ptp")
            out_line = ["circ(%s)"%position]

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
            variables_names = result.groups()[3].split(',')
            variables_names = [x.strip() for x in variables_names]
            out_line = []
            for var in variables_names:
                #if the variable is not declared as parameter, declare it in procedure/function body
                if actual_code_block is None or (not var in actual_code_block.param_names):
                    #check if it is an array
                    array_item_count = re.search('\[ *([0-9]+) *\]', var)
                    if not array_item_count is None:
                        out_line.append("%s = [%s()]*%s"%(var,type_name,array_item_count.groups()[0]))
                        #[int()]*10
                        #[0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    else:
                        out_line.append("%s = %s()"%(var,type_name))

        if instruction_name == 'variable assignment':
            elements = result.groups()
            #(None, 'decl ', 'circ_type', 'def_circ_typ', 'system_constants.base')
            print(elements)
            out_line = ["%s = %s(%s)"%(elements[3].strip(), elements[2].strip(), elements[4].strip())]

        if instruction_name == 'struc declaration':
            """
            >>> re.search(re_structure_decl, "STRUC E6POS REAL X, Y, Z, A, B, C, E1, E2, E3, E4, E5, E6, S, T", re.IGNORECASE).groups()
            (None, 'STRUC ', 'E6POS', 'REAL X', 'REAL', 'X', ', T', 'T', None, 'T')
            >>>
            """
            is_global = not result.groups()[0] is None 
            struc_name = result.groups()[2]
            #this should remove end of line comment
            code_line = re.sub(line_end, "", code_line)
            variables_names = code_line.split(struc_name)[1]
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

            out_line = ["class %s():"%struc_name]
            out_line.extend(["    %s = %s()"%(k,v) for k,v in variables_names_with_types.items()])
        
        if not out_line is None:
            fout.writelines( ["    " * indent + x + '\n' for x in out_line] )
        indent = indent + indent_var

    fout.close()

            