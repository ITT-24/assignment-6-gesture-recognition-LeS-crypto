from recognizer import Parser, Recognizer
from templates import Templates
import pyglet
# gesture input program for first task

""" 01
- build interface for user to enter gestures to test recognizer
- [x] (1P) Gesture entry user interface
"""
MENU_WIDTH = 200
WIDTH = 700 + MENU_WIDTH
HEIGHT = 700
window = pyglet.window.Window(WIDTH, HEIGHT)

# ----- HELPERS ----- #
RADIUS = 2
COLOR = (196, 183, 203)

class Path:
    def __init__(self) -> None:
        self.path = []
        self.circles = []
        self.line = []
        self.batch = pyglet.graphics.Batch()
        self.reco = Recognizer()

        self.t = Templates()
        # print(self.t.gestures)
        self.templates = Parser.parse_template(self.t.gestures)
        # print("star", self.t.star)
        # self.templates = Parser.resample_path("star", self.t.star)

        # self.templates = Parser.parse_xml_files(TEMPLATE_PATH)
    
    def add_point(self, x, y):
        p = [x, y]

        self.path.append(p)        
        self.create_path_line(p)

    def create_path_line(self, point):
        """Create a line following the mouse path for visual drawing feedback"""
        self.create_circle(point)

        if len(self.path) >= 2:
            self.create_connect_line()

    def create_circle(self, point):
        c = pyglet.shapes.Circle(x=point[0], y=point[1], radius=RADIUS, 
                                color=(196, 183, 203), batch=self.batch)
        self.circles.append(c)
    
    def create_connect_line(self):
        """Create a line to connect the last two points: p1---p2"""
        p1 = self.circles[-2]
        p2 = self.circles[-1]
        l = pyglet.shapes.Line(p1.x, p1.y, p2.x, p2.y, width=RADIUS, 
                               color=COLOR, batch=self.batch)
        self.line.append(l)
        pass

    
    def recognize_gesture(self):
        """Use the $1 recognizer on the path"""
        print(f"Recognizing the gesture...\t -> {len(self.path)}")
        _, points = Parser.resample_path("none", self.path)[0]

        result, score = self.reco.recognize(points, self.templates)
        area.set_gesture_label(f"{result}, {score} ")

    def reset(self):
        self.path = []
        self.circles = []
        self.line = []
        area.set_gesture_label("...")


TEMPLATE_PATH = "dataset/templates"
MENU_BG = (206, 196, 212) # (216, 208, 221) # (196, 183, 203) # little darker
SEP_COL = (94, 86, 90)
Y_OFFSET = 15

class Area:
    def __init__(self):
        self.batch = pyglet.graphics.Batch()
        middle_x = (WIDTH - MENU_WIDTH) / 2
        self.label = pyglet.text.Label("Drawing Area", x=middle_x, y=HEIGHT-Y_OFFSET, 
                                       anchor_x="center", anchor_y="center", batch=self.batch)
        self.gesture = pyglet.text.Label("...", x=middle_x, y=0+Y_OFFSET,
                                        anchor_x="center", batch=self.batch)
        
    def set_gesture_label(self, gesture:str):
        self.gesture.text = gesture


class Menu:
    """A menu showing the different possible gestures"""
    def __init__(self) -> None:
        self.batch = pyglet.graphics.Batch()
        self.templates = path.templates
        self.items = []
        self.labels = []
        self.lines = []
        self.create_menu()

    def create_menu(self):
        x = WIDTH - MENU_WIDTH
        bg = pyglet.shapes.Rectangle(x, 0, MENU_WIDTH, HEIGHT, color=MENU_BG, batch=self.batch)
        separator = pyglet.shapes.Line(x, 0, x, HEIGHT, width=5, color=SEP_COL, batch=self.batch)
        
        self.items.append(bg)
        self.items.append(separator)

        self.create_gesture_info()

    def create_gesture_info(self):
        off = 100
        idx = 1
        for template in self.templates:
            label, path = template[0]
            self.create_label(label, off )
            self.create_gesture_lines(path, off)
            
            off += 110

    def create_label(self, label, off):
        middle_x =WIDTH + (MENU_WIDTH / 2) - MENU_WIDTH
        y = 0 + off - 50
        l = pyglet.text.Label(label, x=middle_x, y=y, color=(0, 0, 0, 255),
                                anchor_x="center", batch=self.batch)
        self.labels.append(l)

    def create_gesture_lines(self, points, off):
        """Create a line following a gesture"""
        for i in range(0, len(points)-1):
            p1 = points[i]
            p2 = points[i+1]
            x1 = (p1[0] * 20) + WIDTH-MENU_WIDTH/2
            y1 = (p1[1] * -20) + off
            x2 = (p2[0] * 20) + WIDTH-MENU_WIDTH/2
            y2 = (p2[1] * -20) + off
            l = pyglet.shapes.Line(x1, y1, x2, y2, width=RADIUS, 
                                color=SEP_COL, batch=self.batch)
            self.lines.append(l)


# ----- INIT ----- #

path = Path()
menu = Menu()
area = Area()

# ----- WINDOW INTERACTION ----- #

@window.event
def on_draw():
    window.clear()

    path.batch.draw()
    menu.batch.draw()
    area.batch.draw()

@window.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.ESCAPE:
        window.close()
    if symbol == pyglet.window.key.Q:
        window.close()

@window.event
def on_mouse_press(x, y, button, modifiers):
    """Start "tracking" the gesture being drawn"""
    if button == pyglet.window.mouse.LEFT:
        path.reset()
    # ??: get better/more points


@window.event
def on_mouse_release(x, y, button, modifiers):
    """Stop tracking"""
    if button == pyglet.window.mouse.LEFT:
        path.recognize_gesture()


@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    """ Sample points from the drawing. dx/dy = distance traveled from last point"""
    if buttons & pyglet.window.mouse.LEFT:
        path.add_point(x, y)

# ----- RUN APP ----- #

if __name__ == "__main__":
    pyglet.app.run()