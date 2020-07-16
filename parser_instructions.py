import re
import os
import generic_regexes
from remi import gui
import collections

"""
    This parses dat and src files
        analyzed instructions
"""

instructions_defs = {
    'dat begin':            generic_regexes.line_begin + "(DEFDAT +)" + generic_regexes.dat_name + "( +PUBLIC)?" + generic_regexes.line_end,       #creates a dat parser
    'dat end':              generic_regexes.a_line_containing("ENDDAT"),
    'procedure begin':      generic_regexes.line_begin + generic_regexes.global_def + "(DEF +)" + generic_regexes.function_name + " *\( *(" + generic_regexes.parameters_declaration + ")* *\)" + generic_regexes.line_end, #creates a procedure parser
    'function begin':       generic_regexes.line_begin + generic_regexes.global_def + "(DEFFCT +)" + "([^ ]+) +" + generic_regexes.function_name + " *\( *(" + generic_regexes.parameters_declaration + ")* *\)" + generic_regexes.line_end,  #creates a function parser

    'meta instruction':     r"(?:^ *\& *)",
    'procedure end':        generic_regexes.a_line_containing("END"),
    'function end':         generic_regexes.a_line_containing("ENDFCT"),
    'function return':      generic_regexes.a_line_containing("RETURN" + "(?: +(.+))?"),

    'exit':                 generic_regexes.a_line_containing("EXIT"),
    'halt':                 generic_regexes.a_line_containing("HALT"),

    'switch':               generic_regexes.line_begin + "SWITCH *(.*)",
    'case':                 generic_regexes.line_begin + "CASE +(.*)",
    'default':              generic_regexes.a_line_containing("DEFAULT"),
    'endswitch':            generic_regexes.a_line_containing("ENDSWITCH"),

    'lin':                  generic_regexes.a_line_containing("LIN(?:_rel)? +(.+)"),
    'ptp':                  generic_regexes.a_line_containing("PTP +(.+)"),
    'circ':                 generic_regexes.a_line_containing("CIRC +(.+)"),

    'struc declaration':    generic_regexes.line_begin + generic_regexes.global_def + "(STRUC +)%s +([^ ,]+) +"%(generic_regexes.struct_name,),

    'if begin':             generic_regexes.a_line_containing("IF +" + "(.+)" + " +THEN"),
    'else':                 generic_regexes.a_line_containing("ELSE"),
    'if end':               generic_regexes.a_line_containing("ENDIF"),

    'for begin':            generic_regexes.a_line_containing("FOR +" + "(.+)" + " +TO +((?:(?!STEP).)+)(?: +STEP +(.+))? *"),
    'for end':              generic_regexes.a_line_containing("ENDFOR"),

    'while begin':          generic_regexes.a_line_containing("WHILE +" + "(.+)"),
    'while end':            generic_regexes.a_line_containing("ENDWHILE"),

    'repeat':               generic_regexes.a_line_containing("REPEAT"),
    'until':                generic_regexes.a_line_containing("until +(.+)"),

    'loop begin':           generic_regexes.a_line_containing("LOOP"),
    'loop end':             generic_regexes.a_line_containing("ENDLOOP"),

    'interrupt decl':       generic_regexes.a_line_containing( generic_regexes.global_def + "INTERRUPT +DECL +" + generic_regexes.int_or_real_number + " +WHEN +(.+) +DO +(.+)" ),
    'interrupt on':         generic_regexes.a_line_containing("INTERRUPT +ON +" + generic_regexes.int_or_real_number ),
    'interrupt off':        generic_regexes.a_line_containing("INTERRUPT +OFF +" + generic_regexes.int_or_real_number ),

    'trigger distance':     generic_regexes.a_line_containing( "TRIGGER +WHEN +DISTANCE *= *(0|1) +DELAY *= *" + generic_regexes.int_or_real_number + " +DO +(.+)" ),
    'trigger path':         generic_regexes.a_line_containing( "TRIGGER +WHEN +PATH *= *(.+) +DELAY *= *" + generic_regexes.int_or_real_number + " +DO +(.+)" ),

    'variable assignment':  generic_regexes.a_line_containing( generic_regexes.global_def + "(DECL +)?(?:" + generic_regexes.variable_name + " +)?" + generic_regexes.variable_name + " *= *([^;]+)" ),
    'variable declaration': generic_regexes.a_line_containing( generic_regexes.global_def + "(DECL +)?([^ =\(]+) +(([^ =\(]+"+generic_regexes.c(generic_regexes.index_3d)+"?)( *, *[^ =]+" + generic_regexes.c(generic_regexes.index_3d) + "?)*)" ),

    'function call':        generic_regexes.a_line_containing( generic_regexes.variable_name + " *\( *(.*) *\)" ),

    'enum definition':                 generic_regexes.a_line_containing( generic_regexes.global_def + "ENUM +([^ ]+) +.*" ),

    'wait sec':             generic_regexes.a_line_containing( "WAIT +SEC +" + generic_regexes.int_or_real_number ),

    'wait for':             generic_regexes.a_line_containing( "WAIT +FOR +" + "([^;]+)" ),

    'ext':                  generic_regexes.line_begin + "EXTP? +([^ \(]+) *\(",
    'extfct':               generic_regexes.line_begin + "EXTFCTP? +([^ ]+) +([^ \(]+) *\(",

    'signal decl':          generic_regexes.a_line_containing( generic_regexes.global_def + r"SIGNAL +([^ ]+) +((?:[^ \[]+)(?:\[ *[0-9]* *\])?)(?: +TO +((?:[^ \[]+)(?:\[ *[0-9]* *\])?))?" ),

    'continue':             generic_regexes.a_line_containing( "CONTINUE" ), #in KRL Prevention of advance run stops.
}


