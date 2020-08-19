import re
import os
import generic_regexes
import flow_chart_graphics
import collections
import remi.gui as gui

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
    'resume':               generic_regexes.a_line_containing("RESUME"),

    'trigger distance':     generic_regexes.a_line_containing( "TRIGGER +WHEN +DISTANCE *= *(0|1) +DELAY *= *" + generic_regexes.int_or_real_number + " +DO +(.+)" ),
    'trigger path':         generic_regexes.a_line_containing( "TRIGGER +WHEN +PATH *= *(.+) +DELAY *= *" + generic_regexes.int_or_real_number + " +DO +(.+)" ),

    'variable assignment':  generic_regexes.a_line_containing( generic_regexes.global_def + "(DECL +)?(?:" + generic_regexes.variable_name + " +)?" + generic_regexes.variable_name + " *= *([^;]+)" ),
    'variable declaration': generic_regexes.a_line_containing( generic_regexes.global_def + "(DECL +)?([^ =\(]+) +(([^ =\(]+"+generic_regexes.c(generic_regexes.index_3d)+"?)( *, *[^ =]+" + generic_regexes.c(generic_regexes.index_3d) + "?)*)" ),

    'function call':        generic_regexes.a_line_containing( generic_regexes.variable_name + " *\( *(.*) *\)" ),

    'enum definition':      generic_regexes.a_line_containing( generic_regexes.global_def + "ENUM +([^ ]+) +.*" ),

    'wait sec':             generic_regexes.a_line_containing( "WAIT +SEC +" + generic_regexes.int_or_real_number ),

    'wait for':             generic_regexes.a_line_containing( "WAIT +FOR +" + "([^;]+)" ),

    'ext':                  generic_regexes.line_begin + "EXTP? +([^ \(]+) *\(",
    'extfct':               generic_regexes.line_begin + "EXTFCTP? +([^ ]+) +([^ \(]+) *\(",

    'signal decl':          generic_regexes.a_line_containing( generic_regexes.global_def + r"SIGNAL +([^ ]+) +((?:[^ \[]+)(?:\[ *[0-9]* *\])?)(?: +TO +((?:[^ \[]+)(?:\[ *[0-9]* *\])?))?" ),

    'continue':             generic_regexes.a_line_containing( "CONTINUE" ), #in KRL Prevention of advance run stops.
}


uuid = 0


