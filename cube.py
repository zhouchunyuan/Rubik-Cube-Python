# cube.py
# Chris Barker
# CMU S13 15-112 Term Project
# modified by Chunyuan March 2017

from Tkinter import *
from geometry import *
import heapq
import copy
import random
import solutions
import math
from math import sin, cos, pi

class Struct(object): pass

def loadObject(path, index):
    with open(path) as file:
        try: data = file.read()
        except Exception as e:
            print 'Error reading data!', e
    return eval(data)[index]

def drawChevron(canvas, cx, cy, r):
    coords = (cx - 0.3 * r, cy - 0.5 * r, 
              cx - 0.2 * r, cy - 0.5 * r,
              cx + 0.3 * r, cy,
              cx - 0.2 * r, cy + 0.5 * r,
              cx - 0.3 * r, cy + 0.5 * r,
              cx - 0.3 * r, cy + 0.4 * r,
              cx + 0.2 * r, cy,
              cx - 0.3 * r, cy - 0.4 * r)
    canvas.create_polygon(*coords, fill='white', state='disabled')

def brief(L):
    s = ''
    for e in L:
        s += str(e[0])
    return s

def reversal(move):
    if type(move) == tuple:
        move = move[0]
    if type(move) == str:
        if "'" in move:
            move = move[0]
        else:
            move = move + "'"
    return move

def darken(color):
    if color[0] != '#':
        if color == 'white':
            color = '#ffffff'
        elif color == 'orange':
            color = '#ffa500'
        elif color == 'red':
            color = '#ff0000'
        elif color == 'blue':
            color = '#0000ff'
        elif color == 'green':
            color = '#00ff00'
        elif color == 'yellow':
            color = '#ffff00'
        else: return color
        return darken(color)
    else:
        red = int(color[1:3], 16)
        green = int(color[3:5], 16)
        blue = int(color[5:7], 16)
        red /= 2
        green /= 2
        blue /= 2
        return '#%02x%02x%02x' % (red, green, blue)

class CenterPiece(object):
    def __init__(self, vec, parent):
        self.vec = vec
        self.parent = parent
    def callback(self, e):
        self.parent.addMoves([self.vec], self.PLAYING)