class KRLGenericParser(gui.Container):
    stop_statement_found = False
    permissible_instructions_dictionary = None
    indent_comments = True
    def __init__(self, permissible_instructions_dictionary):
        self.permissible_instructions_dictionary = collections.OrderedDict(permissible_instructions_dictionary)
        standard_permissible_instructions = ['function return','meta instruction','halt','switch','lin','ptp','circ','if begin','for begin','while begin','repeat','loop begin','interrupt decl','interrupt on','interrupt off','trigger distance','trigger path','variable assignment','function call','wait sec','wait for', 'ext', 'extfct', 'signal decl','continue',]
        self.permissible_instructions_dictionary.update({k:v for k,v in instructions_defs.items() if k in standard_permissible_instructions})

        gui.Container.__init__(self)

    def get_parent_function(self):
        if issubclass(type(self), KRLProcedureParser) or issubclass(type(self), KRLFunctionParser):
            return self

        if not self.get_parent() is None:
            if issubclass(type(self.get_parent()), KRLGenericParser):
                return self.get_parent().get_parent_function()
        
        return None

    def get_parent_module_file(self):
        import parser_module
        if self.__class__ == parser_module.KRLModuleDatFileParser or self.__class__ == parser_module.KRLModuleSrcFileParser:
            return self

        if not self.get_parent() is None:
            return self.get_parent().get_parent_module_file()
        
        return None

    def parse(self, file_lines):
        """ Parses the file lines up to the procedure end
        """
        translation_result = [] #here are stored the results of instructions translations from krl to python 
        while len(file_lines) and not self.stop_statement_found:
            code_line_original = file_lines.pop(0)
            
            code_line, endofline_comment_to_append = generic_regexes.prepare_instruction_for_parsing(code_line_original)
            code_line = generic_regexes.replace_enum_value(code_line)

            instruction_name, match_groups = generic_regexes.check_regex_match(code_line, self.permissible_instructions_dictionary)
            
            #here is called the specific parser
            translation_result_tmp, file_lines = self.parse_single_instruction(code_line_original, code_line, instruction_name, match_groups, file_lines)

            if endofline_comment_to_append.startswith(';'):
                endofline_comment_to_append = '#' + endofline_comment_to_append

            if len(translation_result_tmp)>0:
                if '[,]' in translation_result_tmp[0]:
                    translation_result_tmp[0] = re.sub('\[,\]', '[:]', translation_result_tmp[0])

                translation_result_tmp[0] = translation_result_tmp[0] + endofline_comment_to_append
                translation_result.extend(translation_result_tmp)
            else:
                if len(endofline_comment_to_append)>0:
                    translation_result.append(('    ' if self.indent_comments else '') + endofline_comment_to_append + '\n')

        return translation_result, file_lines

    def parse_single_instruction(self, code_line_original, code_line, instruction_name, match_groups, file_lines):
        translation_result_tmp = []
        if 'P00_subm' in code_line_original:
            print("brakepoint")
        if not instruction_name in ['ext', 'extfct']:
            code_line = generic_regexes.replace_geometric_operator(code_line)

        if instruction_name == 'meta instruction':
            return translation_result_tmp, file_lines

        if instruction_name == 'halt':
            translation_result_tmp.append("assert(False) # halt")

        if instruction_name == 'switch':
            value_to_switch = match_groups[0]
            node = KRLStatementSwitch( value_to_switch )
            self.append(node)
            _translation_result_tmp, file_lines = node.parse(file_lines)
            if len(_translation_result_tmp):
                translation_result_tmp.extend(_translation_result_tmp)

        if instruction_name == 'lin':
            position = match_groups[0].strip().lower()
            position = position.replace(" c_dis", ", c_dis")
            position = position.replace(" c_ptp", ", c_ptp")
            position = position.replace(" c_ori", ", c_ori")
            translation_result_tmp.append("global_defs.robot.lin(%s)"%position)

        if instruction_name == 'ptp':
            position = match_groups[0].strip().lower()
            position = position.replace(" c_dis", ", c_dis")
            position = position.replace(" c_ptp", ", c_ptp")
            position = position.replace(" c_ori", ", c_ori")
            translation_result_tmp.append("global_defs.robot.ptp(%s)"%position)

        if instruction_name == 'circ':
            position = match_groups[0].strip().lower()
            position = position.replace(" c_dis", ", c_dis")
            position = position.replace(" c_ptp", ", c_ptp")
            position = position.replace(" c_ori", ", c_ori")
            translation_result_tmp.append("global_defs.robot.circ(%s)"%position)

        if instruction_name == 'struc declaration':
            is_global = not match_groups[0] is None 
            struc_name = match_groups[2]
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

            translation_result_tmp.append("class %s(generic_struct):"%struc_name)

            #if the variable (struc field) is an array, we replace the type with a multi_dimensional_array 
            for var, type_name in variables_names_with_types.items():
                array_item_count = re.search(generic_regexes.c(generic_regexes.index_3d), var)
                #just for debugging breakpoint
                if not array_item_count is None:
                    size = array_item_count.groups()[0]
                    var = var.replace(size, '')
                    type_name = "multi_dimensional_array(%s, %s)"%(type_name,size)
                    translation_result_tmp.append("    %s = %s"%(var,type_name))
                else:
                    translation_result_tmp.append("    %s = %s()"%(var,type_name))
            
            if is_global:
                translation_result_tmp.append("global_defs.%s = %s"%(struc_name, struc_name))
        
        if instruction_name == 'if begin':
            condition = match_groups[0].strip()
            translation_result_tmp.append("if " + condition + ":")
            node = KRLStatementIf(condition)
            self.append(node)
            _translation_result_tmp, file_lines = node.parse(file_lines)
            if len(_translation_result_tmp):
                translation_result_tmp.extend(_translation_result_tmp)

        if instruction_name == 'for begin':
            """
            re.search(re_for, "for $potato=1 to 20 step +1", re.IGNORECASE).groups()
            ('$potato=1', '20', '+1')
            """
            initialization = match_groups[0].strip()
            initialization_variable = initialization.split('=')[0].strip()
            initialization_value = initialization.split('=')[1].strip()
            value_end = match_groups[1].strip()
            step = match_groups[2]

            if not step is None: 
                translation_result_tmp.append("for %s in range(%s, %s, %s):"%(initialization_variable, initialization_value, value_end, step.strip()))
            else:
                translation_result_tmp.append("for %s in range(%s, %s):"%(initialization_variable, initialization_value, value_end))

            node = KRLStatementFor(initialization_variable, initialization_value, value_end, step)
            self.append(node)
            _translation_result_tmp, file_lines = node.parse(file_lines)
            if len(_translation_result_tmp):
                translation_result_tmp.extend(_translation_result_tmp)

        
        if instruction_name == 'while begin':
            condition = match_groups[0].strip()
            translation_result_tmp.append("while " + condition + ":")
            node = KRLStatementWhile(condition)
            self.append(node)
            _translation_result_tmp, file_lines = node.parse(file_lines)
            if len(_translation_result_tmp):
                translation_result_tmp.extend(_translation_result_tmp)

        if instruction_name == 'repeat':
            translation_result_tmp.append("while True:")
            node = KRLStatementRepeatUntil()
            self.append(node)
            _translation_result_tmp, file_lines = node.parse(file_lines)
            if len(_translation_result_tmp):
                translation_result_tmp.extend(_translation_result_tmp)

        if instruction_name == 'loop begin':
            translation_result_tmp.append("while True:")
            node = KRLStatementLoop(condition)
            self.append(node)
            _translation_result_tmp, file_lines = node.parse(file_lines)
            if len(_translation_result_tmp):
                translation_result_tmp.extend(_translation_result_tmp)

        if instruction_name == 'interrupt decl':
            interrupt_declaration_template = """
def %(interrupt_name)s():
    if interrupt_flags[%(interrupt_number)s]:
        if %(condition)s:
            %(instruction)s
interrupts[%(interrupt_number)s] = %(interrupt_name)s"""
            is_global, interrupt_number, condition, instruction = match_groups
            is_global = not is_global is None 
            interrupt_declaration = interrupt_declaration_template%{'interrupt_number':interrupt_number, 'condition':condition, 'instruction':instruction, 'interrupt_name':'_interrupt%s'%interrupt_number}
            translation_result_tmp.extend(interrupt_declaration.split('\n'))
            #translation_result_tmp.append('interrupts[%s] = """if %s:%s""" '%(interrupt_number, condition, instruction)] #to be evaluated cyclically with eval
        if instruction_name == 'interrupt on':
            interrupt_number = match_groups[0]
            translation_result_tmp.append('interrupt_flags[%s] = True'%interrupt_number)
        if instruction_name == 'interrupt off':
            interrupt_number = match_groups[0]
            translation_result_tmp.append('interrupt_flags[%s] = False'%interrupt_number)
        
        if instruction_name == 'trigger distance':
            trigger_distance_declaration_template = """
def %(trigger_name)s():
    %(instruction)s
threading.Timer(%(delay)s, %(trigger_name)s).start()"""

            distance, delay, instruction = match_groups
            trigger_func_name = 'trigger_func%s'%uuid
            uuid = uuid + 1
            trigger_declaration = trigger_distance_declaration_template%{'trigger_name':trigger_func_name, 'instruction':instruction, 'delay':delay}
            translation_result_tmp.extend(trigger_declaration.split('\n'))
            
        if instruction_name == 'trigger path':
            trigger_path_declaration_template = """
#this should be scheduled at path=%(path)s, to be implemented
def %(trigger_name)s():
    %(instruction)s
threading.Timer(%(delay)s, %(trigger_name)s).start()"""

            path, delay, instruction = match_groups
            trigger_func_name = 'trigger_func%s'%uuid
            uuid = uuid + 1
            trigger_declaration = trigger_path_declaration_template%{'trigger_name':trigger_func_name, 'instruction':instruction, 'delay':delay, 'path':path}
            translation_result_tmp.extend(trigger_declaration.split('\n'))

        if instruction_name == 'variable declaration':
            """
            re.search(re_variable_decl, "global decl e6POS potato[ 123], cips", re.IGNORECASE).groups()
            ('global ', 'decl ', 'e6POS', 'potato[ 123]', 'cips')
            >>>
            """
            is_global = not match_groups[0] is None 
            type_name = match_groups[2]
            variables_names = code_line.split(type_name, maxsplit=1)[1] #match_groups[3].split(',')
            variables_names = re.split(r" *, *(?!\]|[0-9])", variables_names) #split with a comma not inside an index definition [,]
            variables_names = [x.strip() for x in variables_names]

            if type_name in ['int', ]:
                type_name = 'krl_' + type_name

            for var in variables_names:
                #if the variable is not declared as parameter, declare it in procedure/function body
                #if actual_code_block is None or (not re.sub(generic_regexes.index_3d, '', var) in actual_code_block.param_names):
                parent_function = self.get_parent_function()
                if parent_function is None or (not re.sub(generic_regexes.c(generic_regexes.index_3d), '', var) in parent_function.param_names):
                    #check if it is an array
                    array_item_count = re.search(generic_regexes.c(generic_regexes.index_3d), var)
                    #just for debugging breakpoint
                    if not array_item_count is None:
                        size = array_item_count.groups()[0]
                        var = var.replace(size, '')
                        translation_result_tmp.append(("global_defs." if is_global else "")+"%s = multi_dimensional_array(%s, %s)"%(var,type_name,size))
                        #[int()]*10
                        #[0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    else:
                        translation_result_tmp.append(("global_defs." if is_global else "")+"%s = %s()"%(var,type_name))
                else:
                    #if the variable decl is a function parameter it have to be not declared again
                    # and we discard also an end of line comment
                    if not parent_function is None:
                        parent_function.pass_to_be_added = True
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
                translation_result_tmp.append("%s = %s(%s)"%(elements[3].strip(), type_name, elements[4].strip()))
            else:
                var = elements[3].strip()
                array_item_count = re.search(generic_regexes.c(generic_regexes.index_3d), var)
                #just for debugging breakpoint
                if not array_item_count is None:
                    size = array_item_count.groups()[0]
                    var = var.replace(size, '')
                    translation_result_tmp.append("globals()['%s']%s = %s"%(var, size, elements[4].strip()))
                else:
                    translation_result_tmp.append("globals()['%s'] = %s"%(var, elements[4].strip()))


        if instruction_name == 'function call':
            self.get_parent_function().calling_list.append(match_groups[0])
            translation_result_tmp.append(code_line.strip())

        if instruction_name == 'enum definition':
            is_global = not match_groups[0] is None 
            enum_name = match_groups[1].strip()
            elements = code_line.split(enum_name)[1]
            element_list = elements.split(',')
            i = 1
            element_list_with_values = []
            for elem in element_list:
                elem = elem.strip()
                element_list_with_values.append("'%s':%s"%(elem, i))
                i = i + 1
            #translation_result_tmp.append('%s = global_defs.enum(%s, "%s", %s)'%(enum_name, 'global_defs' if is_global else 'sys.modules[__name__]', enum_name, ', '.join(element_list_with_values)))
            enum_template = """
class %(enum_name)s(global_defs.enum): #enum
    enum_name = '%(enum_name)s'
    values_dict = {%(values)s}
"""
            #translation_result_tmp.append('%s = global_defs.enum(%s, "%s")'%(enum_name, ', '.join(element_list_with_values)))
            translation_result_tmp.append(enum_template%{'enum_name': enum_name, 'values':', '.join(element_list_with_values)})
            
        if instruction_name == 'wait sec':
            t = match_groups[0]
            translation_result_tmp.append('time.sleep(%s)'%t)

        if instruction_name == 'wait for':
            condition = match_groups[0]
            translation_result_tmp.append('while not (%s):time.sleep(0.1)'%condition)

        if instruction_name == 'ext':
            procedure_name = match_groups[0]
            r = re.search(generic_regexes.line_begin+"EXTP", code_line, re.IGNORECASE)
            module_name = procedure_name #normally a function imported by EXT has the same name of the module in which it is contained. This seems not valid for EXTP
            if not r is None:
                module_name = 'kuka_internals'
            translation_result_tmp.append( "from %s import %s"%( module_name, procedure_name ) )

        if instruction_name == 'extfct':
            return_type, function_name = match_groups[0], match_groups[1]
            r = re.search(generic_regexes.line_begin+" *EXTFCTP", code_line, re.IGNORECASE)
            module_name = function_name #normally a function imported by EXT has the same name of the module in which it is contained. This seems not valid for EXTP
            if not r is None:
                module_name = 'kuka_internals'
            translation_result_tmp.append( "from %s import %s"%( module_name, function_name ) )

        if instruction_name == 'signal decl':
            is_global, signal_name, signal_start, signal_end = match_groups
            is_global = not is_global is None
            if signal_end is None:
                translation_result_tmp.append(("global_defs." if is_global else "") + "%s = signal(%s)"%(signal_name, signal_start))
            else:
                translation_result_tmp.append(("global_defs." if is_global else "") + "%s = signal(%s, %s)"%(signal_name, signal_start, signal_end))
        
        if instruction_name == 'function return':
            value = match_groups[0]
            translation_result_tmp.append("return" if value is None else ("return " + value))

        if instruction_name == 'continue':
            translation_result_tmp.append('global_defs.robot.do_not_stop_ADVANCE_on_next_IO()')
        
        return translation_result_tmp, file_lines 


