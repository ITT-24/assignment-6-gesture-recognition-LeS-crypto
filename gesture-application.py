from pysinewave import SineWave
from recognizer import Parser
from templates import Templates
import pyglet
from time import sleep
import keras
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
from scipy.signal import resample
import os
# application for task 3

"""03
- very simple 2D application (game, controller, quick start menu)
- program is controlled with gestures drawn by user
- support at least 3 distinct gestures

- [x] (1P) Gesture input works.
- [ ] (2P) Functionality and aesthetics of the application.
- [x] (2P) Three gestures are distinguished robustly.
"""

"""
'Draw' music: (loosely inspired by https://typatone.com/)
"""
MENU_WIDTH = 200
SONG_HEIGHT = 100
WIDTH = 700 + MENU_WIDTH
HEIGHT = 700 + SONG_HEIGHT
window = pyglet.window.Window(WIDTH, HEIGHT)

MODEL_PATH = "gesture-recognizer.keras"
INFO_TEXT = "play full song with p // reset with r"

RADIUS = 2
COLOR = (196, 183, 203)

TEMPLATE_DIR = "dataset/test-own"
MENU_BG = (206, 196, 212) # (216, 208, 221) # (196, 183, 203) # little darker
M_SEP_COL = (94, 86, 90)
DISPLAY_BG = (195, 212, 175)
D_SEP_COL = (115, 131, 93)
Y_OFFSET = 15

NUM_POINTS = 50

SCALE = 20
VOLUME = -5

class Path:
    def __init__(self) -> None:
        self.path = []
        self.circles = []
        self.line = []
        self.batch = pyglet.graphics.Batch()
        self.scaler = StandardScaler()
        self.load()
    
    def load(self):
        self.model = keras.models.load_model(MODEL_PATH, compile=False)

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
    
    def recognize_gesture(self):
        """Use the $1 recognizer on the path"""
        print(f"Recognizing the gesture...\t -> {len(self.path)}")

        # parse path into right data shape
        points = np.array(self.path)

        points = self.scaler.fit_transform(points)
        test = resample(points, NUM_POINTS)
        print(test.shape)

        predictions = self.model.predict(np.array([test]))
        prediction = np.argmax(predictions)
        print("pred", prediction)

        correct_gesture = Tone.play_tone(prediction)
        if correct_gesture:
            song.add_gesture_to_song(test, prediction)
            area.info.text = INFO_TEXT
        else:
            area.info.text = "oops... don't know this one"


    def reset(self):
        self.path = []
        self.circles = []
        self.line = []

class Area:
    def __init__(self):
        self.batch = pyglet.graphics.Batch()
        middle_x = (WIDTH - MENU_WIDTH) / 2
        self.label = pyglet.text.Label("Drawing Area", x=middle_x, y=HEIGHT-Y_OFFSET, 
                                       anchor_x="center", anchor_y="center", batch=self.batch)
        self.info = pyglet.text.Label(INFO_TEXT, x=middle_x, y=SONG_HEIGHT+Y_OFFSET,
                                        anchor_x="center", batch=self.batch)
        


class SongDisplay:
    def __init__(self) -> None:
        self.batch = pyglet.graphics.Batch()
        self.items = []
        self.create_display()
        self.lines = []
        self.notes = []

    def create_display(self):
        bg = pyglet.shapes.Rectangle(0, 0, WIDTH, SONG_HEIGHT, color=DISPLAY_BG, batch=self.batch)
        separator = pyglet.shapes.Line(0, SONG_HEIGHT,WIDTH, SONG_HEIGHT, width=5, color=M_SEP_COL, batch=self.batch)
        
        self.items.append(bg)
        self.items.append(separator)

    def add_gesture_to_song(self, points, prediction, offset=50):
        """Create a line gesture to add to the created "song"."""
        off = offset * len(self.notes) + offset
        print("off", off)
        for i in range(0, len(points)-1):
            p1 = points[i]
            p2 = points[i+1]
            x1 = (p1[0] * SCALE/2) + off 
            y1 = (p1[1] * SCALE/2) + SONG_HEIGHT / 2
            x2 = (p2[0] * SCALE/2) + off
            y2 = (p2[1] * SCALE/2) + SONG_HEIGHT / 2
            l = pyglet.shapes.Line(x1, y1, x2, y2, width=RADIUS, 
                                color=M_SEP_COL, batch=self.batch)
            self.lines.append(l)
        self.notes.append(prediction)

    def play_full(self):
        for note in self.notes:
            Tone.play_tone(note)

    def reset(self):
        Tone.waves = []
        song.notes = []
        song.lines = []