class Cube(object):
    directions = { I_HAT : 'green',
                  -I_HAT : 'blue',
                   J_HAT : 'red',
                  -J_HAT : 'orange',
                   K_HAT : 'yellow',
                  -K_HAT : 'white'}

    helpStrings = { 
        'general': 'Welcome to Cubr!\nHover over a button below to view help for it.\n\n\
The Rubik\'s Cube, invented in 1974 by Erno Rubik, is one of the most popular toys of all time.\n\
It consists of six independently rotating faces, each with nine colored stickers.\n\
The goal is to arrange the cube so that each face contains only one color.\n\
In 1981 David Singmaster published his popular three-layer solution method, which is used in this program.\n\
With practice, most people could solve the cube in under a minute. Since then, speedcubing has taken off and the current record is held by \n\
Mats Valk, who solved the cube in 5.55 seconds. In 2010, Tomas Rokicki proved that any Rubik\'s cube can be solved in 20 face rotations or less.\n\n\
This program will interactively guide you through the three-layer solution algorithm.\n\
At each step of the solution, you will be given information describing the step you are completing.\n\
You may either work with a randomly generated Rubik\'s Cube, or use your webcam to input the current configuration of your own cube!\n\n\
Many people think of solving the cube as moving the 54 stickers into place. However, it is much more helpful to think about it as\n\
moving 20 "blocks" (12 edges, 8 corners) into place. The centers of each face always stay in the same orientation relative to each other,\n\
and the stickers on each block always stay in place relative to each other.\n\
Solving the first layer means getting four edges and four corners in place so that one face is all the same color.\n\
This is intuitive for many people, but by being conscious of the algorithms you use, you can improve your time and consistency.\n\
The second layer of blocks requires only one algorithm, and involves moving only four edge pieces into place.\n\
The third and final layer is the most complicated, and requires separate algorithms for orienting (getting the stickers facing the right way)\n\
and for permuting (getting the individual blocks into place). With enough practice, you can be an expert cube solver!\n\
',

        'pause': 'During a guided solution, press this button to pause your progress.',
        'play': 'During a guided solution, press this button to resume solving the cube.',
        'reverse': 'During a guided solution, press this button to reverse the moves made so far.',
        'back': 'Press this button to step one move backward.',
        'step': 'Press this button to step one move forward.',
        'speedUp': 'Press this button to increase the rotation speed during a guided solution.',
        'slowDown': 'Press this button to decrease the rotation speed during a guided solution.',
        'fromCamera': 'Press this button to start the camera and input the configuration of your Rubik\'s cube.\n\
Tip: When inputting your cube through the camera, tilt the cube up or down to reduce glare from the screen.\n\
More tips: If the program misrecognizes a color, press the spacebar anyway to record the colors. Then, click on the misrecognized\n\
color and select the correct color from the list of colors that will pop up. Make sure you copy the movement of the virtual cube when it\n\
rotates to the next face so that your cube will be interpreted accurately.',
        'guide': 'guides through solution',
        'guideFast': 'guides through solution more quickly',
        'reset': 'resets the cube to a solved state',
        'shuffle': 'shuffles the cube',
        'solve': 'solves the cube',
        'info': 'reopen this screen',
        'stats': 'shows statistics'
    }

    faceColors = { }

    @classmethod
    def setFaceColors(cls):
        cls.faceColors = {}
        for z in xrange(3):
            for y in xrange(3):
                for x in xrange(3):
                    pieceId = z * 9 + y * 3 + x + 1
                    cls.faceColors[pieceId] = [ ]
                    (X, Y, Z) = (x - 1, y - 1, z - 1)
                    pos = Vector(X,Y,Z)
                    for vec in [Vector(0,0,1), Vector(0,1,0), Vector(1,0,0)]:
                        for direction in cls.directions:
                            if direction // vec:
                                if direction ** pos > 0:
                                    cls.faceColors[pieceId].append(cls.directions[direction])
    
    def __init__(self, canvas, controlPane, app, mode='solved'):
        Cube.setFaceColors()

        #print self.faceColors

        self.state = CubeState(mode)
        self.faces = { }
        self.size = 3
        self.center = Vector(0,0,0)
        self.app = app

        (self.PAUSED, self.PLAYING, self.REVERSING, self.STEP, self.BACK) = (1,2,3,4,5)
        self.status = self.PAUSED

        (self.INGAME, self.SHOWINGINFO, self.SHOWINGSTATS) = range(3)
        self.helpState = self.SHOWINGINFO
        self.statString = ''
        self.helpIndex = 'general'

        self.shuffling = False

        self.delay = 100
        self.direction = (0, 0)
        self.after = 0
        self.debug = False
        self.message = ""
        self.sol = ''
        self.shuffleLen = 200

        self.moveList = [ ]
        self.moveIndex = -1

        self.controlPane = controlPane
        self.timeBetweenRotations = 0
        self.timeUntilNextRotation = 0

        self.rotating = False
        self.rotationAxis = False
        self.rotationDirection = False
        self.rotationCount = 0
        self.maxRot = 5
        self.rotationQueue = [ ]
        self.rotatingValues = [ ]
        self.sensitivity = 0.04 # click and drag

        self.showingPB = False
        self.pbMin = 0
        self.pbVal = 0
        self.pbMax = 0

        self.paused = False

        self.configureControls(controlPane)

        self.configureWindow(canvas)
        self.showInWindow()

    @property
    def maxRot(self):
        return self.maxRotationCount
    @maxRot.setter
    def maxRot(self, value):
        self.maxRotationCount = value
        self.rotationDTheta = math.pi / (2. * self.maxRotationCount)
    @maxRot.deleter
    def maxRot(self):
        pass
 
    def configureControls(self, pane):

        pane.delete(ALL)

        width = int(pane.cget('width'))
        height = int(pane.cget('height'))

        r = 24

        #
        # PAUSE
        #
        (cx, cy) = (width/2, height/2)
        pauseButton = pane.create_oval(cx - r, cy - r, cx + r, cy + r,
                                       fill='#0088ff', activefill='#00ffff', 
                                       outline='#ffffff', width=1, activewidth=3)
        pane.tag_bind(pauseButton, '<Button-1>', self.pause)
        pane.create_rectangle(cx - (r * 0.35), cy - (r * 0.5), 
                              cx - (r * 0.10), cy + (r * 0.5), fill='#ffffff',
                              state='disabled')
        pane.create_rectangle(cx + (r * 0.35), cy - (r * 0.5), 
                              cx + (r * 0.10), cy + (r * 0.5), fill='#ffffff',
                              state='disabled')

        pane.tag_bind(pauseButton, '<Enter>', lambda e: self.assignHelp('pause'))
        pane.tag_bind(pauseButton, '<Leave>', lambda e: self.assignHelp('general'))

        #
        # PLAY
        #
        (cx, cy) = (width/2 + r*2.4, height/2)
        playButton = pane.create_oval(cx - r, cy - r, cx + r, cy + r,
                                       fill='#0088ff', activefill='#00ffff', 
                                       outline='#ffffff', width=1, activewidth=3)
        pane.tag_bind(playButton, '<Button-1>', self.play)
        pane.create_polygon(cx - r * 0.35, cy - r * 0.5,
                            cx + r * 0.55, cy,
                            cx - r * 0.35, cy + r * 0.5, fill='#ffffff',
                            state='disabled')
        pane.tag_bind(playButton, '<Enter>', lambda e: self.assignHelp('play'))
        pane.tag_bind(playButton, '<Leave>', lambda e: self.assignHelp('general'))

        #
        # REVERSE
        #
        (cx, cy) = (width/2 - r*2.4, height/2)
        reverseButton = pane.create_oval(cx - r, cy - r, cx + r, cy + r,
                                       fill='#0088ff', activefill='#00ffff', 
                                       outline='#ffffff', width=1, activewidth=3)
        pane.tag_bind(reverseButton, '<Button-1>', self.reverse)
        pane.create_polygon(cx + r * 0.35, cy - r * 0.5,
                            cx - r * 0.55, cy,
                            cx + r * 0.35, cy + r * 0.5, fill='#ffffff',
                            state='disabled')
        pane.tag_bind(reverseButton, '<Enter>', lambda e: self.assignHelp('reverse'))
        pane.tag_bind(reverseButton, '<Leave>', lambda e: self.assignHelp('general'))

        #
        # SPEED UP
        #
        (cx, cy) = (width/2 + r * 10.0, height/2)
        speedUpButton = pane.create_rectangle(cx - r, cy - r, cx + r, cy + r,
                                              fill='#0088ff', activefill='#00ffff',
                                              outline='#ffffff', width=1, activewidth=3)
        pane.tag_bind(speedUpButton, '<Button-1>', self.speedUp)
        drawChevron(pane, cx, cy, r)
        drawChevron(pane, cx - 0.3 * r, cy, r * 0.8)
        drawChevron(pane, cx + 0.3 * r, cy, r * 1.2)
        pane.tag_bind(speedUpButton, '<Enter>', lambda e: self.assignHelp('speedUp'))
        pane.tag_bind(speedUpButton, '<Leave>', lambda e: self.assignHelp('general'))

        #
        # SLOW DOWN
        #
        (cx, cy) = (width/2 + r * 7.5, height/2)
        slowDownButton = pane.create_rectangle(cx - r, cy - r, cx + r, cy + r,
                                              fill='#0088ff', activefill='#00ffff',
                                              outline='#ffffff', width=1, activewidth=3)
        pane.tag_bind(slowDownButton, '<Button-1>', self.slowDown)
        drawChevron(pane, cx - 0.3 * r, cy, r * 0.8)
        drawChevron(pane, cx, cy, r)
        pane.tag_bind(slowDownButton, '<Enter>', lambda e: self.assignHelp('slowDown'))
        pane.tag_bind(slowDownButton, '<Leave>', lambda e: self.assignHelp('general'))

        #
        # SHUFFLE
        #
        (cx, cy) = (r * 1.5, height/2)
        shuffleButton = pane.create_oval(cx - r, cy - r, cx + r, cy + r,
                                       fill='#0088ff', activefill='#00ffff', 
                                       outline='#ffffff', width=1, activewidth=3)
        pane.tag_bind(shuffleButton, '<Button-1>', self.shuffle)
        coords = (cx - 0.6 * r, cy - 0.4 * r, 
                  cx - 0.6 * r, cy - 0.2 * r,
                  cx - 0.2 * r, cy - 0.2 * r,
                  cx + 0.2 * r, cy + 0.4 * r,
                  cx + 0.6 * r, cy + 0.4 * r,
                  cx + 0.6 * r, cy + 0.6 * r,
                  cx + 0.8 * r, cy + 0.3 * r,
                  cx + 0.6 * r, cy - 0.0 * r,
                  cx + 0.6 * r, cy + 0.2 * r,
                  cx + 0.2 * r, cy + 0.2 * r,
                  cx - 0.2 * r, cy - 0.4 * r,
                  cx - 0.4 * r, cy - 0.4 * r)

        pane.create_polygon(*coords, outline='#ffffff', fill='#0000ff', state='disabled')

        coords = (cx - 0.6 * r, cy + 0.4 * r, 
                  cx - 0.6 * r, cy + 0.2 * r,
                  cx - 0.2 * r, cy + 0.2 * r,
                  cx + 0.2 * r, cy - 0.4 * r,
                  cx + 0.6 * r, cy - 0.4 * r,
                  cx + 0.6 * r, cy - 0.6 * r,
                  cx + 0.8 * r, cy - 0.3 * r,
                  cx + 0.6 * r, cy - 0.0 * r,
                  cx + 0.6 * r, cy - 0.2 * r,
                  cx + 0.2 * r, cy - 0.2 * r,
                  cx - 0.2 * r, cy + 0.4 * r,
                  cx - 0.4 * r, cy + 0.4 * r)

        pane.create_polygon(*coords, outline='#ffffff', fill='#0000ff', state='disabled')
        pane.tag_bind(shuffleButton, '<Enter>', lambda e: self.assignHelp('shuffle'))
        pane.tag_bind(shuffleButton, '<Leave>', lambda e: self.assignHelp('general'))

        #
        # SOLVE
        #
        (cx, cy) = (r * 4.0, height/2)
        solveButton = pane.create_oval(cx - r, cy - r, cx + r, cy + r,
                                       fill='#0088ff', activefill='#00ffff', 
                                       outline='#ffffff', width=1, activewidth=3)
        pane.tag_bind(solveButton, '<Button-1>', self.solve)
        pane.create_text(cx, cy, text='Solve', fill='white', state='disabled') 
        pane.tag_bind(solveButton, '<Enter>', lambda e: self.assignHelp('solve'))
        pane.tag_bind(solveButton, '<Leave>', lambda e: self.assignHelp('general'))

        #
        # RESET
        #
        (cx, cy) = (r * 6.5, height/2)
        resetButton = pane.create_oval(cx - r, cy - r, cx + r, cy + r,
                                       fill='#0088ff', activefill='#00ffff', 
                                       outline='#ffffff', width=1, activewidth=3)
        pane.tag_bind(resetButton, '<Button-1>', self.reset)

        pane.create_text(cx, cy, text='Reset', fill='white', state='disabled')
        pane.tag_bind(resetButton, '<Enter>', lambda e: self.assignHelp('reset'))
        pane.tag_bind(resetButton, '<Leave>', lambda e: self.assignHelp('general'))

        #
        # FROM CAMERA
        #
        (cx, cy) = (r * 9.0, height/2)
        fromcamButton = pane.create_oval(cx - r, cy - r, cx + r, cy + r,
                                       fill='#0088ff', activefill='#00ffff', 
                                       outline='#ffffff', width=1, activewidth=3)
        pane.tag_bind(fromcamButton, '<Button-1>', self.fromCamera)

        pane.create_text(cx, cy-12, text='From', fill='white', state='disabled')
        pane.create_text(cx, cy, text='Camera', fill='white', state='disabled')
        pane.tag_bind(fromcamButton, '<Enter>', lambda e: self.assignHelp('fromCamera'))
        pane.tag_bind(fromcamButton, '<Leave>', lambda e: self.assignHelp('general'))
        #
        # GUIDE
        #
        (cx, cy) = (r * 12.5, height/2)
        guideButton = pane.create_rectangle(cx - 2*r, cy - r, cx + 2*r, cy + r,
                                       fill='#0088ff', activefill='#00ffff', 
                                       outline='#ffffff', width=1, activewidth=3)
        pane.tag_bind(guideButton, '<Button-1>', self.guideThrough)

        pane.create_text(cx, cy-12, text='Guide Through', fill='white', state='disabled')
        pane.create_text(cx, cy, text='Solution', fill='white', state='disabled')
        pane.tag_bind(guideButton, '<Enter>', lambda e: self.assignHelp('guide'))
        pane.tag_bind(guideButton, '<Leave>', lambda e: self.assignHelp('general'))

        #
        # GUIDE FASTER
        #
        (cx, cy) = (r * 17.5, height/2)
        guideFastButton = pane.create_rectangle(cx - 2.5*r, cy - r, cx + 2.5*r, cy + r,
                                       fill='#0088ff', activefill='#00ffff', 
                                       outline='#ffffff', width=1, activewidth=3)
        pane.tag_bind(guideFastButton, '<Button-1>', self.guideFastThrough)

        pane.create_text(cx, cy-12, text='Guide Through', fill='white', state='disabled')
        pane.create_text(cx, cy, text='Solution (Faster)', fill='white', state='disabled')
        pane.tag_bind(guideFastButton, '<Enter>', lambda e: self.assignHelp('guideFast'))
        pane.tag_bind(guideFastButton, '<Leave>', lambda e: self.assignHelp('general'))

        #
        # BACK
        #
        r = 14
        (cx, cy) = (width/2 - r*7.5, height/2)
        backButton = pane.create_oval(cx - r, cy - r, cx + r, cy + r,
                                       fill='#0088ff', activefill='#00ffff', 
                                       outline='#ffffff', width=1, activewidth=3)
        pane.tag_bind(backButton, '<Button-1>', self.back)
        pane.create_polygon(cx + r * 0.35, cy - r * 0.5,
                            cx - r * 0.55, cy,
                            cx + r * 0.35, cy + r * 0.5, fill='#ffffff',
                            state='disabled')
        pane.tag_bind(backButton, '<Enter>', lambda e: self.assignHelp('back'))
        pane.tag_bind(backButton, '<Leave>', lambda e: self.assignHelp('general'))

        #
        # FORWARD
        #
        (cx, cy) = (width/2 + r*7.5, height/2)
        stepButton = pane.create_oval(cx - r, cy - r, cx + r, cy + r,
                                       fill='#0088ff', activefill='#00ffff', 
                                       outline='#ffffff', width=1, activewidth=3)
        pane.tag_bind(stepButton, '<Button-1>', self.step)
        pane.create_polygon(cx - r * 0.35, cy - r * 0.5,
                            cx + r * 0.55, cy,
                            cx - r * 0.35, cy + r * 0.5, fill='#ffffff',
                            state='disabled')
        pane.tag_bind(stepButton, '<Enter>', lambda e: self.assignHelp('step'))
        pane.tag_bind(stepButton, '<Leave>', lambda e: self.assignHelp('general'))

        #
        # INFO
        #
        (cx, cy) = (width - r * 3.5, height/2)
        helpButton = pane.create_rectangle(cx - 2*r, cy - r, cx + 2*r, cy + r,
                                       fill='#0088ff', activefill='#00ffff', 
                                       outline='#ffffff', width=1, activewidth=3)
        pane.tag_bind(helpButton, '<Button-1>', lambda e: self.assignHelpState(self.SHOWINGINFO))

        pane.create_text(cx, cy, text='Help', fill='white', state='disabled')
        pane.tag_bind(helpButton, '<Enter>', lambda e: self.assignHelp('info'))
        pane.tag_bind(helpButton, '<Leave>', lambda e: self.assignHelp('general'))

        #
        # STATS
        #
        (cx, cy) = (width - r * 8.0, height/2)
        statsButton = pane.create_rectangle(cx - 2*r, cy - r, cx + 2*r, cy + r,
                                       fill='#0088ff', activefill='#00ffff', 
                                       outline='#ffffff', width=1, activewidth=3)
        pane.tag_bind(statsButton, '<Button-1>', self.showStats)

        pane.create_text(cx, cy, text='Stats', fill='white', state='disabled')
        pane.tag_bind(statsButton, '<Enter>', lambda e: self.assignHelp('stats'))
        pane.tag_bind(statsButton, '<Leave>', lambda e: self.assignHelp('general'))

    def configureWindow(self, canvas):
        if canvas == None:
            self.root = Tk()
            (self.width, self.height) = (450, 450)
            self.canvas = Canvas(self.root, width=self.width, height=self.height, background='#333333')
            self.needsLoop = True
        else:
            self.root = canvas._root()
            self.canvas = canvas
            (self.width, self.height) = (int(canvas.cget('width')), int(canvas.cget('height')))
            self.needsLoop = False

        self.dim = {'width': self.width, 'height': self.height}
    
    def speedUp(self, e):
         self.maxRot = max(1, self.maxRot - 1)
    def slowDown(self, e):
        self.maxRot += 1

    def timer(self):
        needsRedraw = self.move() or (not self.status == self.PAUSED)

        if self.rotating:
            self.rotationCount -= 1
            if self.rotationCount <= 0:
                self.rotating = False
                self.rotatingValues = [ ]
                self.state.rotate(self.rotationItem)
                del self.rotationItem
            needsRedraw = True

        if self.timeUntilNextRotation > 0:
            self.timeUntilNextRotation -= 1

        if (not self.rotating) and (self.timeUntilNextRotation <= 0):
            if (self.status == self.PLAYING) or (self.status == self.STEP):
                if self.moveIndex >= (len(self.moveList) - 1):
                    self.status = self.PAUSED
                    self.updateMessage('')
                    self.shuffling = False
                else:
                    self.moveIndex += 1
                    needsRedraw = self.makeMove(self.moveList[self.moveIndex],
                        animate = not self.shuffling, 
                        render = not self.shuffling or (self.moveIndex % 20 == 0))

            if (self.status == self.REVERSING) or (self.status == self.BACK):
                if self.moveIndex < 0:
                    self.status = self.PAUSED
                else:
                    needsRedraw = self.makeMove(reversal(self.moveList[self.moveIndex]))
                    self.moveIndex -= 1

            if (self.status == self.STEP) or (self.status == self.BACK):
                self.status = self.PAUSED
            self.timeUntilNextRotation = self.timeBetweenRotations


        if needsRedraw:
            try:
                self.redraw()
            except:
                self.updateMessage('Could not read cube.')
                self.state.setSolved()
                self.redraw()

    def updateMessage(self, msg):
        self.message = msg

    def updateSol(self, msg):
        self.sol = msg

    def showInWindow(self):
        self.canvas.pack()
        self.camera = Camera(Vector(4,-6.5,-7), Vector(0,0,0), pi/5, self.dim)
        self.amt = self.camera.sensitivity * self.camera.pos.dist(self.camera.origin)
        self.redraw()
        if self.needsLoop: root.mainloop()
        
    def cleanup(self):
        for pg in self.faces.values():
                self.canvas.itemconfig(pg, state='hidden')

    def move(self):
        self.amt = self.camera.sensitivity * self.camera.pos.dist(self.camera.origin)
        redraw = False
        if self.direction != (0, 0):
            self.camera.rotate(self.direction)
            redraw = True
        if self.app.resized:
            self.app.dragVal = (0,0)
            self.app.resized = False
            redraw = True
        elif self.app.dragVal != (0,0):
            self.camera.rotate((-self.sensitivity * self.app.dragVal[0],
                                -self.sensitivity * self.app.dragVal[1]))
            redraw = True
            self.app.dragVal = (self.app.dragVal[0] * 0.7,
                                self.app.dragVal[1] * 0.7)            
            if self.app.dragVal[0] < 0.01 and self.app.dragVal[1] < 0.01:
                self.app.dragVal = (0,0)
        return redraw

    @staticmethod
    def corners(center, direction, *args):
        if len(args) == 0:
            if direction // Vector(0,1,0): # parallel
                norm1 = Vector(1, 0, 0)
            else: norm1 = Vector(0,1,0)
            norm2 = 2 * direction * norm1
        else: (norm1, norm2) = args

        corners = [ ]
        for coef1 in xrange(-1, 2, 2):
            for coef2 in xrange(coef1, -2 * coef1, -2*coef1):
                corner = center + (0.5 * norm1 * coef1 +
                                   0.5 * norm2 * coef2)
                corners.append(corner)
        return corners

    def pieceOffset(self, x, y, z):
        z -= 1
        y -= 1
        x -= 1
        return Vector(x,y,z)
        
    def redraw(self):
        self.canvas.delete(ALL)

        # Top message
        self.canvas.create_text(self.camera.width/2, 40, text=self.message, fill='white', font='Arial 24 bold')

        # Bottom message
        sol = self.sol
        lineWidth = 100
        margin = 15
        y = self.camera.height - margin - 20
        while len(sol) > 0:
            self.canvas.create_text(self.camera.width/2, 
                y, text=sol[-lineWidth:], fill='white', font='Courier 12')
            y -= margin
            sol = sol[:-lineWidth]

        # Progress bar
        if self.showingPB:
            w = (self.width * (self.moveIndex - self.pbMin + 1) / 
                    (max(1, self.pbMax - self.pbMin)))
            self.canvas.create_rectangle(0, self.height-20, w, self.height, fill='#00ff66')

        toDraw = [ ]

        for z in xrange(self.size):
            for y in xrange(self.size):
                for x in xrange(self.size):
                    try:
                        (pieceID, rotationKey) = self.state.state[z][y][x]
                    except:
                        pieceID = 1
                        rotationKey = 210

                    pieceCenter = self.center + self.pieceOffset(x, y, z)
                    outDirections = [d for d in Cube.directions if d**pieceCenter > 0]
                    sod = [ ] #sorted out directions
                    for od in outDirections:
                        if od // CubeState.keys[rotationKey / 100]:
                            sod.append(od)
                    for od in outDirections:
                        if od // CubeState.keys[(rotationKey / 10) % 10]:
                            sod.append(od)
                    for od in outDirections:
                        if od // CubeState.keys[rotationKey % 10]:
                            sod.append(od)

                    pieceRotation = Vector(0,0,0)
                    theta = 0.

                    if pieceID in self.rotatingValues:
                        oldCenter = pieceCenter
                        pieceOffset = pieceCenter - (pieceCenter > self.rotationAxis)
                        pieceRotation = self.rotationAxis * pieceOffset
                        theta = self.rotationDTheta * (self.maxRot - self.rotationCount)

                        if self.rotationDirection:
                            theta *= -1

                        pieceCenter = (pieceCenter > self.rotationAxis)
                        pieceCenter = pieceCenter + cos(theta) * pieceOffset
                        pieceCenter = pieceCenter + sin(theta) * pieceRotation

                    faceColors = Cube.faceColors[pieceID]
                    #print pieceID,faceColors
                    for direc, color in zip(sod, faceColors):
                        axes = ()
                        faceCenter = pieceCenter + (direc / 2)

                        if pieceID in self.rotatingValues:
                            if direc // self.rotationAxis:
                                faceCenter = pieceCenter + (direc / 2)
                                if self.rotationAxis // Vector(0,1,0):
                                    axis0temp = Vector(1,0,0)
                                else:
                                    axis0temp = Vector(0,1,0)
                                axis1temp = direc * axis0temp
                                axis0 = axis0temp * cos(theta) + axis1temp * sin(theta)
                                axis1 = axis0 * direc
                                axes = (axis0, axis1)
                            else:
                                perp = -1 * (direc * self.rotationAxis)
                                perp = perp ^ (direc.mag)
                                faceCenter = pieceCenter + (sin(theta) * (perp / 2) + 
                                                            cos(theta) * (direc / 2))
                                axis0 = self.rotationAxis
                                axis1 = (faceCenter - pieceCenter) * self.rotationAxis * 2
                                axes = (axis0, axis1)
                            
                        visible = (faceCenter - pieceCenter) ** (faceCenter - self.camera.pos) < 0
                        corners = self.corners(faceCenter, pieceCenter - faceCenter, *axes)
                        corners = [corner.flatten(self.camera) for corner in corners]
                        state = 'disabled' # if visible else 'hidden'
                        outline = '#888888' if visible else 'gray'
                        if not visible: color = 'gray'
                        a = 0 if visible else 1000
                        spec = (corners, color, state, outline)
                        toDraw.append(((pieceCenter-self.camera.pos).mag + a, spec))
                        #a = self.canvas.create_polygon(corners, fill=color, 
                        #                            width=2, state=state, outline='#888888'
                        #                            #,activewidth=4, activefill=darken(color)
                        #                            )
                        if self.debug:
                            self.canvas.create_text(faceCenter.flatten(self.camera), text=str(pieceID))

                        #if pieceCenter.mag() == 1:
                        #    b = CenterPiece(pieceCenter, self)
                        #    self.canvas.tag_bind(a, '<Button-1>', b.callback)

                        """
                        newCorners = ()
                        for corner in corners: newCorners += corner.flatten(self.camera)
                        if visible:
                            self.canvas.create_polygon(self.faces[(pieceID,color)], newCorners)
                        #self.canvas.itemconfig(self.faces[(pieceID,color)], state=state)
              
                        """

            toDraw.sort(lambda a,b: cmp(b,a))
            for polygon in toDraw:
                spec = polygon[1]
                (corners, color, state, outline) = spec
                self.canvas.create_polygon(corners, fill=color, width=2, state=state, outline=outline)

        self.drawHelp()


    def gatherStats(self):
        self.statString = 'Unable to fetch solution logs.'
        stats = None
        try:
            with open('solutionLogs.txt') as file:
                stats = eval(file.read())
        except: return
        if stats is not None:
            self.statString = ''

            stats = [s.split(';') for s in stats]

            moves = [stat[-1] for stat in stats] # Gets last element
            moves = [mv[6:] for mv in moves] # Remove "Moves:"
            moves = [int(mv) for mv in moves]
            if len(moves) == 0:
                self.statString += "No solutions generated yet."
                return
            self.statString += "%d solution%s logged.\n" % (len(moves), '' if len(moves)==1 else 's')
            avgMoves = sum(moves)/len(moves)
            self.statString += "Average number of 90 degree face rotations per solution: %d\n" % (avgMoves)

            times = [stat[-2] for stat in stats] # gets 2nd to last element
            times = [tm[6:-4] for tm in times] # removes "Time: " ... " sec"
            times = [float(tm) for tm in times]
            avgTime = sum(times)/(max(1, len(times)))
            self.statString += "Average time needed to generate a solution: %0.4f seconds" % (avgTime)

    def resetStats(self):
        try:
            with open('solutionLogs.txt', 'r+') as file:
                file.seek(0) # beginning
                file.truncate()
                file.writelines(['[]'])
        except: return

    def showStats(self, *args):
        self.gatherStats()
        self.helpState = self.SHOWINGSTATS

    def drawHelp(self):
        ## MAGIC NUMBERS EVERYWHERE
        if self.helpState == self.SHOWINGINFO:
            canvas = self.canvas
            canvas.create_rectangle(100, 100, self.width-100, self.height-100,
                fill='#888888', outline='#ccccff', width=4)
            canvas.create_rectangle(110, 110, 140, 140, fill='#880000', activefill='#aa0000')
            canvas.create_text(125, 125, text='X', fill='black', state='disabled')

            canvas.create_rectangle(self.width/2-50, self.height-140, 
                                    self.width/2+50, self.height-110, 
                                    fill='#008800', activefill='#00aa00')
            canvas.create_text(self.width/2, self.height-125, text='Start', fill='black', state='disabled')

            canvas.create_text(self.width/2, 130, text="Welcome to Cubr!",
                font='Arial 25 bold')

            canvas.create_text(self.width/2, self.height/2, text=self.helpStrings[self.helpIndex])

        elif self.helpState == self.SHOWINGSTATS:
            canvas = self.canvas
            canvas.create_rectangle(100, 100, self.width-100, self.height-100,
                fill='#888888', outline='#ccccff', width=4)
            canvas.create_rectangle(110, 110, 140, 140, fill='#880000', activefill='#aa0000')
            canvas.create_text(125, 125, text='X', fill='black', state='disabled')

            canvas.create_rectangle(self.width/2-50, self.height-140, 
                                    self.width/2+50, self.height-110, 
                                    fill='#008800', activefill='#00aa00')
            canvas.create_text(self.width/2, self.height-125, text='Back', fill='black', state='disabled')

            canvas.create_rectangle(147, self.height-130, 178, self.height-115, fill='#aaffaa', activefill='#ffffff')
            canvas.create_text(250, self.height-130, text="These statistics are generated dynamically.\nClick here to reset your data logs.", state='disabled')

            canvas.create_text(self.width/2, self.height/2, text=self.statString, font='Arial 24 bold')

    def click(self, event):
        if self.helpState == self.SHOWINGINFO or self.helpState == self.SHOWINGSTATS:
            if 110 < event.x < 140 and 110 < event.y < 140:
                self.helpState = self.INGAME
                self.redraw()
            elif self.width/2-50 < event.x < self.width/2+50 and \
                 self.height-140 < event.y < self.height-110:
                 self.helpState = self.INGAME
                 self.redraw()
        if self.helpState == self.SHOWINGSTATS:
            if 147 < event.x < 178 and self.height-130 < event.y < self.height-115:
                self.resetStats()
                self.showStats()
                self.redraw()

    def assignHelp(self, key):
        self.helpIndex = key
        self.redraw()

    def assignHelpState(self, state):
        self.helpState = state
        self.redraw()

    def setConfig(self, config):
        #print config.events
        try:
            self.state = CubeState('barebones')

            #colorOrder is used to contain the orientation info
            # ['0','1','2'] => 201
            # in this example, '2' is at the 2-index position
            #  use int(colorOrder[2]+colorOrder[1]+colorOrder[0]
            #  to create cube states
            colorOrder = [[[['','',''],['','',''],['','','']],
                           [['','',''],['','',''],['','','']],
                           [['','',''],['','',''],['','','']]],
                          [[['','',''],['','',''],['','','']],
                           [['','',''],['','',''],['','','']],
                           [['','',''],['','',''],['','','']]],
                          [[['','',''],['','',''],['','','']],
                           [['','',''],['','',''],['','','']],
                           [['','',''],['','',''],['','','']]]]
            if self.debug:
                print self.state

            # Modify the state to include [(color, direction), (color, direction), ...]
            # And then parse pieceId and orientationKey out of that

            def faceToAxis(face):
                if self.debug:
                    print face
                #decide direction according to the center piece
                center = face[1][1]   
                axis = [vec for vec in Cube.directions if 
                        Cube.directions[vec].lower() == center.lower()][0]
                return axis

            def setAxes(normal, known, dirString):
                dirString = dirString.lower()
                if dirString == 'up':
                    up = known
                elif dirString == 'down':
                    up = known * -1
                elif dirString == 'left':
                    up = (normal * known)
                elif dirString == 'right':
                    up = (known * normal)

                down = up * -1
                left = (up * normal)
                right = left * -1

                return (up, down, left, right)


            timesTouched = [[[0,0,0],[0,0,0],[0,0,0]],[[0,0,0],[0,0,0],[0,0,0]],[[0,0,0],[0,0,0],[0,0,0]]]
            
            for faceInfo in config:
                axis = faceToAxis(faceInfo.currentFace)
                prevAxis = nextAxis = None

                if faceInfo.prevFace:
                    prevAxis = faceToAxis(faceInfo.prevFace)
                if faceInfo.nextFace:
                    nextAxis = faceToAxis(faceInfo.nextFace)
                prevTurn = faceInfo.prevTurn
                nextTurn = faceInfo.nextTurn
                
                if self.debug:
                    print 'axis:', axis, Cube.directions[axis]
                    print 'prevAxis:', prevAxis,
                    if prevAxis:
                        print Cube.directions[prevAxis]
                    print 'nextAxis:', nextAxis, 
                    if nextAxis:
                        print Cube.directions[nextAxis]
                    print 'prevTurn:', prevTurn 
                    print 'nextTurn:', nextTurn

                if prevTurn:
                    (up, down, left, right) = setAxes(axis, prevAxis, prevTurn)
                elif nextTurn:
                    (up, down, left, right) = setAxes(axis, nextAxis * -1, nextTurn)

                if self.debug:
                    print 'up:', up, Cube.directions[up]
                    print 'down:', down, Cube.directions[down]
                    print 'left:', left, Cube.directions[left]
                    print 'right:', right, Cube.directions[right]
                    
                #print '----',faceInfo.currentFace[1][1],'----'

                for row in xrange(3):
                    for col in xrange(3):
                        pos = axis
                        pos = pos + (down * (row - 1))
                        pos = pos + (right * (col - 1))
                        #pos is the absolute coordinate
                        #1st corner is (blue,orange,white)
                        (x, y, z) = pos.components
                        (x, y, z) = (int(x+1), int(y+1), int(z+1))

                        timesTouched[z][y][x] += 1

                        cell = self.state.state[z][y][x]
                        if type(cell) == list:
                            cell.append((faceInfo.currentFace[row][col], axis))

                        ####### modified algorism for orientation ##############    
                        currentColor = faceInfo.currentFace[row][col]
                        currentColorCode = [vec for vec,color in Cube.directions.items() if color == currentColor]
                        currentColorCode = currentColorCode[0]
                        
                        if currentColorCode // Vector(0,0,1) :
                            orderCode = 2
                        elif currentColorCode // Vector(0,1,0) :
                            orderCode = 1
                        elif currentColorCode // Vector(1,0,0) :
                            orderCode = 0
                            
                        if axis // Vector(0,0,1):# currently in Z direction,
                            positionCode = 2 # Z direction [2]
                        elif axis // Vector(0,1,0):# currently in Y direction
                            positionCode = 1 # Y direction [1]
                        elif axis // Vector(1,0,0):# currently in X direction
                            positionCode = 0 # X direction [0]

                        colorOrder[z][y][x][orderCode ] = str(positionCode)
                        #########################################################
                        
                        #print currentColor, 'order',orderCode, 'pos',positionCode,'=',colorOrder[z][y][x]
                        if self.debug:
                            print 'x,y,z', x, y, z,
                            print 'pos=', pos,self.state.state[z][y][x]
                            print orderCode, positionCode
                            
            # fill vacant positions for colorOrder
            # e.g. ['2','','1'] => ['2','0','1']
            for z in xrange(3):
                for y in xrange(3):
                    for x in xrange(3):
                        notAdded = set(['0','1','2'])
                        for c in colorOrder[z][y][x]:
                            if c in notAdded:
                                notAdded.discard(c)
                        while len(notAdded) > 0:
                            for i in xrange(3):
                                if colorOrder[z][y][x][i]=='':
                                    colorOrder[z][y][x][i]= notAdded.pop()