class KRLStatementRepeatUntil(KRLGenericParser):
    condition = ""
    pass_to_be_added = True
    def __init__(self):
        permissible_instructions = ['until']
        permissible_instructions_dictionary = {k:v for k,v in instructions_defs.items() if k in permissible_instructions}
        KRLGenericParser.__init__(self, permissible_instructions_dictionary)

    def parse_single_instruction(self, code_line_original, code_line, instruction_name, match_groups, file_lines):
        translation_result_tmp = []
        
        if not instruction_name in ['until','']:
            self.pass_to_be_added = False

        if instruction_name == 'until':
            self.condition = match_groups[0].strip()
            translation_result_tmp.append("    if %s:"%self.condition)
            translation_result_tmp.append("        " + "break")
            self.pass_to_be_added = False
            self.stop_statement_found = True

        _translation_result_tmp, file_lines = KRLGenericParser.parse_single_instruction(self, code_line_original, code_line, instruction_name, match_groups, file_lines)
        if len(_translation_result_tmp):
            translation_result_tmp.extend(generic_regexes.indent_lines(_translation_result_tmp, 1))

        return translation_result_tmp, file_lines 


class KRLStatementWhile(KRLGenericParser):
    condition = ""
    pass_to_be_added = True
    def __init__(self, condition):
        self.condition = condition
        permissible_instructions = ['while end']
        permissible_instructions_dictionary = {k:v for k,v in instructions_defs.items() if k in permissible_instructions}
        KRLGenericParser.__init__(self, permissible_instructions_dictionary)

    def parse_single_instruction(self, code_line_original, code_line, instruction_name, match_groups, file_lines):
        translation_result_tmp = []
        
        if not instruction_name in ['while end','']:
            self.pass_to_be_added = False

        if instruction_name == 'while end':
            self.pass_to_be_added = False
            self.stop_statement_found = True

        _translation_result_tmp, file_lines = KRLGenericParser.parse_single_instruction(self, code_line_original, code_line, instruction_name, match_groups, file_lines)
        if len(_translation_result_tmp):
            translation_result_tmp.extend(generic_regexes.indent_lines(_translation_result_tmp, 1))

        return translation_result_tmp, file_lines 