class KRLGenericParser(flow_chart_graphics.FlowInstruction):
    stop_statement_found = False
    permissible_instructions_dictionary = None
    indent_comments = True
    def __init__(self, permissible_instructions_dictionary):
        self.permissible_instructions_dictionary = collections.OrderedDict(permissible_instructions_dictionary)
        standard_permissible_instructions = ['function return','meta instruction','halt','switch','lin','ptp','circ','if begin','for begin','while begin','repeat','loop begin','interrupt decl','interrupt on','interrupt off','trigger distance','trigger path','variable assignment','function call','wait sec','wait for', 'ext', 'extfct', 'signal decl','continue','resume',]
        self.permissible_instructions_dictionary.update({k:v for k,v in instructions_defs.items() if k in standard_permissible_instructions})

        flow_chart_graphics.FlowInstruction.__init__(self)

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
        global uuid
        translation_result_tmp = []






        if "profileRobotMeasures" in code_line_original:
            print("brakepoint")



        

        if ':' in code_line:
            if instruction_name in ['variable assignment', 'function call', 'return', 'lin', 'ptp', 'circ']:
                code_line = generic_regexes.replace_geometric_operator(code_line)

        if instruction_name == 'meta instruction':
            return translation_result_tmp, file_lines

        if instruction_name == 'halt':
            translation_result_tmp.append("assert(False) # halt")
            node = flow_chart_graphics.FlowInstruction('HALT')
            self.append(node)

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
            node = flow_chart_graphics.FlowInstruction('LIN %s'%position)
            self.append(node)

        if instruction_name == 'ptp':
            position = match_groups[0].strip()
            position = position.replace(" c_dis", ", c_dis")
            position = position.replace(" c_ptp", ", c_ptp")
            position = position.replace(" c_ori", ", c_ori")
            translation_result_tmp.append("global_defs.robot.ptp(%s)"%position)
            node = flow_chart_graphics.FlowInstruction('PTP %s'%position)
            self.append(node)

        if instruction_name == 'circ':
            position = match_groups[0].strip().lower()
            position = position.replace(" c_dis", ", c_dis")
            position = position.replace(" c_ptp", ", c_ptp")
            position = position.replace(" c_ori", ", c_ori")
            translation_result_tmp.append("global_defs.robot.circ(%s)"%position)
            node = flow_chart_graphics.FlowInstruction('CIRC %s'%position)
            self.append(node)

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
                var, size, subindex, is_array = generic_regexes.split_varname_index(var)
                if is_array:
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
                translation_result_tmp.append("for %s in range(%s, %s + 1, %s):"%(initialization_variable, initialization_value, value_end, step.strip()))
            else:
                translation_result_tmp.append("for %s in range(%s, %s + 1):"%(initialization_variable, initialization_value, value_end))

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
            node = KRLStatementLoop()
            self.append(node)
            _translation_result_tmp, file_lines = node.parse(file_lines)
            if len(_translation_result_tmp):
                translation_result_tmp.extend(_translation_result_tmp)

        if instruction_name == 'interrupt decl':
            interrupt_declaration_template = \
                "def fcond%(interrupt_name)s():\n" \
                "    if interrupt_flags[%(interrupt_number)s]:\n" \
                "        return (%(condition)s)\n" \
                "    return False\n" \
                "def fcall%(interrupt_name)s():\n" \
                "    %(instruction)s\n" \
                "interrupts[%(interrupt_number)s] = InterruptData(fcall%(interrupt_name)s, threads_callstack[threading.currentThread][-1], fcond%(interrupt_name)s)\n"
            is_global, interrupt_number, condition, instruction = match_groups
            is_global = not is_global is None 
            node = InterruptObject(interrupt_number, is_global, condition, instruction)
            self.get_parent_function().append(node)
            interrupt_declaration = interrupt_declaration_template%{'interrupt_number':interrupt_number, 'condition':condition, 'instruction':instruction, 'interrupt_name':'_interrupt%s'%interrupt_number}
            translation_result_tmp.extend(interrupt_declaration.split('\n'))
            #translation_result_tmp.append('interrupts[%s] = """if %s:%s""" '%(interrupt_number, condition, instruction)] #to be evaluated cyclically with eval
        if instruction_name == 'interrupt on':
            interrupt_number = match_groups[0]
            translation_result_tmp.append('interrupt_flags[%s] = True'%interrupt_number)
            node = flow_chart_graphics.FlowInstruction('INTERRUPT ON %s'%interrupt_number)
            self.append(node)

        if instruction_name == 'interrupt off':
            interrupt_number = match_groups[0]
            translation_result_tmp.append('interrupt_flags[%s] = False'%interrupt_number)
            node = flow_chart_graphics.FlowInstruction('INTERRUPT OFF %s'%interrupt_number)
            self.append(node)

        if instruction_name == 'resume':
            translation_result_tmp.append("robot.resume_interrupt()")
            node = flow_chart_graphics.FlowInstruction('RESUME')
            self.append(node)

        if instruction_name == 'trigger distance':
            trigger_distance_declaration_template = \
                "def %(trigger_name)s():\n" \
                "    %(instruction)s\n" \
                "threading.Timer(%(delay)s, %(trigger_name)s).start()\n"

            distance, delay, instruction = match_groups
            trigger_func_name = 'trigger_func%s'%uuid
            uuid = uuid + 1
            trigger_declaration = trigger_distance_declaration_template%{'trigger_name':trigger_func_name, 'instruction':instruction, 'delay':delay}
            translation_result_tmp.extend(trigger_declaration.split('\n'))
            node = flow_chart_graphics.FlowInstruction('TRIGGER WHEN DISTANCE=%s DELAY=%s DO %s'%(distance, delay, instruction))
            self.append(node)
            
        if instruction_name == 'trigger path':
            trigger_path_declaration_template = \
                "#this should be scheduled at path=%(path)s, to be implemented\n" \
                "def %(trigger_name)s():\n" \
                "    %(instruction)s\n" \
                "threading.Timer(%(delay)s, %(trigger_name)s).start()\n"

            path, delay, instruction = match_groups
            trigger_func_name = 'trigger_func%s'%uuid
            uuid = uuid + 1
            trigger_declaration = trigger_path_declaration_template%{'trigger_name':trigger_func_name, 'instruction':instruction, 'delay':delay, 'path':path}
            translation_result_tmp.extend(trigger_declaration.split('\n'))
            node = flow_chart_graphics.FlowInstruction('TRIGGER WHEN PATH=%s DELAY=%s DO %s'%(path, delay, instruction))
            self.append(node)

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

            for var in variables_names:
                #if the variable is not declared as parameter, declare it in procedure/function body
                #if actual_code_block is None or (not re.sub(generic_regexes.index_3d, '', var) in actual_code_block.param_names):
                parent_function = self.get_parent_function()
                var, size, subindex, is_array = generic_regexes.split_varname_index(var)

                if not parent_function is None:
                    parent_function.local_variables[var] = type_name

                if parent_function is None or not var in parent_function.param_names:
                    #check if it is an array
                    if is_array:
                        translation_result_tmp.append(("global_defs." if is_global else "")+"%s = multi_dimensional_array(%s, %s)"%(var,type_name,size))
                    else:
                        translation_result_tmp.append(("global_defs." if is_global else "")+"%s = %s()"%(var,type_name))

                    if is_global:
                        translation_result_tmp.append("from global_defs import %s"%(var))
                else:
                    #   #if the variable decl is a function parameter it have to be not declared again
                    #    # and we discard also an end of line comment
                    #    if not parent_function is None:
                    #        parent_function.pass_to_be_added = True
                    #endofline_comment_to_append = ""

                    if not parent_function is None: #if variable declaration is a procedure paramter
                        if not is_array: #this is intended to recreate enum, arrays are already transferred correctly
                            translation_result_tmp.append(("global_defs." if is_global else "")+"%(var)s = %(typ)s(%(var)s)"%{'var':var,'typ':type_name})



        if instruction_name == 'variable assignment':
            result = re.search(instructions_defs['variable assignment'], code_line, re.IGNORECASE)
            elements = result.groups()
            #(None, 'decl ', 'circ_type', 'def_circ_typ', 'system_constants.base')
            #print(elements)
            is_global = not elements[0] is None 
            is_decl = not elements[1] is None
            type_name = elements[2]
            var = elements[3].strip()
            value = elements[4].strip()
            var, size, subindex, is_array = generic_regexes.split_varname_index(var)

            parent_function = self.get_parent_function()

            if not type_name is None: 
                type_name = type_name.strip()
                translation_result_tmp.append("%s%s%s = %s(%s)"%(var, size, subindex, type_name, value))
                
                #if there is a parent function, the variable name have to be appended to local_variables dictionary
                if not parent_function is None:
                    parent_function.local_variables[var] = type_name

            else:
                if not parent_function is None:
                    if not (generic_regexes.var_without_pointed_field(var)[0] in parent_function.local_variables):
                        parent_function.global_variables.append(generic_regexes.var_without_pointed_field(var)[0])

                if is_array:
                    translation_result_tmp.append("%s%s%s = %s"%(var, size, subindex, value))
                else:
                    translation_result_tmp.append("%s%s = %s"%(var, subindex, value))

            node = flow_chart_graphics.FlowInstruction('%s%s = %s'%(var if not is_array else "%s%s"%(var, size), subindex, value))
            self.append(node)


        if instruction_name == 'function call':
            self.get_parent_function().calling_list.append(match_groups[0])
            translation_result_tmp.append(code_line.strip())
            node = flow_chart_graphics.FlowInstruction('CALL %s'%code_line.strip())
            self.append(node)

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
            enum_template = \
                "class %(enum_name)s(global_defs.enum): #enum\n" \
                "    enum_name = '%(enum_name)s'\n" \
                "    values_dict = {%(values)s}"
            #translation_result_tmp.append('%s = global_defs.enum(%s, "%s")'%(enum_name, ', '.join(element_list_with_values)))
            translation_result_tmp.append(enum_template%{'enum_name': enum_name, 'values':', '.join(element_list_with_values)})
            
        if instruction_name == 'wait sec':
            t = match_groups[0]
            translation_result_tmp.append('robot.wait_sec(%s)'%t)
            node = flow_chart_graphics.FlowInstruction('WAIT SEC %s'%t)
            self.append(node)

        if instruction_name == 'wait for':
            condition = match_groups[0]
            translation_result_tmp.append('while not (%s):time.sleep(0.1)'%condition)
            node = flow_chart_graphics.FlowInstruction('WAIT FOR %s'%condition)
            self.append(node)

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
            node = flow_chart_graphics.FlowInstruction('RETURN %s'%value)
            self.append(node)

        if instruction_name == 'continue':
            translation_result_tmp.append('global_defs.robot.do_not_stop_ADVANCE_on_next_IO()')
            node = flow_chart_graphics.FlowInstruction('CONTINUE')
            self.append(node)
        
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

            self.box_text_content = 'UNTIL %s'%(self.condition)

        _translation_result_tmp, file_lines = KRLGenericParser.parse_single_instruction(self, code_line_original, code_line, instruction_name, match_groups, file_lines)
        if len(_translation_result_tmp):
            translation_result_tmp.extend(generic_regexes.indent_lines(_translation_result_tmp, 1))

        return translation_result_tmp, file_lines 

    def recalc_size_and_arrange_children(self):
        
        w, h = super(KRLStatementRepeatUntil, self).recalc_size_and_arrange_children()
        self.box_height = 100
        
        #the box is at the bottom
        h = h + self.box_height

        h = h + 30*2 #height is increased by 30 for bottom lines
        w = w + 30*2 #to give margins to return and endfor lines
        gui._MixinSvgSize.set_size(self, w, h)

        self.set_viewbox(-w/2, 0, w, h)

        return w, h

    def draw(self):
        line_length = 30
        self.box_height = line_length
        self.box_width = max( len(self.box_text_content) * self.text_letter_width, 200 )
        w, h = self.recalc_size_and_arrange_children()
        
        #top vertical line
        self.drawings_keys.append( self.append(gui.SvgLine(0, 0, 0, line_length), 'line_top') )

        #middle vertical line
        self.drawings_keys.append( self.append(gui.SvgLine(0, h-self.box_height-line_length*2, 0, h-self.box_height-line_length*1), 'line_middle') )

        #central box line
        self.drawings_keys.append( self.append(flow_chart_graphics.RomboidBox(-self.box_width/2, h-self.box_height-line_length*1, self.box_width, self.box_height, self.box_text_content), 'box') )

        #line returns
        poly = gui.SvgPolyline(10)
        poly.add_coord(-self.box_width/2, h-self.box_height/2-line_length*1)
        poly.add_coord(-w/2, h-self.box_height/2-line_length*1)
        poly.add_coord(-w/2, line_length)
        poly.add_coord(0, line_length)
        self.drawings_keys.append( self.append(poly, 'lret') )
        
        #arrow
        polygon = gui.SvgPolygon(10)
        polygon.add_coord(0, line_length)
        polygon.add_coord(-10, line_length+5)
        polygon.add_coord(-10, line_length-5)
        self.drawings_keys.append( self.append(polygon, 'arrow') )
        self.children['arrow'].set_stroke(1, 'black')
        self.children['arrow'].set_fill('black')

        poly = gui.SvgPolyline(10)
        poly.add_coord(self.box_width/2, h-self.box_height/2-line_length*1)
        poly.add_coord(w/2, h-self.box_height/2-line_length*1)
        poly.add_coord(w/2, h)
        poly.add_coord(0, h)
        self.drawings_keys.append( self.append(poly, 'lendfor') )
        
        self.children['line_middle'].set_stroke(1, 'black')
        self.children['line_top'].set_stroke(1, 'black')
        self.children['lret'].set_stroke(1, 'black')
        self.children['lret'].set_fill('transparent')
        self.children['lendfor'].set_stroke(1, 'black')
        self.children['lendfor'].set_fill('transparent')
        
        self.children['box'].set_stroke(1, 'black')