##            for z in xrange(3):
##                for y in xrange(3):
##                    for x in xrange(3):
##                        print x,y,z
##                        orientation = colorOrder[z][y][x][2]+colorOrder[z][y][x][1]+colorOrder[z][y][x][0]
##                        #using "{:<2}".format(str(pieceID)) to pad
##                        print "{:<3}".format(str(orientation)),
##                    print ''
##                print ''
                    

            if self.debug:
                print 'state=', self.state
                print 'times', timesTouched

            # Cast each [ ] list to a ( ) tuple
            # [(color,dir),(color,dir),(color,dir)] ----> (pieceId, orientationKey)

            reverseZ = -1 if self.camera.view ** Vector(0,0,1) < 0 else 1
            reverseY = -1 if self.camera.view ** Vector(0,1,0) < 0 else 1
            reverseX = -1 if self.camera.view ** Vector(1,0,0) < 0 else 1

            zRange = range(3)[::reverseZ]
            yRange = range(3)[::reverseY]
            xRange = range(3)[::reverseX]

            for z in zRange:
                for y in yRange:
                    for x in xRange:
                        
                        cell = self.state.state[z][y][x]

                        if type(cell) == list:

                            pieceId = -1
                            colors = set()
                            for i in cell:
                                colors.add(i[0])

                            for key in Cube.faceColors:
                                if set(Cube.faceColors[key]) == colors:
                                    pieceId = key
                                    break
                            
                            if pieceId >= 0: pass