class KRLStatementLoop(KRLGenericParser):
    pass_to_be_added = True
    def __init__(self):
        permissible_instructions = ['loop end']
        permissible_instructions_dictionary = {k:v for k,v in instructions_defs.items() if k in permissible_instructions}
        KRLGenericParser.__init__(self, permissible_instructions_dictionary)

    def parse_single_instruction(self, code_line_original, code_line, instruction_name, match_groups, file_lines):
        translation_result_tmp = []
        
        if not instruction_name in ['loop end','']:
            self.pass_to_be_added = False

        if instruction_name == 'loop end':
            self.pass_to_be_added = False
            self.stop_statement_found = True

        _translation_result_tmp, file_lines = KRLGenericParser.parse_single_instruction(self, code_line_original, code_line, instruction_name, match_groups, file_lines)
        if len(_translation_result_tmp):
            translation_result_tmp.extend(generic_regexes.indent_lines(_translation_result_tmp, 1))

        return translation_result_tmp, file_lines 


class KRLStatementFor(KRLGenericParser):
    variable = ""
    value_begin = ""
    value_end = ""
    value_step = ""
    pass_to_be_added = True
    def __init__(self, variable, value_begin, value_end, value_step = None):
        self.variable = variable
        self.value_begin = value_begin
        self.value_end = value_end
        self.value_step = value_step
        permissible_instructions = ['for end']
        permissible_instructions_dictionary = {k:v for k,v in instructions_defs.items() if k in permissible_instructions}
        KRLGenericParser.__init__(self, permissible_instructions_dictionary)

    def parse_single_instruction(self, code_line_original, code_line, instruction_name, match_groups, file_lines):
        translation_result_tmp = []
        
        if not instruction_name in ['for end', '']:
            self.pass_to_be_added = False

        if instruction_name == 'for end':
            self.pass_to_be_added = False
            self.stop_statement_found = True

        _translation_result_tmp, file_lines = KRLGenericParser.parse_single_instruction(self, code_line_original, code_line, instruction_name, match_groups, file_lines)
        if len(_translation_result_tmp):
            translation_result_tmp.extend(generic_regexes.indent_lines(_translation_result_tmp, 1))

        return translation_result_tmp, file_lines 


