import re
import os
import generic_regexes

"""
    This parses dat and src files
        analyzed instructions
"""

instructions_defs = {
    'procedure end':        generic_regexes.a_line_containing("END"),
    'function end':         generic_regexes.a_line_containing("ENDFCT"),
    'function return':      generic_regexes.a_line_containing("RETURN +" + "(.+)?"),

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

    'variable assignment':  generic_regexes.a_line_containing( generic_regexes.global_def + "(DECL +)?(?:" + generic_regexes.variable_name + " +)?" + generic_regexes.variable_name + " *= *([^#]+)" ),
    'variable declaration': generic_regexes.a_line_containing( generic_regexes.global_def + "(DECL +)?([^ =\(]+) +(([^ =\(]+"+generic_regexes.c(generic_regexes.index_3d)+"?)( *, *[^ =]+" + generic_regexes.c(generic_regexes.index_3d) + "?)*)" ),

    'function call':        generic_regexes.a_line_containing( generic_regexes.variable_name + " *\( *(.*) *\)" ),

    'enum':                 generic_regexes.a_line_containing( generic_regexes.global_def + "ENUM +([^ ]+) +.*" ),

    'wait sec':             generic_regexes.a_line_containing( "WAIT +SEC +" + generic_regexes.int_or_real_number ),

    'wait for':             generic_regexes.a_line_containing( "WAIT +FOR +" + "([^#]+)" ),

    'ext':                  generic_regexes.line_begin + "EXTP? +([^ \(]+) *\(",
    'extfct':               generic_regexes.line_begin + "EXTFCTP? +([^ ]+) +([^ \(]+) *\(",

    'continue':             generic_regexes.a_line_containing( "CONTINUE" ), #in KRL Prevention of advance run stops.
}


class KRLStatementSwitch(KRLGenericParser):
    value_to_switch = "" #the switch(value_to_switch)
    def __init__(self, value_to_switch):
        self.value_to_switch = value_to_switch
        permissible_instructions = ['function return','halt','switch','lin','ptp','circ','if begin','for begin','while begin','repeat','loop begin','interrupt decl','interrupt on','interrupt off','trigger distance','trigger path','variable assignment','function call','wait sec','wait for','continue',]
        permissible_instructions_dictionary = {k:v for k,v in d.iteritems() if k in permissible_instructions}
        KRLGenericParser.__init__(self, permissible_instructions_dictionary)

    def parse_single_instruction(code_line_original, code_line, instruction_name, match_groups):
        translation_result_tmp = []

        return translation_result_tmp, file_lines 


class KRLProcedureParser(KRLGenericParser):
    name = ""
    param_names = None
    callers_list = None
    calling_list = None
    def __init__(self, name, param_names):
        permissible_instructions = ['procedure end','function end','function return','halt','switch','lin','ptp','circ','struc declaration','if begin','for begin','while begin','repeat','loop begin','interrupt decl','interrupt on','interrupt off','trigger distance','trigger path','variable assignment','variable declaration','function call','enum','wait sec','wait for','continue',]
        permissible_instructions_dictionary = {k:v for k,v in d.iteritems() if k in permissible_instructions}
        KRLGenericParser.__init__(self, permissible_instructions_dictionary)
        self.name = name
        self.param_names = param_names
        self.callers_list = []
        self.calling_list = []

    def parse_single_instruction(code_line_original, code_line, instruction_name, match_groups, file_lines):
        translation_result_tmp = []

        self.declarations_done = self.declarations_done or instruction_name in ['function return','halt','switch','lin','ptp','circ','struc declaration','if begin','for begin','while begin','repeat','loop begin','interrupt decl','interrupt on','interrupt off','trigger distance','trigger path','variable assignment','function call','enum','wait sec','wait for','continue',]
        if instruction_name == 'procedure end': 
            break
        
        if instruction_name == 'function end':
            break

        if instruction_name == 'function return':
            value = match_groups[0]
            translation_result_tmp.append("return" if value is None else ("return " + value))

        if instruction_name == 'halt':
            translation_result_tmp.append("assert(False) # halt")

        if instruction_name == 'switch':
            value_to_switch = match_groups[0]
            node = KRLStatementSwitch( value_to_switch )
            translation_result_tmp, file_lines = node.parse()

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
        if instruction_name == 'if begin':
        if instruction_name == 'for begin':
        if instruction_name == 'while begin':
        if instruction_name == 'repeat':
        if instruction_name == 'loop begin':
        if instruction_name == 'interrupt decl':
        if instruction_name == 'interrupt on':
        if instruction_name == 'interrupt off':
        if instruction_name == 'trigger distance':
        if instruction_name == 'trigger path':
        if instruction_name == 'variable assignment':
        if instruction_name == 'variable declaration':
        if instruction_name == 'function call':
        if instruction_name == 'enum':
        if instruction_name == 'wait sec':
        if instruction_name == 'wait for':
        if instruction_name == 'continue':
        
        return translation_result_tmp, file_lines


class KRLFunctionParser(KRLProcedureParser):
    return_type = None
    def __init__(self, name, param_names, return_type, file_lines):
        KRLProcedureParser.__init__(self, name, param_names, file_lines)
        self.return_type = return_type
        