class KRLStatementWhile(KRLGenericParser):
    condition = ""
    pass_to_be_added = True
    def __init__(self, condition):
        self.condition = condition
        permissible_instructions = ['while end']
        permissible_instructions_dictionary = {k:v for k,v in instructions_defs.items() if k in permissible_instructions}
        KRLGenericParser.__init__(self, permissible_instructions_dictionary)

        self.box_text_content = 'WHILE %s'%(condition)

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

    def recalc_size_and_arrange_children(self):
        w, h = super(KRLStatementWhile, self).recalc_size_and_arrange_children()
        
        h = h + 30*3 #height is increased by 30 for bottom lines
        w = w + 30*2 #to give margins to return and endfor lines
        gui._MixinSvgSize.set_size(self, w, h)

        self.set_viewbox(-w/2, 0, w, h)

        return w, h

    def draw(self):
        self.box_height = 100
        self.box_width = max( len(self.box_text_content) * self.text_letter_width, 200 )
        w, h = self.recalc_size_and_arrange_children()
        
        line_length = 30
        #top vertical line
        self.drawings_keys.append( self.append(gui.SvgLine(0, 0, 0, line_length), 'line_top') )

        #central box line
        self.drawings_keys.append( self.append(flow_chart_graphics.RomboidBox(-self.box_width/2, line_length, self.box_width, self.box_height-line_length, self.box_text_content), 'box') )

        #line returns
        poly = gui.SvgPolyline(10)
        poly.add_coord(0, h-line_length*3)
        poly.add_coord(0, h-line_length*2)
        poly.add_coord(-w/2, h-line_length*2)
        poly.add_coord(-w/2, (self.box_height-line_length)/2 + line_length)
        poly.add_coord(-self.box_width/2, (self.box_height-line_length)/2 + line_length)
        self.drawings_keys.append( self.append(poly, 'lret') )

        poly = gui.SvgPolyline(10)
        poly.add_coord(self.box_width/2, (self.box_height-line_length)/2 + line_length)
        poly.add_coord(w/2, (self.box_height-line_length)/2 + line_length)
        poly.add_coord(w/2, h-line_length*1)
        poly.add_coord(0, h-line_length*1)
        poly.add_coord(0, h)
        self.drawings_keys.append( self.append(poly, 'lendfor') )

        polygon = gui.SvgPolygon(10)
        polygon.add_coord(-self.box_width/2, (self.box_height-line_length)/2 + line_length)
        polygon.add_coord(-self.box_width/2-10, (self.box_height-line_length)/2 + line_length-5)
        polygon.add_coord(-self.box_width/2-10, (self.box_height-line_length)/2 + line_length+5)
        self.drawings_keys.append( self.append(polygon, 'arrow') )
        self.children['arrow'].set_stroke(1, 'black')
        self.children['arrow'].set_fill('black')
        
        self.children['line_top'].set_stroke(1, 'black')
        self.children['lret'].set_stroke(1, 'black')
        self.children['lret'].set_fill('transparent')
        self.children['lendfor'].set_stroke(1, 'black')
        self.children['lendfor'].set_fill('transparent')
        
        self.children['box'].set_stroke(1, 'black')