class KRLStatementIf(KRLGenericParser):
    condition = ""
    pass_to_be_added = True
    def __init__(self, condition):
        self.condition = condition
        permissible_instructions = ['else','if end']
        permissible_instructions_dictionary = {k:v for k,v in instructions_defs.items() if k in permissible_instructions}
        KRLGenericParser.__init__(self, permissible_instructions_dictionary)

    def parse_single_instruction(self, code_line_original, code_line, instruction_name, match_groups, file_lines):
        translation_result_tmp = []
        
        if not instruction_name in ['else','if end','']:
            self.pass_to_be_added = False

        if instruction_name == 'else':
            if self.pass_to_be_added:
                translation_result_tmp.append('    pass')
            translation_result_tmp.append("else:")
            self.pass_to_be_added = True
        if instruction_name == 'if end':
            if self.pass_to_be_added:
                translation_result_tmp.append('    pass')
            self.pass_to_be_added = False

            self.stop_statement_found = True

        _translation_result_tmp, file_lines = KRLGenericParser.parse_single_instruction(self, code_line_original, code_line, instruction_name, match_groups, file_lines)
        if len(_translation_result_tmp):
            translation_result_tmp.extend(generic_regexes.indent_lines(_translation_result_tmp, 1))

        return translation_result_tmp, file_lines 


