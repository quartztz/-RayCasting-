import numpy as np
import os

PATH = os.path.abspath(os.getcwd())
print(PATH)

LOAD_MAP_FROM_FILE = True
BOUNDARIES_AROUND = False

# colors

BG = "#000015"
FG = "#cccddc"

# screen

SIZE = (600, 300)
SCALE = int(np.sqrt(SIZE[0]*2*SIZE[0]))
FULLSCREEN = False

FPS = 30

# movement

VIEW_ANGLE = 1/3
CURR_ANGLE = 1/8
MVMT_SPEED = 5
TURN_SPEED = 0.10
VIEW_PLUS = 1/64

# rendering

DRAW_DISTANCE = 300
LIGHT_FALLOFF = 50
RESOLUTION = 30

# map file loading 

def loadMap(): 
	
	data = []

	mapPATH = PATH + "\\map.txt"
	with open(mapPATH) as f: 
		lines = f.readlines()

	for line in lines: 
		s = line.split(" | ")
		s = [int(x) for x in s]
		data.append(s)
	
	return data