class KRLStatementLoop(KRLGenericParser):
    pass_to_be_added = True
    def __init__(self):
        permissible_instructions = ['loop end']
        permissible_instructions_dictionary = {k:v for k,v in instructions_defs.items() if k in permissible_instructions}
        KRLGenericParser.__init__(self, permissible_instructions_dictionary)
        self.box_text_content = 'LOOP infinite'

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

    def recalc_size_and_arrange_children(self):
        w, h = super(KRLStatementLoop, self).recalc_size_and_arrange_children()
        
        h = h + 30*1 #height is increased by 30 for bottom lines
        w = w + 30*2 #to give margins to return and endfor lines
        gui._MixinSvgSize.set_size(self, w, h)

        self.set_viewbox(-w/2, 0, w, h)

        return w, h

    def draw(self):
        self.box_height = 100
        self.box_width = max( len(self.box_text_content) * self.text_letter_width, 200 )
        w, h = self.recalc_size_and_arrange_children()
        
        line_length = 30
        #top vertical line
        self.drawings_keys.append( self.append(gui.SvgLine(0, 0, 0, line_length), 'line_top') )

        #central box line
        self.drawings_keys.append( self.append(flow_chart_graphics.RomboidBox(-self.box_width/2, line_length, self.box_width, self.box_height-line_length, self.box_text_content), 'box') )

        #line returns
        poly = gui.SvgPolyline(10)
        poly.add_coord(0, h-line_length*1) 
        poly.add_coord(0, h)
        poly.add_coord(-w/2, h)
        poly.add_coord(-w/2, (self.box_height-line_length)/2 + line_length)
        poly.add_coord(-self.box_width/2, (self.box_height-line_length)/2 + line_length)
        self.drawings_keys.append( self.append(poly, 'line') )
        
        #arrow
        polygon = gui.SvgPolygon(10)
        polygon.add_coord(-self.box_width/2, (self.box_height-line_length)/2 + line_length)
        polygon.add_coord(-self.box_width/2-10, (self.box_height-line_length)/2 + line_length-5)
        polygon.add_coord(-self.box_width/2-10, (self.box_height-line_length)/2 + line_length+5)
        self.drawings_keys.append( self.append(polygon, 'arrow') )
        self.children['arrow'].set_stroke(1, 'black')
        self.children['arrow'].set_fill('black')

        self.children['line_top'].set_stroke(1, 'black')
        self.children['line'].set_stroke(1, 'black')
        self.children['line'].set_fill('transparent')

        self.children['box'].set_stroke(1, 'black')


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

        self.box_text_content = 'FOR %s=%s TO %s%s'%(variable, value_begin, value_end, '' if value_step is None else 'STEP %s'%value_step)

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

    def recalc_size_and_arrange_children(self):
        w, h = super(KRLStatementFor, self).recalc_size_and_arrange_children()
        
        h = h + 30*3 #height is increased by 30 for bottom lines
        w = w + 30*2 #to give margins to return and endfor lines
        gui._MixinSvgSize.set_size(self, w, h)

        self.set_viewbox(-w/2, 0, w, h)

        return w, h

    def draw(self):
        self.box_height = 100
        self.box_width = max( len(self.box_text_content) * self.text_letter_width, 200 )
        w, h = self.recalc_size_and_arrange_children()
        
        line_length = 30
        #top vertical line
        self.drawings_keys.append( self.append(gui.SvgLine(0, 0, 0, line_length), 'line_top') )

        #central box line
        self.drawings_keys.append( self.append(flow_chart_graphics.ForBox(-self.box_width/2, line_length, self.box_width, self.box_height-line_length, self.box_text_content), 'box') )

        #line returns
        poly = gui.SvgPolyline(10)
        poly.add_coord(0, h-line_length*3)
        poly.add_coord(0, h-line_length*2)
        poly.add_coord(-w/2, h-line_length*2)
        poly.add_coord(-w/2, (self.box_height-line_length)/2 + line_length)
        poly.add_coord(-self.box_width/2, (self.box_height-line_length)/2 + line_length)
        self.drawings_keys.append( self.append(poly, 'lret') )

        #arrow
        polygon = gui.SvgPolygon(10)
        polygon.add_coord(-self.box_width/2, (self.box_height-line_length)/2 + line_length)
        polygon.add_coord(-self.box_width/2-10, (self.box_height-line_length)/2 + line_length-5)
        polygon.add_coord(-self.box_width/2-10, (self.box_height-line_length)/2 + line_length+5)
        self.drawings_keys.append( self.append(polygon, 'arrow') )
        self.children['arrow'].set_stroke(1, 'black')
        self.children['arrow'].set_fill('black')

        poly = gui.SvgPolyline(10)
        poly.add_coord(self.box_width/2, (self.box_height-line_length)/2 + line_length)
        poly.add_coord(w/2, (self.box_height-line_length)/2 + line_length)
        poly.add_coord(w/2, h-line_length*1)
        poly.add_coord(0, h-line_length*1)
        poly.add_coord(0, h)
        self.drawings_keys.append( self.append(poly, 'lendfor') )
        
        self.children['line_top'].set_stroke(1, 'black')
        self.children['lret'].set_stroke(1, 'black')
        self.children['lret'].set_fill('transparent')
        self.children['lendfor'].set_stroke(1, 'black')
        self.children['lendfor'].set_fill('transparent')

        self.children['box'].set_stroke(1, 'black')