class KRLStatementSwitch(KRLGenericParser):
    value_to_switch = "" #the switch(value_to_switch)
    pass_to_be_added = False
    first_switch_instruction = True
    def __init__(self, value_to_switch):
        self.value_to_switch = value_to_switch
        permissible_instructions = ['case','default','endswitch']
        permissible_instructions_dictionary = {k:v for k,v in instructions_defs.items() if k in permissible_instructions}
        KRLGenericParser.__init__(self, permissible_instructions_dictionary)

    def parse_single_instruction(self, code_line_original, code_line, instruction_name, match_groups, file_lines):
        translation_result_tmp = []
        
        if not instruction_name in ['case','default','endswitch','']:
            self.pass_to_be_added = False

        if instruction_name == 'case':
            if self.pass_to_be_added:
                translation_result_tmp.append('    pass')
            case_value = match_groups[0]

            condition = "%s == %s:"%(self.value_to_switch, case_value)
            if ',' in case_value:
                case_values = case_value.split(',')
                condition = ' or '.join(['%s == %s'%(self.value_to_switch, x) for x in case_values]) + ':'

            if self.first_switch_instruction:
                translation_result_tmp.append("if " + condition)
            else:
                translation_result_tmp.append("elif " + condition)
            self.first_switch_instruction = False
            self.pass_to_be_added = True
        if instruction_name == 'default':
            if self.pass_to_be_added:
                translation_result_tmp.append('    pass')
            translation_result_tmp.append("else:")
        if instruction_name == 'endswitch':
            self.pass_to_be_added = False
            self.stop_statement_found = True

        _translation_result_tmp, file_lines = KRLGenericParser.parse_single_instruction(self, code_line_original, code_line, instruction_name, match_groups, file_lines)
        if len(_translation_result_tmp):
            translation_result_tmp.extend(generic_regexes.indent_lines(_translation_result_tmp, 1))

        return translation_result_tmp, file_lines 