class Menu:
    """A menu showing the different possible gestures"""

    def __init__(self) -> None:
        self.batch = pyglet.graphics.Batch()
        self.templates = []
        self.items = []
        self.labels = []
        self.lines = []
        self.create_menu()

    def create_menu(self):
        x = WIDTH - MENU_WIDTH
        bg = pyglet.shapes.Rectangle(x, SONG_HEIGHT, MENU_WIDTH, HEIGHT, color=MENU_BG, batch=self.batch)
        separator = pyglet.shapes.Line(x, SONG_HEIGHT, x, HEIGHT, width=5, color=M_SEP_COL, batch=self.batch)
        
        self.items.append(bg)
        self.items.append(separator)

        gestures = self.load_gestures()
        self.create_gesture_info(gestures)

    def load_gestures(self):
        """Load (working) gestures to display for reference"""
        working_gestures = ["circle", "pigtail", "star", "v"]
        i = 0
        data = []

        for root, subdirs, files in os.walk(TEMPLATE_DIR):
            for f in files:
                if i >= len(working_gestures):
                    continue
                if f"{working_gestures[i]}-1.csv" == f:
                    fname = f.split('.')[0]
                    label = fname[:-2]

                    points = pd.read_csv(f"dataset/test-own/{f}")
                    points = points.loc[:, ~points.columns.str.contains('^Unnamed')]
                    points = points.to_numpy(dtype=float)
                        
                    scaler = StandardScaler()
                    points = scaler.fit_transform(points)
                    resampled = resample(points, NUM_POINTS)
                    
                    data.append((label, resampled))
                    i += 1
        return data


    def create_gesture_info(self, templates):
        # TODO update
        off = 100
        idx = 1
        for template in templates:
            label, path = template
            self.create_label(label, off )
            self.create_gesture_lines(path, off)
            
            off += 110

    def create_label(self, label, off):
        middle_x =WIDTH + (MENU_WIDTH / 2) - MENU_WIDTH
        y = 0 + off - 50 + SONG_HEIGHT
        l = pyglet.text.Label(label, x=middle_x, y=y, color=(0, 0, 0, 255),
                                anchor_x="center", batch=self.batch)
        self.labels.append(l)

    def create_gesture_lines(self, points, off):
        """Create a line following a gesture"""
        for i in range(0, len(points)-1):
            p1 = points[i]
            p2 = points[i+1]
            x1 = (p1[0] * SCALE) + WIDTH-MENU_WIDTH/2
            y1 = ((p1[1] * SCALE) + off ) + SONG_HEIGHT
            x2 = (p2[0] * SCALE) + WIDTH-MENU_WIDTH/2
            y2 = ((p2[1] * SCALE) + off ) + SONG_HEIGHT
            l = pyglet.shapes.Line(x1, y1, x2, y2, width=RADIUS, 
                                color=M_SEP_COL, batch=self.batch)
            self.lines.append(l)


class Tone:
    """Creates sine waves that emulate the gesture. Uses: https://pypi.org/project/pysinewave/"""
    waves =  []

    def test_wave():
        sineWave = SineWave(pitch=12, pitch_per_second=10) 
        sineWave.set_volume(-1)
        sineWave.play()
        sleep(2)
        sineWave.set_pitch(-5)
        sleep(3)
        sineWave.stop()

    def play_tone(prediction:int)-> bool:
        match(prediction):
            case 1: # v / check
                Tone.v_wave()
            case 4: # pigtail
                Tone.pig_wave()
            case 7: # delete
                pass
            case 8: # circle
                Tone.circle_wave()
            case 11: # x
                pass
            case 12: # star
                Tone.star_wave()
            case 14: # caret/arrow
                pass
            case _:
                print("oops")
                Tone.oops_wave()
                return False
        return True

    def v_wave():
        wave = SineWave(pitch=12, pitch_per_second=60)
        wave.set_volume(VOLUME)
        wave.play()
        sleep(1)
        wave.set_pitch(0)
        sleep(1)
        wave.set_pitch(12)
        sleep(2)
        wave.stop()

    def pig_wave():
        wave = SineWave(pitch=-4, pitch_per_second=120)
        wave.set_volume(VOLUME)
        wave.play()
        sleep(1)
        wave.set_pitch(8)
        sleep(1)
        wave.set_pitch(-2)
        sleep(2)
        wave.stop()

    def circle_wave():
        wave = SineWave(pitch=6, pitch_per_second=10)
        wave.set_volume(VOLUME)
        wave.play()
        sleep(1)
        wave.set_pitch(-6)
        sleep(1)
        wave.set_pitch(6)
        sleep(2)
        wave.stop()

    def star_wave():
        p = 6
        wave = SineWave(pitch=-p, pitch_per_second=20)
        wave.set_volume(VOLUME)
        wave.play()
        sleep(1)
        wave.set_pitch(p * 2) # top mid
        sleep(1)
        wave.set_pitch(-p) # bot r
        sleep(1)
        wave.set_pitch(p -2 ) # l
        sleep(1)
        wave.set_pitch(p) # r
        sleep(1)
        wave.set_pitch(-p - 2) # bot r
        sleep(2)
        wave.stop()

    def oops_wave():
        wave = SineWave(pitch=4, pitch_per_second=150)
        wave.set_volume(VOLUME)
        wave.play()
        sleep(0.5)
        wave.set_pitch(-2)
        sleep(1)
        wave.stop()

# TODO: show labels


# ----- INIT ----- #

path = Path()
menu = Menu()
area = Area()
song = SongDisplay()


# ----- WINDOW INTERACTION ----- #

@window.event
def on_draw():
    window.clear()

    path.batch.draw()
    menu.batch.draw()
    area.batch.draw()
    song.batch.draw()

@window.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.ESCAPE:
        window.close()
    elif symbol == pyglet.window.key.Q:
        window.close()
    elif symbol == pyglet.window.key.T:
        Tone.test_wave()
    elif symbol == pyglet.window.key.P:
        song.play_full()
    elif symbol == pyglet.window.key.R:
        song.reset()

@window.event
def on_mouse_press(x, y, button, modifiers):
    """Start "tracking" the gesture being drawn"""
    if button == pyglet.window.mouse.LEFT:
        path.reset()


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