class KRLStatementIf(KRLGenericParser):
    condition = ""
    pass_to_be_added = True
    nodes_yes = None
    nodes_no = None
    yes_done = False
    def __init__(self, condition):
        self.condition = condition
        permissible_instructions = ['else','if end']
        permissible_instructions_dictionary = {k:v for k,v in instructions_defs.items() if k in permissible_instructions}

        self.nodes_yes = []
        self.nodes_no = []

        KRLGenericParser.__init__(self, permissible_instructions_dictionary)

        self.box_text_content = 'IF %s'%(condition)

    def append(self, v, *args, **kwargs):
        if not self.yes_done:
            self.nodes_yes.append(v)
        else:
            self.nodes_no.append(v)
        return super(KRLStatementIf, self).append(v, *args, **kwargs)

    def parse_single_instruction(self, code_line_original, code_line, instruction_name, match_groups, file_lines):
        translation_result_tmp = []
        
        if not instruction_name in ['else','if end','']:
            self.pass_to_be_added = False

        if instruction_name == 'else':
            self.yes_done = True
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

    def recalc_size_and_arrange_children(self):
        #remove all drawings prior to redraw it
        for k in self.drawings_keys:
            self.remove_child(self.children[k])
        self.drawings_keys = []

        box_text_size = max( len(self.box_text_content) * self.text_letter_width, 100 )
        h = self.box_height

        w_max = box_text_size
        #estimate self width
        for k in self._render_children_list:
            v = self.children[k]
            v.draw()
            w_max = max(w_max, float(v.attr_width))

        total_width = (w_max*2+box_text_size)

        h_yes = h
        for v in self.nodes_yes:
            v.set_position(-w_max/2+total_width/2-float(v.attr_width)/2 , h_yes)
            h_yes = h_yes + float(v.attr_height) 

        h_no = h
        for v in self.nodes_no:
            v.set_position(-total_width/2 + w_max/2 - float(v.attr_width)/2, h_no)
            h_no = h_no + float(v.attr_height) 
            
        #w_max = w_max * 2 + box_text_size #the width is x3 because it has components at left and at right

        h = max(h_yes, h_no)
        
        h = h + 30 #height is increased by 30 for bottom lines

        gui._MixinSvgSize.set_size(self, total_width, h)

        total_width = (w_max*2+box_text_size)
        self.set_viewbox(-total_width/2, 0, total_width, h)

        return box_text_size, w_max, total_width, h

    def draw(self):
        self.box_height = 200
        box_text_size, w_max, w, h = self.recalc_size_and_arrange_children()
        
        line_length = 30
        #top vertical line
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, gui.SvgLine(0, 0, 0, line_length), 'line_top') )

        romboid_h = self.box_height-(line_length)
        romboid_w = box_text_size
        #right horizontal line
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, gui.SvgLine(romboid_w/2, romboid_h/2+line_length, w/2-w_max/2 , romboid_h/2+line_length), 'line_right_h') )

        #left horizontal line
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, gui.SvgLine(-romboid_w/2, romboid_h/2+line_length, -w/2+w_max/2 , romboid_h/2+line_length), 'line_left_h') )

        #right vertical line
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, gui.SvgLine(w/2-w_max/2, romboid_h/2+line_length, w/2-w_max/2 , self.box_height), 'line_right_v') )
        #left vertical line
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, gui.SvgLine(-w/2+w_max/2, romboid_h/2+line_length, -w/2+w_max/2 , self.box_height), 'line_left_v') )


        #right vertical line bottom
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, gui.SvgLine(w/2-w_max/2, h-line_length, w/2-w_max/2, h), 'line_right_v_b') )
        #left vertical line bottom
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, gui.SvgLine(-w/2+w_max/2, h-line_length, -w/2+w_max/2, h), 'line_left_v_b') )

        #line bottom
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, gui.SvgLine(-w/2+w_max/2, h-1, w/2-w_max/2, h-1), 'line_bottom') )

        #central box line
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, flow_chart_graphics.RomboidBox(-romboid_w/2, line_length, romboid_w, romboid_h, self.box_text_content), 'box') )


        txt_true = gui.SvgText(romboid_w/2, romboid_h/2 + line_length -3, 'true')
        txt_true.attributes['text-anchor'] = 'start'
        txt_true.attributes['dominant-baseline'] = 'baseline' #'middle'
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, txt_true, 'true'))

        txt_false = gui.SvgText(-romboid_w/2, romboid_h/2 + line_length -3, 'false')
        txt_false.attributes['text-anchor'] = 'end'
        txt_false.attributes['dominant-baseline'] = 'baseline' #'middle'
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, txt_false, 'false'))


        self.children['line_top'].set_stroke(1, 'black')
        self.children['line_right_h'].set_stroke(1, 'black')
        self.children['line_left_h'].set_stroke(1, 'black')
        self.children['line_right_v'].set_stroke(1, 'black')
        self.children['line_left_v'].set_stroke(1, 'black')
        self.children['line_right_v_b'].set_stroke(1, 'black')
        self.children['line_left_v_b'].set_stroke(1, 'black')
        self.children['line_bottom'].set_stroke(1, 'black')

        self.children['box'].set_stroke(1, 'black')