class KRLProcedureParser(KRLGenericParser):
    name = ""
    param_names = None
    callers_list = None
    calling_list = None
    declarations_done = False
    pass_to_be_added = True
    def __init__(self, name, param_names):
        permissible_instructions = ['procedure end','function end','enum definition','struc declaration']
        permissible_instructions_dictionary = {k:v for k,v in instructions_defs.items() if k in permissible_instructions}
        KRLGenericParser.__init__(self, permissible_instructions_dictionary)
        #this is to reduce priority of instruction declaration, otherwise it gets priority over instructions such as "RETURN value"
        self.permissible_instructions_dictionary['variable declaration'] = instructions_defs['variable declaration']
        self.name = name
        self.param_names = param_names
        self.callers_list = []
        self.calling_list = []

    def parse_single_instruction(self, code_line_original, code_line, instruction_name, match_groups, file_lines):
        translation_result_tmp = []

        if not instruction_name in ['procedure end','function end','']:
            self.pass_to_be_added = False

        self.declarations_done = self.declarations_done or instruction_name in ['halt','switch','lin','ptp','circ','if begin','for begin','while begin','repeat','loop begin','interrupt decl','interrupt on','interrupt off','trigger distance','trigger path','function call','wait sec','wait for','continue',]
        #if declarations are done remove the regex to avoid search it
        if self.declarations_done:
            self.permissible_instructions_dictionary.pop('variable declaration', None)

        if instruction_name == 'procedure end': 
            self.stop_statement_found = True
            if self.pass_to_be_added:
                translation_result_tmp.append('    pass')
        
        if instruction_name == 'function end':
            self.stop_statement_found = True
            if self.pass_to_be_added:
                translation_result_tmp.append('    pass')

        _translation_result_tmp, file_lines = KRLGenericParser.parse_single_instruction(self, code_line_original, code_line, instruction_name, match_groups, file_lines)
        if len(_translation_result_tmp):
            translation_result_tmp.extend(generic_regexes.indent_lines(_translation_result_tmp, 1))

        return translation_result_tmp, file_lines


class KRLFunctionParser(KRLProcedureParser):
    return_type = None
    def __init__(self, name, param_names, return_type):
        KRLProcedureParser.__init__(self, name, param_names)
        self.return_type = return_type
        
