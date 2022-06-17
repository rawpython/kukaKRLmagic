import re

# this "(?:group content)" is a non capturing group, it finds the related group content but discards
def c(s): #capture
    return "(%s)"%s      
def nc(s): #non capture
    return "(?:%s)"%s   
def d(s): #discard
    return "(?!%s)"%s    
    

line_begin = r"(?:^ *)"
line_end = r"(?: *(?:;+.*)?)$"    #here sharp # is used instead of dot comma ; to define a line ending with comment, this is because the dot comma are replaced with sharp before parsing
re_comment = line_begin + line_end
#index_3d = "\[ *[0-9]* *(?:, *[0-9]* *){0,2}\]"
#index_value = "(?:[0-9]*|[\$a-z_A-Z]{1}[a-z_A-Z0-9\.]*)"
index_value = "(?:[^,;\{\}]*)"
index_3d = "\[ *%s *(?:, *%s *){0,2}\]"%(index_value, index_value)
subfield = r"\.[\$a-z_A-Z]{1}[a-z_A-Z0-9\.]*"
variable_name = c(r"[\$a-z_A-Z]{1}[a-z_A-Z0-9\.]* *" + nc(index_3d) + "?" + nc(subfield) + "?")
dat_name = c(r"[\$a-z_A-Z]{1}[a-z_A-Z0-9\.]* *")
function_name = dat_name
struct_name = dat_name
global_def = "(GLOBAL +)?"
parameters_declaration = variable_name + "(?: *\: *)" + "(IN|OUT)" + "(?: *, *)?"
int_or_real_number = r"((?:\+|-)?[0-9]+(?:\.[0-9]+)?)"
re_string = '((?!r)"[^"]+")' #KRL strings can contain special sequences for python like %s, and so it is required to prepend r""
re_string_python = '(r"[^"]+")'
re_binary_number = "'b([0-1]+)'"

re_not = nc("[ \)]") + c("not") + nc("[ \(]")
re_and = nc("[ \)]") + c("and") + nc("[ \(]")
re_or = nc("[ \)]") + c("or") + nc("[ \(]")

enum_value = '(#[^ ,\[\]\(\)\{\}\+\-\*/\'\"]+)'


def a_line_containing(keyword):
    return line_begin + keyword + line_end

variable_or_function_call_with_params = nc(variable_name + " *(?:\( *[^\(\):]* *\))?")
re_geometric_addition_operator = c(variable_or_function_call_with_params + ':' + variable_or_function_call_with_params) #r"([^:=,]+:[^:,]+)"

