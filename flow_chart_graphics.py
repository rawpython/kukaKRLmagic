import remi
import remi.gui as gui


class FlowInstruction(gui.SvgSubcontainer):
    drawings_keys = None
    box_height = 200
    box_width = 200
    text_letter_width = 10
    box_text_content = ''
    margins = 5

    def __init__(self, box_text_content = ''):
        super(FlowInstruction, self).__init__(0, 0, 200, 200)
        self.box_text_content = box_text_content
        self.drawings_keys = []
        self.draw()
        self.css_font_family = 'courier'

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
            #v.set_position(-w_max/2, h)
            v.set_position(-float(v.attr_width)/2, h)
            h = h + float(v.attr_height) 

        gui._MixinSvgSize.set_size(self, w_max, h)

        self.set_viewbox(-w_max/2, 0, w_max, h)

        return w_max, h

    def draw(self):
        self.box_height = 70
        w, h = self.recalc_size_and_arrange_children()
        
        line_length = 20
        #top vertical line
        self.drawings_keys.append( self.append(gui.SvgLine(0, 0, 0, line_length), 'line_top') )

        #central box
        #self.drawings_keys.append( gui.SvgSubcontainer.append(self, gui.SvgRectangle(-w/2, line_length, w, self.box_height-line_length), 'box') )
        self.drawings_keys.append( self.append(RectangleBox(-w/2, line_length, w, self.box_height-line_length, self.box_text_content), 'box') )

        self.children['line_top'].set_stroke(1, 'black')
        self.children['box'].set_stroke(1, 'black')


class LabeledBox(gui.SvgSubcontainer):
    # Centered at 0, 0
    text = ''
    def __init__(self, x, y, w, h, text):
        super(LabeledBox, self).__init__(x,y,w,h)
        self.text = text
        
        txt = gui.SvgText(0, 0, self.text)
        #txt.attr_textLength = w-w*0.1
        #txt.attr_lengthAdjust = 'spacingAndGlyphs' # 'spacing'
        txt.attributes['text-anchor'] = 'middle'
        txt.attributes['dominant-baseline'] = 'middle' #'central'
        self.append(txt)

        self.set_viewbox(-w/2, -h/2, w, h)

    def set_stroke(self, w, color):
        for k,v in self.children.items():
            if type(v) in [gui.SvgLine, gui.SvgRectangle, gui.SvgEllipse, gui.SvgPolygon, gui.SvgPolyline]:
                v.set_stroke(w, color)

    def set_fill(self, color):
        for k,v in self.children.items():
            if type(v) in [gui.SvgRectangle, gui.SvgCircle, gui.SvgEllipse, gui.SvgPolygon, gui.SvgPolyline]:
                v.set_fill(color)


class RectangleBox(LabeledBox):
    # Centered at 0, 0
    def __init__(self, x, y, w, h, text):
        super(RectangleBox, self).__init__(x,y,w,h,text)
        self.append(gui.SvgRectangle(-w/2, -h/2, w, h), 'box')
        self.children['box'].set_fill('rgba(100,100,100, 0.01)')


class ProcedureCallBox(LabeledBox):
    # Centered at 0, 0
    def __init__(self, x, y, w, h, text):
        super(ProcedureCallBox, self).__init__(x,y,w,h,text)
        offset = 5
        self.append(gui.SvgRectangle(-w/2+offset, -h/2, w-offset*2, h), 'box_small')
        self.append(gui.SvgRectangle(-w/2, -h/2, w, h), 'box')
        self.children['box'].set_fill('rgba(100,100,100, 0.01)')
        
        
class EllipseBox(LabeledBox):
    # Centered at 0, 0
    def __init__(self, x, y, w, h, text):
        super(EllipseBox, self).__init__(x,y,w,h,text)
        self.append(gui.SvgEllipse(0, 0, w/2, h/2), 'box')
        self.children['box'].set_fill('rgba(100,255,100, 0.1)')
        

class RomboidBox(LabeledBox):
    # Centered at 0, 0
    def __init__(self, x, y, w, h, text):
        super(RomboidBox, self).__init__(x,y,w,h,text)
        poly = gui.SvgPolygon(10)
        poly.add_coord(-w/2, 0)
        poly.add_coord(0, -h/2)
        poly.add_coord(w/2, 0)
        poly.add_coord(0, h/2)
        poly.add_coord(-w/2, 0 )
        self.append(poly, 'box')
        self.children['box'].set_fill('rgba(255,255,0, 0.2)')
        

class ForBox(LabeledBox):
    # Centered at 0, 0
    def __init__(self, x, y, w, h, text):
        super(ForBox, self).__init__(x,y,w,h, text)
        corners_width = 30
        poly = gui.SvgPolygon(10)
        poly.add_coord(-w/2, 0) 
        poly.add_coord(-w/2+corners_width, -h/2)
        poly.add_coord(w/2-corners_width, -h/2)
        poly.add_coord(w/2, 0)
        poly.add_coord(w/2-corners_width, h/2)
        poly.add_coord(-w/2+corners_width, h/2)
        poly.add_coord(-w/2, 0 )
        
        self.append(poly, 'box')
        self.children['box'].set_fill('rgba(100,100,255, 0.1)')