#this is a fake KRLGenericParser because it have not to parse code
# it subclasses KRLGenericParser in order to make it possible call get_parent_function
# it is the KRLStatementSwitch that parses code and appends widget to this
class KRLStatementCase(KRLGenericParser):
    condition = ""
    nodes_yes = None
    nodes_no = None
    yes_done = False
    def __init__(self, condition):
        self.condition = condition
        self.nodes_yes = []
        self.nodes_no = []

        permissible_instructions = []
        permissible_instructions_dictionary = {k:v for k,v in instructions_defs.items() if k in permissible_instructions}
        KRLGenericParser.__init__(self, permissible_instructions_dictionary)

        flow_chart_graphics.FlowInstruction.__init__(self,'CASE %s'%(condition))

    def append(self, v, *args, **kwargs):
        if not self.yes_done:
            self.nodes_yes.append(v)
        else:
            self.nodes_no.append(v)
        return super(KRLStatementCase, self).append(v, *args, **kwargs)

    def recalc_size_and_arrange_children(self):
        #remove all drawings prior to redraw it
        for k in self.drawings_keys:
            self.remove_child(self.children[k])
        self.drawings_keys = []

        w = max( len(self.box_text_content) * self.text_letter_width, 200 )
        h = self.box_height

        w_max_yes = w
        w_max_no = w
        #estimate self width
        for v in self.nodes_yes:
            v.draw()
            w_max_yes = max(w_max_yes, float(v.attr_width))
            print(v.box_text_content + ": " + v.attr_width)
        for v in self.nodes_no:
            v.draw()
            w_max_no = max(w_max_no, float(v.attr_width))
            print(v.box_text_content + ": " + v.attr_width)

        w = (w_max_yes*2 + w_max_no) + 10

        h_yes = h
        for v in self.nodes_yes:
            v.set_position(w/2-float(v.attr_width), h_yes)
            h_yes = h_yes + float(v.attr_height) 

        h_no = h
        for v in self.nodes_no:
            v.set_position(-float(v.attr_width)/2, h_no)
            h_no = h_no + float(v.attr_height) 
            
        #w_max = w_max * 3 #the width is x3 because it has components at left and at right

        h = max(h_yes, h_no)
        
        h = h + 30 #height is increased by 30 for bottom lines

        gui._MixinSvgSize.set_size(self, w, h)

        self.set_viewbox(-w/2, 0, w, h)

        return w, w_max_yes, w_max_no, h, h_yes, h_no

    def draw(self):
        self.box_height = 200
        w, w_max_yes, w_max_no, h, h_yes, h_no = self.recalc_size_and_arrange_children()
        
        line_length = 30
        #top vertical line
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, gui.SvgLine(0, 0, 0, line_length), 'line_top') )

        romboid_h = self.box_height-(line_length)
        romboid_w = max( len(self.box_text_content) * self.text_letter_width, 200 )
        #right horizontal line
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, gui.SvgLine(romboid_w/2, romboid_h/2+line_length, w/2 - w_max_yes/2 , romboid_h/2+line_length), 'line_right_h') )
        
        #right vertical line
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, gui.SvgLine(w/2 - w_max_yes/2 , romboid_h/2+line_length, w/2 - w_max_yes/2  , self.box_height), 'line_right_v') )
        #central vertical line
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, gui.SvgLine(0, h, 0 , h - line_length), 'line_central_v') )

        #right vertical line bottom
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, gui.SvgLine(w/2 - w_max_yes/2, h_yes, w/2 - w_max_yes/2, h), 'line_right_v_b') )
        
        #line bottom
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, gui.SvgLine(0, h,w/2 - w_max_yes/2, h), 'line_bottom') )

        #central box line
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, flow_chart_graphics.RomboidBox(-romboid_w/2, line_length, romboid_w, romboid_h, self.box_text_content), 'box') )


        txt_true = gui.SvgText(romboid_w/2, romboid_h/2 + line_length -3, 'true')
        txt_true.attributes['text-anchor'] = 'start'
        txt_true.attributes['dominant-baseline'] = 'baseline' #'middle'
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, txt_true, 'true'))

        txt_false = gui.SvgText(0, romboid_h + line_length, 'false')
        txt_false.attributes['text-anchor'] = 'end'
        txt_false.attributes['dominant-baseline'] = 'hanging' #'central'
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, txt_false, 'false'))


        self.children['line_top'].set_stroke(1, 'black')
        self.children['line_right_h'].set_stroke(1, 'black')
        self.children['line_central_v'].set_stroke(1, 'black')
        self.children['line_right_v'].set_stroke(1, 'black')
        self.children['line_right_v_b'].set_stroke(1, 'black')
        self.children['line_bottom'].set_stroke(1, 'black')

        self.children['box'].set_stroke(1, 'black')


