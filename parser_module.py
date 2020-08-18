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


class MouseNavArea(gui.Container):
    zoom_absolute_position = 1.0
    def __init__(self, *args, **kwargs):
        gui.Container.__init__(self, *args, **kwargs)
        self.style['overflow'] = 'hidden'
        self.style['outline'] = '1px solid gray'
        self.style['zoom'] = '1.0'
        self.onmousemove.do(self.center_view)
        self.onwheel.do(self.zoom, js_prevent_default=True, js_stop_propagation=True)
        
        
    @gui.decorate_set_on_listener("(self, emitter, deltaY)")
    @gui.decorate_event_js("var params={};" \
            "params['deltaY']=event.deltaY;" \
            "remi.sendCallbackParam('%(emitter_identifier)s','%(event_name)s',params);")
    def onwheel(self, deltaY):
        """Called when the mouse cursor moves inside the Widget.

        Args:
            deltaY (float): the relative scroll value
        """
        return (deltaY,)

    def center_view(self, emitter, x, y):
        offset = 100

        x = float(x)
        wself = float(gui.from_pix(self.css_width))

        y = float(y)
        hself = float(gui.from_pix(self.css_height))
        for c in self.children.values():
            c.css_position = 'relative'
            wchild = wself
            try:
                wchild = gui.from_pix(c.css_width)
            except:
                wchild = float(c.attr_width)
            wchild = wchild * self.zoom_absolute_position
            if wself < wchild:
                left = offset/2 -(wchild+offset-wself) * (x/wself)
                #left = left + offset/2 - offset * (x/wself)
                c.css_left = gui.to_pix( left / self.zoom_absolute_position )
            
            hchild = hself
            try:
                hchild = gui.from_pix(c.css_height)
            except:
                hchild = float(c.attr_height)
            hchild = hchild * self.zoom_absolute_position
            if hself < hchild:
                top = offset/2-(hchild+offset-hself) * (y/hself)
                #top = top + offset/2 - offset * (y/hself)
                c.css_top = gui.to_pix( top / self.zoom_absolute_position )
        
    def zoom(self, emitter, relative_value):
        self.zoom_absolute_position = min(max(0, self.zoom_absolute_position + float(relative_value)*0.0003), 2.0)
        self.set_zoom( self.zoom_absolute_position )

    def set_zoom(self, value):
        self.zoom_absolute_position = value
        for c in self.children.values():
            c.style['zoom'] = str(value)


class KRLModuleSrcFileParser(parser_instructions.KRLGenericParser, gui.HBox):
    file_path_name = ''   # the str path and file
    def __init__(self, file_path_name):
        # read all instructions, parse and collect definitions
        self.krl_procedures_and_functions_list = []
        self.indent_comments = False
        self.file_path_name = file_path_name
        permissible_instructions = ['procedure begin', 'function begin']
        permissible_instructions_dictionary = {k:v for k,v in parser_instructions.instructions_defs.items() if k in permissible_instructions}
        parser_instructions.KRLGenericParser.__init__(self, permissible_instructions_dictionary)

        gui.HBox.__init__(self)
        self.css_align_items = 'flex-start'
        self.append(gui.ListView(width=300), 'list')
        self.append(MouseNavArea(width=800, height=800), 'container')
        
        self.children['list'].onselection.do(self.on_proc_list_selected)
        
    def on_proc_list_selected(self, widget, selected_key):
        w = gui.from_pix(self.children['container'].css_width)
        h = gui.from_pix(self.children['container'].css_height)
        self.children['container'].append(widget.children[selected_key].node, 'proc_to_view')
        widget.children[selected_key].node.draw()
        best_zoom = min(w/float(widget.children[selected_key].node.attr_width), h/float(widget.children[selected_key].node.attr_height))
        self.children['container'].set_zoom(best_zoom)


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
            #self.append(node)
            li = gui.ListItem(node.name)
            li.node = node
            self.children['list'].append(li)
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
            li = gui.ListItem(node.name)
            li.node = node
            self.children['list'].append(li)
            _translation_result_tmp, file_lines = node.parse(file_lines)
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
        

class KRLModule(gui.VBox):
    name = ''
    module_dat = None   # KRLDat instance
    module_src = None   # KRLSrc instance
    def __init__(self, module_name, dat_path_and_file = '', src_path_and_file = '', imports_to_prepend = '', *args, **kwargs):
        super(KRLModule, self).__init__(*args, **kwargs)
        self.append(gui.Label("MODULE: %s"%module_name))
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
            self.append(self.module_src)
            file_lines = fread_lines(src_path_and_file)
            translation_result, file_lines = self.module_src.parse(file_lines)
            with open(os.path.dirname(os.path.abspath(__file__)) + "/%s.py"%self.name, ('a+' if has_dat else 'w+')) as f:
                if not has_dat:
                    f.write(imports_to_prepend)
                for l in translation_result:
                    f.write(l + '\n')

        


