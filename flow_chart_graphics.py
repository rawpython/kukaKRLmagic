import remi
import remi.gui as gui


class FlowInstruction(gui.SvgSubcontainer):
    drawings_keys = None
    drawings_height = 200
    text_letter_width = 10
    def __init__(self, text = ''):
        super(FlowInstruction, self).__init__(0, 0, 200, 200)
        self.text = text
        self.drawings_keys = []
        self.draw()

    def recalc_size_and_arrange_children(self):
        #remove all drawings prior to redraw it
        for k in self.drawings_keys:
            self.remove_child(self.children[k])
        self.drawings_keys = []

        w = max( len(self.text) * self.text_letter_width, 200 )
        h = self.drawings_height

        w_max = w
        #estimate self width
        for k in self._render_children_list:
            v = self.children[k]
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
        self.drawings_height = 70
        w, h = self.recalc_size_and_arrange_children()
        
        line_length = 20
        #top vertical line
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, gui.SvgLine(0, 0, 0, line_length), 'line_top') )

        #central box
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, gui.SvgRectangle(-w/2, line_length, w, self.drawings_height-line_length), 'box') )

        #text
        txt = gui.SvgText(0, (self.drawings_height-line_length)/2 + line_length, self.text)
        #txt.attr_textLength = w-w*0.1
        #txt.attr_lengthAdjust = 'spacingAndGlyphs' # 'spacing'
        txt.attributes['text-anchor'] = 'middle'
        txt.attributes['dominant-baseline'] = 'middle' #'central'
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, txt, 'text') )

        self.children['line_top'].set_stroke(1, 'black')
        self.children['box'].set_stroke(1, 'black')
        self.children['box'].set_fill('transparent')


class Romboid(gui.SvgSubcontainer):
    # Centered at 0, 0
    def __init__(self, x, y, w, h):
        super(Romboid, self).__init__(x,y,w,h)
        self.append(gui.SvgLine(-w/2, 0, 0, -h/2), 'l1')
        self.append(gui.SvgLine(0, -h/2, w/2, 0), 'l2')
        self.append(gui.SvgLine(w/2, 0, 0, h/2), 'l3')
        self.append(gui.SvgLine(0, h/2, -w/2, 0 ), 'l4')
        self.set_viewbox(-w/2, -h/2, w, h)

    def set_stroke(self, w, color):
        self.children['l1'].set_stroke(w, color)
        self.children['l2'].set_stroke(w, color)
        self.children['l3'].set_stroke(w, color)
        self.children['l4'].set_stroke(w, color)


class ForBox(gui.SvgSubcontainer):
    # Centered at 0, 0
    def __init__(self, x, y, w, h):
        super(ForBox, self).__init__(x,y,w,h)
        corners_width = 30
        self.append(gui.SvgLine(-w/2, 0, -w/2+corners_width, -h/2), 'l1')
        self.append(gui.SvgLine(w/2-corners_width, -h/2, w/2, 0), 'l2')

        self.append(gui.SvgLine(w/2, 0, w/2-corners_width, h/2), 'l3')
        self.append(gui.SvgLine(-w/2+corners_width, h/2, -w/2, 0 ), 'l4')
        
        self.append(gui.SvgLine(-w/2+corners_width, -h/2, w/2-corners_width, -h/2), 'ltop')
        self.append(gui.SvgLine(-w/2+corners_width, h/2, w/2-corners_width, h/2), 'lbottom')
        self.set_viewbox(-w/2, -h/2, w, h)

    def set_stroke(self, w, color):
        self.children['l1'].set_stroke(w, color)
        self.children['l2'].set_stroke(w, color)
        self.children['l3'].set_stroke(w, color)
        self.children['l4'].set_stroke(w, color)
        self.children['ltop'].set_stroke(w, color)
        self.children['lbottom'].set_stroke(w, color)