class KRLStatementSwitch(KRLGenericParser):
    value_to_switch = "" #the switch(value_to_switch)
    pass_to_be_added = False
    first_switch_instruction = True
    actual_case_node = None

    def __init__(self, value_to_switch):
        self.value_to_switch = value_to_switch
        permissible_instructions = ['case','default','endswitch']
        permissible_instructions_dictionary = {k:v for k,v in instructions_defs.items() if k in permissible_instructions}
        KRLGenericParser.__init__(self, permissible_instructions_dictionary)

        self.box_text_content = 'SWITCH %s'%(self.value_to_switch)

    def append(self, w, *args, **kwargs):
        self.actual_case_node.append(w, *args, **kwargs)

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

            node = KRLStatementCase(condition)
            
            if self.first_switch_instruction:
                translation_result_tmp.append("if " + condition)
                KRLGenericParser.append(self, node)
            else:
                self.actual_case_node.yes_done = True
                translation_result_tmp.append("elif " + condition)
                self.actual_case_node.append(node)
            
            self.actual_case_node = node

            self.first_switch_instruction = False
            self.pass_to_be_added = True


        if instruction_name == 'default':
            if self.pass_to_be_added:
                translation_result_tmp.append('    pass')
            translation_result_tmp.append("else:")
            self.actual_case_node.yes_done = True

            
        if instruction_name == 'endswitch':
            self.pass_to_be_added = False
            self.stop_statement_found = True

        _translation_result_tmp, file_lines = KRLGenericParser.parse_single_instruction(self, code_line_original, code_line, instruction_name, match_groups, file_lines)
        if len(_translation_result_tmp):
            translation_result_tmp.extend(generic_regexes.indent_lines(_translation_result_tmp, 1))

        return translation_result_tmp, file_lines 

    def recalc_size_and_arrange_children(self):
        #remove all drawings prior to redraw it
        for k in self.drawings_keys:
            self.remove_child(self.children[k])
        self.drawings_keys = []

        w = max( len(self.box_text_content) * self.text_letter_width, 200 )
        h = self.box_height

        w_max = w
        #estimate self width
        for k in self._render_children_list:
            v = self.children[k]
            v.draw()
            w_max = max(w_max, float(v.attr_width))

        #set position for children
        for k in self._render_children_list:
            v = self.children[k]
            v.set_position(-float(v.attr_width)/2, h)
            h = h + float(v.attr_height) 

        gui._MixinSvgSize.set_size(self, w_max+self.margins*2, h+self.margins*2)

        self.set_viewbox(-w_max/2-self.margins, -self.margins, w_max+self.margins*2, h+self.margins*2)

        return w_max+self.margins*2, h+self.margins*2

    #overloads FlowInstruction.draw()
    def draw(self):
        self.box_height = 0
        w, h = self.recalc_size_and_arrange_children()

        #text
        txt = gui.SvgText(-w/2+10, +10, self.box_text_content)
        txt.attributes['text-anchor'] = 'start'
        txt.attributes['dominant-baseline'] = 'top' #'central'
        self.drawings_keys.append( KRLGenericParser.append(self, txt, 'text') )