##                                desiredColorOrder = Cube.faceColors[pieceId]
##
##                                currentOrder = [ ]
##                                ori = 0
##                                notAdded = set([0,1,2])
##
##                                #print [c[0] for c in cell]
##
##                                cell.sort(lambda a,b: cmp(desiredColorOrder.index(a[0]),
##                                                          desiredColorOrder.index(b[0])))
##                                #print [c[0] for c in cell]
##                                #pirnt ''
##
##                                for i in cell:
##                                    ori *= 10
##                                    if i[1] // Vector(0,0,1):
##                                        ori += 2
##                                        notAdded.discard(2)
##                                    elif i[1] // Vector(0,1,0):
##                                        ori += 1
##                                        notAdded.discard(1)
##                                    elif i[1] // Vector(1,0,0):
##                                        ori += 0
##                                        notAdded.discard(0)
##
##                                while len(notAdded) > 0:
##                                    ori *= 10
##                                    ori += notAdded.pop()
##
##                                orientationKey = ori
                                #print pieceId,[(c[0],c[1]) for c in cell],'==',ori
                            else:
                                raise ValueError('Invalid Cube')

                            if pieceId in (5, 11, 13, 14, 15, 17, 23):
                                raise ValueError('Invalid Cube') # Center piece

##                            desired = Cube.faceColors[CubeState.solvedState[z][y][x][0]]
##
##                            if self.debug:
##                                print 'The piece with colors %s is at the position of %s' % (colors, desired)
##                                print 'setting (%d,%d,%d) to (%s, %s)' % (z,y,x,pieceId,orientationKey)
                                
                            oriStr = colorOrder[z][y][x]
                            orientationKey = int(oriStr[2]+oriStr[1]+oriStr[0])
                            
                            self.state.state[z][y][x] = (pieceId, orientationKey)
        except:
            self.updateMessage('Unable to read camera input.')
            self.state.setSolved()
            self.redraw()
        if self.debug:
            print 'final state=', self.state
                
        self.redraw()
        
    def addMoves(self, moves, status=-1):
        self.moveList[self.moveIndex+1:] = [ ]
        self.moveList.extend(moves)
        if status != -1:
            self.status = status

    def rotate(self, axis):
        self.showingPB = False
        self.addMoves([axis], self.PLAYING)

    def makeMove(self, move, render=True, animate=True):
        if type(move) == tuple:
            self.updateMessage(move[1])
            axis = move[0]
        else:
            axis = move

        self.rotationItem = self.state.rotationInfo(axis)

        if animate:
            self.rotating = True

            self.rotationAxis = self.rotationItem.rotationAxis
            self.rotatingValues = self.rotationItem.rotatingValues
            self.rotationDirection = self.rotationItem.rotationDirection
            self.rotationCount = self.maxRot

        else:
            self.rotating = False
            self.state.rotate(self.rotationItem)
            while (self.moveIndex + 1) % 20 != 0:
                if self.moveIndex == len(self.moveList) - 1:
                    self.updateMessage('')
                    break
                self.moveIndex += 1
                move = self.moveList[self.moveIndex]
                if type(move) == tuple:
                    self.updateMessage(move[1])
                    axis = move[0]
                else:
                    axis = move
                self.rotationItem = self.state.rotationInfo(axis)
                self.state.rotate(self.rotationItem)

        return render

    def pause(self, e):
        self.status = self.PAUSED
    def play(self, e):
        self.status = self.PLAYING
    def step(self, e):
        self.timeUntilNextRotation
        self.status = self.STEP
    def back(self, e):
        self.timeUntilNextRotation = 0
        self.status = self.BACK
    def reverse(self, e):
        self.status = self.REVERSING
    def fromCamera(self, e):
        if not self.app.inCam:
            self.app.fromCamera()
        
    def reset(self, e):
        self.moveList = [ ]
        self.moveIndex = 0
        self.shuffling = False
        self.showingPB = False
        self.state.setSolved()
        self.redraw()

    def solve(self, *args):
        try:
            solution = self.getSolution()
        except Exception as e:
            import traceback, sys
            txt = 'Error finding solution. Make sure your cube is configured legally and was input accurately.'
            print 'error:', e
            traceback.print_exc(file=sys.stdout)
            self.updateMessage(txt)
            self.redraw()
        else:
            if not self.showingPB:
                self.addMoves(solution, self.PLAYING)
                self.showingPB = True
                self.pbMin = len(self.moveList) - len(solution)
                self.pbMax = len(self.moveList)
                self.updateSol('With F as Red and U as Yellow: Solution: '+brief(solution))
            self.maxRot = 5
            self.timeBetweenRotations = 0
            self.timeUntilNextRotation = 0

    def guideThrough(self, *args):
        if not self.showingPB:
            self.solve()
        self.maxRot = 20
        self.timeBetweenRotations = 35
        self.timeUntilNextRotation = 15

    def guideFastThrough(self, *args):
        if not self.showingPB:
            self.solve()
        self.maxRot = 13
        self.timeBetweenRotations = 18
        self.timeUntilNextRotation = 5

    def shuffle(self, *args):
        self.showingPB = False
        n = self.shuffleLen
        delay = 5
        moves = ["U", "L", "D", "R", "F", "B",
                 "U'", "L'", "D'", "R'", "F'", "B'"
        ]
        moveList = [(random.choice(moves), "Shuffling step %d of %d" % (i+1,n)) for i in xrange(n)]
        self.addMoves(moveList, self.PLAYING)
        self.shuffling = True
        self.status = self.PLAYING

    def getSolution(self, method='beginner'):
        if method == 'beginner':
            solution = solutions.beginner3Layer(self.state.copy())
        return solution

