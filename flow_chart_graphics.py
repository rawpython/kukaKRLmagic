import remi
import remi.gui as gui


class FlowInstruction(gui.SvgSubcontainer):
    drawings_keys = None
    drawings_height = 200

    def __init__(self, text = ''):
        super(FlowInstruction, self).__init__(0, 0, 200, 200)
        self.text = text
        self.drawings_keys = []
        self.draw()

    def draw(self):
        
        #remove all drawings prior to redraw it
        for k in self.drawings_keys:
            self.remove_child(self.children[k])
        self.drawings_keys = []

        w = 200
        h = self.drawings_height

        for k in self._render_children_list:
            v = self.children[k]
            v.set_position(-w/2, h)
            h = h + float(v.attr_height) 

        gui._MixinSvgSize.set_size(self, w, h)

        #w = float(self.attr_width)
        #h = float(self.attr_height)

        self.set_viewbox(-w/2, 0, w, h)

        line_length = 30
        #top vertical line
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, gui.SvgLine(0, 0, 0, line_length), 'line_top') )

        #central box
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, gui.SvgRectangle(-w/2, 30, w, self.drawings_height-(line_length*2)), 'box') )

        #text
        txt = gui.SvgText(0, self.drawings_height/2, self.text)
        txt.attr_textLength = w
        txt.attr_lengthAdjust = 'spacingAndGlyphs' # 'spacing'
        txt.attributes['text-anchor'] = 'middle'
        txt.attributes['dominant-baseline'] = 'middle' #'central'
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, txt, 'text') )

        #bottom vertical line
        self.drawings_keys.append( gui.SvgSubcontainer.append(self, gui.SvgLine(0, self.drawings_height-line_length, 0, self.drawings_height), 'line_bottom') )

        self.children['line_top'].set_stroke(1, 'black')
        self.children['line_bottom'].set_stroke(1, 'black')
        self.children['box'].set_stroke(1, 'black')
        self.children['box'].set_fill('transparent')

