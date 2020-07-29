import re
import os
import generic_regexes
import parser_instructions
import flow_chart_graphics
import remi.gui as gui

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
            if len(_translation_result_tmp):
                translation_result_tmp.extend(_translation_result_tmp)
        
        _translation_result_tmp, file_lines = parser_instructions.KRLGenericParser.parse_single_instruction(self, code_line_original, code_line, instruction_name, match_groups, file_lines)
        if len(_translation_result_tmp):
            translation_result_tmp.extend(_translation_result_tmp)

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

        gap_between_elements = 70
        #set position for children
        for k in self._render_children_list:
            v = self.children[k]
            v.set_position(-float(v.attr_width)/2, h + gap_between_elements)
            h = h + float(v.attr_height) + gap_between_elements

        gui._MixinSvgSize.set_size(self, w_max+self.margins*2, h+self.margins*2)

        self.set_viewbox(-w_max/2-self.margins, -self.margins, w_max+self.margins*2, h+self.margins*2)

        return w_max+self.margins*2, h+self.margins*2

    #overloads FlowInstruction.draw§()
    def draw(self):
        self.box_height = 50
        w, h = self.recalc_size_and_arrange_children()

        #central box
        self.drawings_keys.append( self.append(gui.SvgRectangle(-w/2, 0, w, h), 'box') )

        #text
        txt = gui.SvgText(0, self.box_height/2, self.box_text_content)
        txt.attributes['text-anchor'] = 'middle'
        txt.attributes['dominant-baseline'] = 'middle' #'central'
        self.drawings_keys.append( self.append(txt, 'text') )

        self.children['box'].set_stroke(1, 'black')
        self.children['box'].set_fill('transparent')



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

    #overloads FlowInstruction.draw§()
    def draw(self):
        self.box_height = 50
        w, h = self.recalc_size_and_arrange_children()
        
        title_box_width = max( len(self.box_text_content) * self.text_letter_width, 200 )

        self.drawings_keys.append( self.append(gui.SvgRectangle(-w/2, 0, title_box_width, self.box_height), 'title') )
        #central box
        self.drawings_keys.append( self.append(gui.SvgRectangle(-w/2, self.box_height, w, h), 'box') )

        #text
        txt = gui.SvgText(-w/2 + title_box_width/2, self.box_height/2, self.box_text_content)
        #txt.attr_textLength = w-w*0.1
        #txt.attr_lengthAdjust = 'spacingAndGlyphs' # 'spacing'
        txt.attributes['text-anchor'] = 'middle'
        txt.attributes['dominant-baseline'] = 'middle' #'central'
        self.drawings_keys.append( self.append(txt, 'text') )

        self.children['title'].set_stroke(1, 'black')
        self.children['title'].set_fill('lightyellow')

        self.children['box'].set_stroke(1, 'black')
        self.children['box'].set_fill('transparent')
            

class KRLModule(flow_chart_graphics.FlowInstruction):
    name = ''
    module_dat = None   # KRLDat instance
    module_src = None   # KRLSrc instance
    def __init__(self, module_name, dat_path_and_file = '', src_path_and_file = '', imports_to_prepend = ''):
        flow_chart_graphics.FlowInstruction.__init__(self)
        self.name = module_name
        if len(dat_path_and_file):
            self.module_dat = KRLModuleDatFileParser(dat_path_and_file)

            #it seems to have no relevance in flowcharts
            #self.module_dat.text = "DAT %s"%module_name
            #self.append(self.module_dat)
            
            file_lines = fread_lines(dat_path_and_file)
            translation_result, file_lines = self.module_dat.parse(file_lines)
            with open(os.path.dirname(os.path.abspath(__file__)) + "/%s.py"%self.name, 'w+') as f:
                f.write(imports_to_prepend)
                for l in translation_result:
                    f.write(l + '\n')
            
        if len(src_path_and_file):
            has_dat = not (self.module_dat is None)
            self.module_src = KRLModuleSrcFileParser(src_path_and_file)
            self.module_src.box_text_content = "SRC %s"%module_name
            self.append(self.module_src)
            file_lines = fread_lines(src_path_and_file)
            translation_result, file_lines = self.module_src.parse(file_lines)
            with open(os.path.dirname(os.path.abspath(__file__)) + "/%s.py"%self.name, ('a+' if has_dat else 'w+')) as f:
                if not has_dat:
                    f.write(imports_to_prepend)
                for l in translation_result:
                    f.write(l + '\n')
        self.box_text_content = self.name
        self.draw()

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

    #overloads FlowInstruction.draw§()
    def draw(self):
        self.box_height = 50
        w, h = self.recalc_size_and_arrange_children()

        #central box
        self.drawings_keys.append( self.append(gui.SvgRectangle(-w/2, 0, w, h), 'box') )

        #text
        txt = gui.SvgText(0, self.box_height/2, self.box_text_content)
        txt.attributes['text-anchor'] = 'middle'
        txt.attributes['dominant-baseline'] = 'middle' #'central'
        self.drawings_keys.append( self.append(txt, 'text') )

        self.children['box'].set_stroke(1, 'black')
        self.children['box'].set_fill('transparent')