class CubeState(object):
    """Container for a 3D list representing the cube's state.
Non-graphical; meant for algorithmic purposes."""

    # Each element is in the form (pieceID, orientationKey)
    # Orientation Keys:
        # CORNERS
            # 2 == Z
            # 1 == Y
            # 0 == X
        # orientationKey = [first priority][second priority][third priority]
        # 210 = ZYX
        # 021 = XZY
        # etc.

    solvedState = [[[ ( 1, 210), ( 2, 210), ( 3, 210) ],
                    [ ( 4, 210), ( 5, 210), ( 6, 210) ],
                    [ ( 7, 210), ( 8, 210), ( 9, 210) ]],

                   [[ (10, 210), (11, 210), (12, 210) ],
                    [ (13, 210), (14, 210), (15, 210) ],
                    [ (16, 210), (17, 210), (18, 210) ]],

                   [[ (19, 210), (20, 210), (21, 210) ],
                    [ (22, 210), (23, 210), (24, 210) ],
                    [ (25, 210), (26, 210), (27, 210) ]]]

    barebones = [[[          [],        [],        [] ],
                  [          [], ( 5, 210),        [] ],
                  [          [],        [],        [] ]],

                 [[          [], (11, 210),        [] ],
                  [ (13, 210), (14, 210), (15, 210) ],
                  [         [], (17, 210),         [] ]],

                 [[          [],        [],       [] ],
                  [          [], ( 23, 210),      [] ],
                  [          [],        [],       [] ]]]
    keys = { 2: Vector(0,0,1),
             1: Vector(0,1,0),
             0: Vector(1,0,0)}
    perpendiculars = { Vector(0,0,1): [0, 1],
                       Vector(0,1,0): [0, 2],
                       Vector(1,0,0): [1, 2]}

    movementCodes = solutions.MOVE_CODES
    movementKeys = {
                    "U": Vector(0,0,1),
                    "D": Vector(0,0,-1),
                    "L": Vector(-1,0,0),
                    "R": Vector(1,0,0),
                    "F": Vector(0,1,0),
                    "B": Vector(0,-1,0)
                  }

    def __init__(self, state='solved'):
        self.state = state
        self.size = 3
        if self.state == 'solved':
            self.setSolved()
        elif self.state == 'barebones':
            self.setBare()
    def __str__(self):
        s = ''
        for z in xrange(self.size):
            for y in xrange(self.size):
                for x in xrange(self.size):
                    item = str(self.state[z][y][x])
                    s += item
                s += '\n'
            s += '\n'
        return s

    def condense(self):
        s = 'State:'
        for z in xrange(self.size):
            for y in xrange(self.size):
                for x in xrange(self.size):
                    item = self.state[z][y][x]
                    item2 = str(item[0]) + "'" + str(item[1])
                    s += item2
                    s += ','
                s += ','
            s += ','
        return s

    @classmethod
    def getPerps(cls, p):
        for key in cls.perpendiculars:
            if key // p: return cls.perpendiculars[key]

    @staticmethod
    def kthDigit(num, k):
        num /= (10**k)
        return num % 10

    @staticmethod
    def swapDigits(num, i, j):
        ithDigit = CubeState.kthDigit(num, i)
        num -= ithDigit * int(10**i)
        jthDigit = CubeState.kthDigit(num, j)
        num -= jthDigit * int(10**j)
        num += ithDigit * int(10**j)
        num += jthDigit * int(10**i)
        return num

    def rotationInfo(self, axis):
        isNeg = False
        if type(axis) == str and "'" in axis:
            isNeg = True
            axis = axis[0]

        if type(axis) == str:
            axis = CubeState.movementKeys[axis]
  
        rotationIndcs = [ ]
        # find out the affected 9 blocks
        # put it into rotationIndcs
        for x in xrange(self.size):
            for y in xrange(self.size):
                for z in xrange(self.size):
                    pos = Vector(x-1,y-1,z-1)
                    #<0,1,0> == <1,1,1> returns [False,True,False]
                    #and the total bool value is True if any 'True' inside the list
                    if pos**axis > 0 and pos == axis:
                        rotationIndcs.append((x,y,z))
                      

        oldValues = { }
        for i in rotationIndcs:
            oldValues[i] = self.state[i[2]][i[1]][i[0]]

        rot = Struct()
        rot.rotationAxis = axis
        rot.rotatingValues =[val[0] for val in oldValues.values()]
        # totatingValues are only block indices from 1 to 27
        rot.rotationDirection = isNeg
        rot.oldValues = oldValues
        # oldValues is tuple like ((0, 2, 0): (7, 210) ... )
        rot.rotationIndcs = rotationIndcs
        # rotationIndcs is the (0,2,0)... part
        return rot

    def rotate(self, r):

        # Vector axis of rotation

        axis = r.rotationAxis
        isNeg = r.rotationDirection
        rotationIndcs = r.rotationIndcs
        oldValues = r.oldValues

        for idx in rotationIndcs:
            pos = Vector(idx[0]-1, idx[1]-1, idx[2]-1)
            #pos > axis is the project from pos to axis
            posn = pos - (pos > axis)
            #posn is the position vector projection on
            #the rotated surface
            newn = axis * posn
            #A*B=A x B. The above is vector cross multiply
            #which means posn rotate around axis clockwise

            if isNeg:
                newn = newn * -1.
            new = newn + (pos > axis)
            # new is the rotated vector, projected back to
            # the rotated surface

            # Alter the rotationkey
            (oldId, oldKey) = oldValues[idx]
            perps = CubeState.getPerps(axis)
            toSwap = [ ]
            for perp in perps:
                for i in xrange(self.size):
                    if CubeState.kthDigit(oldKey, i) == perp:
                        toSwap.append(i)
            newKey = CubeState.swapDigits(oldKey, *toSwap)
            newValue = (oldId, newKey)

            newi = (int(new.x+1), int(new.y+1), int(new.z+1))
            self.state[newi[2]][newi[1]][newi[0]] = newValue

    def copy(self):
        return CubeState(copy.deepcopy(self.state))

    def setBare(self):
        self.state = copy.deepcopy(CubeState.barebones)

    def setSolved(self):
        self.state = copy.deepcopy(CubeState.solvedState)
