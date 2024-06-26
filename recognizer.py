# $1 gesture recognizer
import xml.etree.ElementTree as ET
import os
import numpy as np
import math
from sklearn.preprocessing import StandardScaler
from scipy.signal import resample
from templates import Templates # TODO update to use this instead of TEMPLATE_APTH

TEST_PATH = "dataset/test"
TEMPLATE_PATH = "dataset/templates"
NUM_POINTS = 64 # 50 ?

class Parser:
    """via: lstm_demo.ipynb"""

    def parse_template(list):
        data = []
        for el in list:
            # print(el)
            label, points = el
            data.append(Parser.resample_path(label, points))
        return data
    
    def parse_xml_files(folderpath:str):
        data = []

        for root, subdirs, files in os.walk(folderpath):
            # if 'ipynb_checkpoint' in root:
            #     continue

            if len(files) > 0:
                for f in files:
                    if ".xml" in f:
                        fname = f.split('.')[0]
                        label = fname[:-2]
                        
                        xml_root = ET.parse(f'{root}/{f}').getroot()
                        
                        points = []
                        for element in xml_root.findall('Point'):
                            x = element.get('X')
                            y = element.get('Y')
                            points.append([x, y])
                            
                        points = np.array(points, dtype=float)
                        data.append(Parser.resample_path(label, points))
        
        return data

    # STEP 1
    def resample_path(label:str, points:np.array):
        data = []

        scaler = StandardScaler()
        points = scaler.fit_transform(points)
        resampled = resample(points, NUM_POINTS)
        
        data.append((label, resampled))

        return data

class Rect:
    """Helper class for Bbox"""
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height


class Recognizer:
    """via: https://depts.washington.edu/acelab/proj/dollar/index.html"""
    
    def __init__(self) -> None:
        self.phi = 0.5 * (-1.0 + math.sqrt(5.0)) # golden ratio
        self.angle_range = self.deg2Rad(45.0)
        self.angle_precision = self.deg2Rad(2.0)
        self.square_size = 250
        self.diagonal = math.sqrt(self.square_size * self.square_size + self.square_size * self.square_size)
        self.half_diagonal = 0.5 * self.diagonal
        self.origin = [0, 0]

    def load_templates(self):
        return Parser.parse_xml_files(TEMPLATE_PATH)

    def deg2Rad(self, d):
        return (d * math.pi / 180.0)

    # STEP 2
    def get_centroid(self, points):
        x = 0
        y = 0
        for i in range(0, len(points)):
            x += points[i][0]
            y += points[i][1]

        x /= len(points)
        y /= len(points)
        return (x,y)

    def get_indicative_angle(self, points):
        cx, cy = self.get_centroid(points)
        return math.atan2(cy - points[0][1], cx - points[0][0])

    def rotate_by(self, points, radians):
        cx, cy = self.get_centroid(points)
        cos = math.cos(radians)
        sin = math.sin(radians)
        new_points = []
        for i in range(0, len(points)):
            qx = (points[i][0] - cx) * cos - (points[i][1] - cy) * sin + cx
            qy = (points[i][0] - cx) * sin + (points[i][1] - cy) * cos + cy
            new_points.append([qx, qy])
        return new_points

    # STEP 3
    def get_bbox(self, points):
        max_x, max_y = np.max(points, 0)
        min_x, min_y = np.min(points, 0)
        rect = Rect(min_x, min_y, max_x - min_x, max_y - min_y)
        return rect

    def scale_to(self, points, size=250):
        b = self.get_bbox(points)
        new_points = []
        for i in range(0, len(points)):
            qx = points[i][0] * (size / b.width)
            qy = points[i][1] * (size / b.height)
            new_points.append([qx, qy]) 
        return new_points

    def translate_to(self, points, pt):
        cx, cy = self.get_centroid(points)
        new_points = []
        for i in range(0, len(points)):
            qx = points[i][0] + pt[0] - cx
            qy = points[i][1] + pt[1] - cy 
            new_points.append([qx, qy])
        return new_points

    # STEP 4
    def distance_at_best_angle(self, points, T, a, b, threshold):
        x1 = self.phi * a + (1.0 - self.phi) * b
        f1 = self.distance_at_angle(points, T, x1)
        x2 = (1.0 - self.phi) * a + self.phi * b
        f2 = self.distance_at_angle(points, T, x2)

        while np.abs(b - a) > threshold:
            if f1 < f2:
                b = x2
                x2 = x1
                f2 = f1
                x1 = self.phi * a + (1.0 - self.phi) * b
                f1 = self.distance_at_angle(points, T, x1)
            else:
                a = x1
                x1 = x2 
                f1 = f2 
                x2 = (1.0 - self.phi) * a + self.phi * b
                f2 = self.distance_at_angle(points, T, x2)
        return min(f1, f2)

    def distance_at_angle(self, points, T, radians):
        new_points = self.rotate_by(points, radians)
        return self.path_distance(new_points, T)

    def path_distance(self, pts1, pts2):
        d = 0.0
        for i in range(0, len(pts1)):
            d += self.get_distance(pts1[i], pts2[i])
        return d / len(pts1)

    def get_distance(self, p1, p2):
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        return math.sqrt(dx * dx + dy * dy)
    
    def preprocess(self, points): # create a "Unistroke"
        # NOTE: resampling already done during parsing
        radians = self.get_indicative_angle(points)
        points = self.rotate_by(points, -radians)
        points = self.scale_to(points, self.square_size)
        points = self.translate_to(points, self.origin)
        return points
    
    def preprocess_templates(self, templates) -> list:
        ts = []
        for template in templates:
            t_label, t_points = template[0] # template[0] # for unistroke-gestures.ipnby
            t_points = self.preprocess(t_points)
            ts.append((t_label, t_points))
        return ts

    # THE RECOGNIZER
    def recognize(self, points, templates=None) -> tuple[str, float]:
        b = np.inf

        points = self.preprocess(points) # pre

        result = "no_match"
        score = 0

        if templates == None:
            templates = self.load_templates()
        templates = self.preprocess_templates(templates) 

        for template in templates:
            t_label, t_points = template # template[0] # for unistroke-gestures.ipnby
            # t_points = self.preprocess(t_points) # pre # TODO (move out to Parser -> do only once)
            


            d = self.distance_at_best_angle(points, t_points, -self.angle_range, +self.angle_range, self.angle_precision)
            if d < b:
                b = d
                result = t_label
                score = 1.0 - b / self.half_diagonal
                # print(result, score)
            
        return (result, score)
    

def test_gestures():
    templates = Parser.parse_xml_files(TEMPLATE_PATH)
    # t = Templates()
    # templates =  Parser.parse_template(t.gestures)
    tests = Parser.parse_xml_files(TEST_PATH)
    recognizer = Recognizer()

    for gesture in tests:
        label, points = gesture[0]
        result, score = recognizer.recognize(points, templates)
        print(f"TEST:   [{label}]\n=\t[{result}] {score}\n")



if __name__ == "__main__":

    test_gestures()