krl_tokes_to_python = {
    r'\$IN':  '$inputs',
    r'\$OUT':  '$outputs',
    r'\$':  'DOLLAR__',
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


def prepare_instruction_for_parsing(code_line):
    """ returns reworked code_line and endofline_comment in a tuple
    """
    #spaces are removed to keep the indentation consistent in all the code, as required by Python
    code_line = code_line.strip()
    #since KRL is case insensitive, and Python is case sensitive, the code is transformed to lower making it all the variable names equal in the code
    code_line = code_line.lower()

    #common keywords are replaced as per Python spelling, i.e. TRUE becomes True
    for k,v in krl_tokes_to_python.items():
        code_line = re.sub(k, v, code_line, flags=re.IGNORECASE)
    
    #this should remove end of line comment
    endofline_comment_to_append = re.search(line_end, code_line).span()
    endofline_comment_to_append = code_line[endofline_comment_to_append[0]:endofline_comment_to_append[1]].strip()
    code_line = code_line.replace(endofline_comment_to_append, "")

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
            #code_line = code_line.replace('}', ')')
            #code_line = code_line.replace('{', 'generic_struct(')
            
            #putting = after field name
            while True:
                fields_and_values = re.search('[:\(\{\=,)]{1} *([^:,\(\{="\)\} ]+) ([^\)=\},; ]+)', code_line)
                if fields_and_values is None:
                    break
                field_and_value = code_line[fields_and_values.span()[0]+1:fields_and_values.span()[1]]
                field_and_value = field_and_value.strip()
                #replace the first occurrence of the found field, with the field replacing the first space occurrence with equal = sign 
                code_line = code_line.replace(field_and_value,"." + field_and_value.replace(' ', '=', 1), 1)

    #replace strings "..." with r"..." to skip python special sequences
    code_line_new = ''
    while True:
        r = re.search(re_string, code_line) 
        if r is None:
            break
        code_line_new = code_line_new + code_line[0:r.span()[0]]
        code_line_new = code_line_new + code_line[r.span()[0]:r.span()[1]]
        code_line = code_line[r.span()[1]:]
    code_line = code_line_new + code_line

    #replace binary numbers
    result = re.search(re_binary_number,code_line)
    if not result is None:
        value = result.groups()[0]
        code_line = code_line.replace(code_line[result.span()[0]:result.span()[1]], "0b%s"%value) 

    while True:
        result = re.search(re_not,code_line)
        if result is None:
            break
        value = result.groups()[0]
        code_line = code_line.replace(code_line[result.span()[0]+1:result.span()[1]-1], "!") 
    
    while True:
        result = re.search(re_and,code_line)
        if result is None:
            break
        value = result.groups()[0]
        code_line = code_line.replace(code_line[result.span()[0]+1:result.span()[1]-1], "&&") 

    while True:
        result = re.search(re_or,code_line)
        if result is None:
            break
        value = result.groups()[0]
        code_line = code_line.replace(code_line[result.span()[0]+1:result.span()[1]-1], "||") 
    
    return (code_line, endofline_comment_to_append)


def replace_geometric_operator(code_line):
    #replacing geometric addition operator :
    while True:
        geoadd = re.search(re_geometric_addition_operator, code_line)
        is_not_a_string = (re.search(re_string_python, code_line) == None)
        if (not geoadd is None) and is_not_a_string:
            span = geoadd.span()
            #operands = geoadd.groups()[0]
            #operands = operands.split(':')
            to_be_replaced = code_line[span[0]:span[1]]
            replacement = to_be_replaced.replace(':', '+')
            #code_line = code_line.replace(to_be_replaced, "_geometric_addition_operator(%s, %s)"%(operands[0], operands[1]))
            code_line = code_line.replace(to_be_replaced, replacement)
        else:
            break
    return code_line


def replace_enum_value(code_line):
    while True:
        enum_value_match = re.search(enum_value, code_line)
        if (not enum_value_match is None):
            span = enum_value_match.span()
            enum_value_match_string = enum_value_match.groups()[0]
            #to_be_replaced = code_line[span[0]:span[1]]
            code_line = code_line.replace(enum_value_match_string, '\'%s\''%(enum_value_match_string.replace('#','')))
        else:
            break
    return code_line


def check_regex_match(code_line, regex_dict_instruction_name_value):
    match = None
    instruction_name = ''
    if re.search(re_comment, code_line) is None:
        for k, v in regex_dict_instruction_name_value.items():
            match = re.search(v, code_line, re.IGNORECASE) 
            if not match is None:
                instruction_name = k
                match = match.groups()
                break
    return instruction_name, match

def indent_lines(list_of_strings, indent):
    ret = ['    '*indent + x for x in list_of_strings]
    return ret

def split_varname_index(_var): #given potato[3,2] it returns 'potato','[3,2]',True
    var = _var
    size = ''
    is_array = False
    ret = re.search(c(index_3d), var)
    subindex = ''
    if not ret is None:
        size = ret.groups()[0]
        #var = var.replace(size, '')
        _var = var
        var = _var.split(size)[0]
        try:
            subindex = _var.split(size)[1]
        except:
            pass
        is_array = True
    return var, size, subindex, is_array

def var_without_pointed_field(_var): #given potato.weight it returns 'potato', 'weight', is_pointed
    var = _var
    field = ''
    is_pointed = False
    if '.' in var:
        is_pointed = True
        var, field = var.split('.', maxsplit = 1)
    return var, field, is_pointed
