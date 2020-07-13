# this "(?:group content)" is a non capturing group, it finds the related group content but discards
def c(s): #capture
    return "(%s)"%s      
def nc(s): #non capture
    return "(?:%s)"%s   
def d(s): #discard
    return "(?!%s)"%s    

    

line_begin = r"(?:^ *)"
line_end = r"(?: *#+.*)?$"    #here sharp # is used instead of dot comma ; to define a line ending with comment, this is because the dot comma are replaced with sharp before parsing
re_comment = line_begin + line_end
index_3d = "\[ *[0-9]* *(?:, *[0-9]* *){0,2}\]"
variable_name = c(r"[\$a-z_A-Z]{1}[a-z_A-Z0-9\.]* *" + nc(index_3d) + "?")
dat_name = c(r"[\$a-z_A-Z]{1}[a-z_A-Z0-9\.]* *")
function_name = dat_name
struct_name = dat_name
global_def = "(GLOBAL +)?"
parameters_declaration = variable_name + "(?: *\: *)" + "(IN|OUT)" + "(?: *, *)?"
int_or_real_number = r"((?:\+|-)?[0-9]+(?:\.[0-9]+)?)"


def a_line_containing(keyword):
    return line_begin + keyword + line_end


krl_tokes_to_python = {
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
    endofline_comment_to_append = code_line[endofline_comment_to_append[0]:endofline_comment_to_append[1]]
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

    return (code_line, endofline_comment_to_append)


def replace_geometric_operator(code_line):
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
    return code_line


def check_regex_match(code_line, regex_dict_instruction_name_value):
    match = None
    if re.search(re_comment, code_line) is None:
        for k, v in regex_dict_instruction_name_value.items():
            math = re.search(v, code_line, re.IGNORECASE) 
            if not match is None:
                instruction_name = k
                match = match.groups()
                break
    return instruction_name, match

def indent_lines(list_of_strings, indent):
    ret = ['    '*indent + x for x in list_of_strings]
    return ret


class KRLGenericParser():
    permissible_instructions_dictionary = None
    def __init__(self, permissible_instructions_dictionary):
        self.permissible_instructions_dictionary = permissible_instructions_dictionary

    def parse(self, file_lines):
        """ Parses the file lines up to the procedure end
        """
        translation_result = [] #here are stored the results of instructions translations from krl to python 
        while len(file_lines):
            code_line_original = file_lines.pop()
            
            code_line, endofline_comment_to_append = generic_regexes.prepare_instruction_for_parsing(code_line_original)
            code_line = generic_regexes.replace_geometric_operator(code_line)
            instruction_name, match_groups = generic_regexes.check_regex_match(code_line, permissible_instructions_dictionary)
            
            #here is called the specific parser
            translation_result_tmp, file_lines = self.parse_single_instruction(code_line_original, code_line, instruction_name, match_groups, file_lines)

            if len(translation_result_tmp)>0:
                if '[,]' in translation_result_tmp[0]:
                    translation_result_tmp[0] = re.sub('\[,\]', '[:]', translation_result_tmp[0])

                translation_result_tmp[0] = translation_result_tmp[0] + endofline_comment_to_append
                translation_result.append(*translation_result_tmp)
            else:
                if len(endofline_comment_to_append)>0:
                    translation_result_tmp.append(endofline_comment_to_append + '\n')

        return translation_result, file_lines
