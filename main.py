import pygame
import pygame.display as display
import pygame.draw as draw
from consts import *
import numpy as np

WIN = display.set_mode(SIZE)
SETUP = WIN.subsurface(pygame.Rect(0, 0, SIZE[0] // 2, SIZE[1]))
GAME = WIN.subsurface(pygame.Rect(SIZE[0] // 2, 0, SIZE[0] // 2, SIZE[1]))
if FULLSCREEN: display.toggle_fullscreen()

CLOCK = pygame.time.Clock()
FPS = 60

pygame.font.init()
FONT = pygame.font.SysFont("consolas", 20)

chosen = True

# realm of the Setup

class App:

	def __init__(self, res):

		# 'drawing' before starting the simulation, then should be set to 'simulating' or something

		self.state = "drawing"
		self.res = res
		self.BC = BoundaryContainer(self)
		self.S = None

	def handleEvents(self):

		for event in pygame.event.get():

			if event.type == pygame.QUIT:
				pygame.quit()
				return True

			elif event.type == pygame.MOUSEBUTTONDOWN:
				self.BC.event(event.pos, event.button)

			elif event.type == pygame.KEYDOWN:
				if self.state == "drawing":
					self.S = Source(self.res, self)
					self.renderer = Renderer(self.S)
					self.state = "simulating"
	
	def getInputs(self):

		KEYS = pygame.key.get_pressed()
		
		global CURR_ANGLE, VIEW_ANGLE, LIGHT_FALLOFF

		# angle movement
		
		if KEYS[pygame.K_LEFT]:
			CURR_ANGLE -= TURN_SPEED
			self.S.update()
		if KEYS[pygame.K_RIGHT]: 
			CURR_ANGLE += TURN_SPEED
			self.S.update()

		# FOV increase
		
		if KEYS[pygame.K_UP]: 
			tempAngle = VIEW_ANGLE + VIEW_PLUS
			VIEW_ANGLE = min(2, tempAngle)
			self.S.update()
		if KEYS[pygame.K_DOWN]: 
			tempAngle = VIEW_ANGLE - VIEW_PLUS
			VIEW_ANGLE = max(0, tempAngle)
			self.S.update()

		# light control

		if KEYS[pygame.K_PLUS]: 
			LIGHT_FALLOFF += 5
			print(LIGHT_FALLOFF)
			self.S.update()
		if KEYS[pygame.K_MINUS]: 
			LIGHT_FALLOFF -= 5
			print(LIGHT_FALLOFF)
			self.S.update()

		# source position

		if KEYS[pygame.K_w]:
			self.S.update( (self.S.pos[0], self.S.pos[1] - MVMT_SPEED) )
		if KEYS[pygame.K_s]: 
			self.S.update( (self.S.pos[0], self.S.pos[1] + MVMT_SPEED) )
		if KEYS[pygame.K_a]: 
			self.S.update( (self.S.pos[0] - MVMT_SPEED, self.S.pos[1]) )
		if KEYS[pygame.K_d]: 
			self.S.update( (self.S.pos[0] + MVMT_SPEED, self.S.pos[1]) )

	def returnState(self):

		return self.state

	def render(self, font, t, c, p): 

		txt = font.render(t, 0, c)
		WIN.blit(txt, p)

	def run(self):

		while True:

			WIN.fill(BG)
			if self.handleEvents():
				break
			if self.state == 'simulating': 
				self.getInputs()
				self.S.show()
				self.renderer.show()
			self.BC.show()
			CLOCK.tick(FPS)
			display.flip()

class Wall:

	def __init__(self, pos: tuple):

		self.s = pos[0]
		self.e = pos[1]

	def render(self):

		draw.aaline(SETUP, FG, self.s, self.e)

	def getVector(self): 

		t = pygame.Vector2(self.s[0] - self.e[0], self.s[1] - self.e[1])
		t.normalize_ip()
		return t

	def __str__(self): 

		return f"this is a wall at ({self.s}, {self.e})"

class BoundaryContainer:

	def __init__(self, App, BoundariesAround : bool = False):

		self.App = App
		self.lines = []
		if BoundariesAround: 
			self.populate()
		self.chosen = True
		self.pos = []

	def populate(self): 
		corners = ((0, 0), (0, SIZE[0] - 1), (SIZE[0] + 1, SIZE[0] + 1), (SIZE[0] + 1, 0), (0, 0))
		for i in range(4):
			l = Wall((corners[i], corners[i+1]))
			self.lines.append(l)

	def event(self, eventPos, eventButton):

		if eventButton == 1: 

			if self.chosen:
				self.pos.append(eventPos)
				self.chosen = False
			else:
				self.pos.append(eventPos)
				self.lines.append(Wall(self.pos))
				self.pos = []
				if self.App.S: 
					self.App.S.update()
				self.chosen = True

		elif eventButton == 3:
			
			self.lines = []
			self.App.S.update()


	def show(self):

		draw.line(WIN, FG, (SIZE[0]//2, 0), (SIZE[0]//2, SIZE[1]), width = 3)

		for line in self.lines:
			line.render()

	def getAppState(self):

		return self.App.returnState()

class Source:

	def __init__(self, res, App):

		self.App = App
		self.res = res
		self.pos = (SETUP.get_width() // 2, SETUP.get_height() // 2)
		self.rays = self.getRays(res)
		self.lines = self.generateLines()

	def getRays(self, res):

		space = np.linspace(0, VIEW_ANGLE * np.pi, res) + CURR_ANGLE
		LENGTH = 1
		r = []

		for i in space:
			x = LENGTH * round(np.cos(i), 3)
			y = LENGTH * round(np.sin(i), 3)
			v = pygame.Vector2(x, y)
			r.append(v)

		return r

	def generateLines(self):

		ls = []

		for r in self.rays:
			l = LineR(r, self)
			ls.append(l)

		return ls

	def show(self):
		
		draw.circle(SETUP, FG, self.pos, 5)
		for line in self.lines:
			if line.hit:
				line.show()

	def update(self, pos = None):

		pos = self.pos if pos == None else pos

		self.rays = self.getRays(self.res)
		self.lines = self.generateLines()

		self.pos = pos
		for line in self.lines:
			line.update(pos)

	def getDistances(self): 
		
		ds = []

		for l in self.lines: 
			ds.append(l.getDistance())

		return ds

	def getAppState(self):

		return self.App.returnState()

class LineR:

	def __init__(self, vector, Source):

		self.Source = Source
		self.origin = Source.pos
		self.vector = vector
		self.hit = True
		self.dist = 0
		# self.secondOrigin = self.vectToPoint(self.vector, 50)
		self.pointOnLine = self.vectToPoint(self.vector, SCALE)

	def cast(self, bound):

		if not self.getPossibleIntersection(bound): 
			return None
		
		x1, y1 = bound.s[0], bound.s[1]
		x2, y2 = bound.e[0], bound.e[1]
		x3, y3 = self.origin[0], self.origin[1]
		x4 = self.pointOnLine[0]
		y4 = self.pointOnLine[1]
		den = (x1 - x2)*(y3 - y4) - (y1 - y2)*(x3 - x4)
		if den == 0: 
			print("den = 0")
		tnum = (x1 - x3)*(y3 - y4) - (y1 - y3)*(x3 - x4)
		unum = (x2 - x1)*(y1 - y3) - (y2 - y1)*(x1 - x3)
		t = tnum/den
		u = unum/den
		if t > 0 and t < 1 and u > 0:
			self.hit = True
			retPoint = (round(x1 + t*(x2 - x1), 3), round(y1 + t*(y2-y1), 3))
			return retPoint
		else: 
			return None

	def getPossibleIntersection(self, bound):

		v1 = self.vector.rotate_rad(3.14)
		v2 = bound.getVector()
		scalar = v1.dot(v2)
		return scalar < 1
		
	def reset(self): 

		self.pointOnLine = self.vectToPoint(self.vector, SCALE)
		self.hit = False

	def distTo(self, pol):

		hyp = np.sqrt((pol[0] - self.origin[0])**2 + (pol[1] - self.origin[1])**2)
		return round(hyp, 3)

	def update(self, pos):

		self.reset()

		self.origin = pos

		pols = {}

		for bound in self.Source.App.BC.lines:
			c = self.cast(bound)
			pol = c if c != None else None
			if pol:
				pols[pol] = self.distTo(pol)
		

		sortedDictionary = sorted(pols, key = pols.get)

		pl = None if not sortedDictionary else sortedDictionary[0]

		if pl:
			self.pointOnLine = pl
		else:
			self.pointOnLine = self.vectToPoint(self.vector, SCALE)

	def vectToPoint(self, vector, s):

		x = self.origin[0] + vector.x * s
		y = self.origin[1] + vector.y * s
		t = (x, y)
		return t

	def getDistance(self): 

		d = self.distTo(self.pointOnLine)
		return d

	def show(self):

		draw.aaline(SETUP, FG, self.origin, self.pointOnLine)

# Rendering Farlands 

class Renderer: 

	def __init__(self, Source): 

		self.surf = GAME
		self.S = Source
		self.l = self.S.lines
		self.n = len(self.S.lines)
		self.r = self.getResolution(self.n)

	def getResolution(self, n): 
		
		scale = (self.surf.get_width() // self.n)
		return scale

	def show(self):

		dists = self.S.getDistances()

		for i in range(self.n):
			line = self.l[i]

			d = dists[i]
			if d > SCALE - DRAW_DISTANCE: continue
			
			delta = d * 0.2
			
			height = self.surf.get_height() - delta
			width = self.r
			
			x = width * i
			y = delta / 2
			
			rect = pygame.Rect((x, y), (width, height))
			
			alpha = min(int(255*(LIGHT_FALLOFF/delta)), 255)
			color = pygame.Color(FG)
			color.a = alpha
			color = color.premul_alpha()
			draw.rect(self.surf, color, rect)

a = App(100)
a.run()