class InterruptObject(flow_chart_graphics.FlowInstruction):
    number = 0
    is_global = False
    condition = ''
    instruction = ''
    def __init__(self, number, is_global, condition, instruction, *args, **kwargs):
        text = 'INTERRUPT DECL %s WHEN %s DO %s'%(number, condition, instruction)
        flow_chart_graphics.FlowInstruction.__init__(self, text, *args, **kwargs)
        self.number = number
        self.is_global = is_global
        self.condition = condition
        self.instruction = instruction


class KRLProcedureParser(KRLGenericParser):
    name = ""
    local_variables = None #dictionary variable_name:type
    global_variables = None #list of variable_name
    declared_interrupts = None #dictionary interrupt_number:InterruptObject
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
        self.local_variables = {}
        self.global_variables = []
        self.declared_interrupts = {}
        self.param_names = param_names
        self.callers_list = []
        self.calling_list = []

        self.box_text_content = 'PROCEDURE %s(%s)'%(name, ', '.join(param_names))
    
    def parse(self, file_lines):
        # Parses the file lines up to the procedure end

        translation_result = [] #here are stored the results of instructions translations from krl to python 
        _translation_result, file_lines = KRLGenericParser.parse(self, file_lines)
        if len(self.global_variables) > 0:
            translation_result.append("    global " + ', '.join(self.global_variables))
        translation_result.extend(_translation_result)

        return translation_result, file_lines
    
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

    #overloads FlowInstruction.draw()
    def draw(self):
        self.box_height = 50
        w, h = self.recalc_size_and_arrange_children()
        
        ellispe_width = max( len(self.box_text_content) * self.text_letter_width, 200 )

        #central box
        self.drawings_keys.append( self.append(flow_chart_graphics.EllipseBox(-ellispe_width/2, 0, ellispe_width, self.box_height, self.box_text_content), 'box') )

        self.children['box'].set_stroke(1, 'black')


class KRLFunctionParser(KRLProcedureParser):
    return_type = None
    def __init__(self, name, param_names, return_type):
        KRLProcedureParser.__init__(self, name, param_names)
        self.return_type = return_type

        self.box_text_content = 'FUNCTION %s %s(%s)'%(return_type, name, ', '.join(param_names))

        
