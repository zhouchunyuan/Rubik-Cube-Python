# solutions.py
# Chris Barker
# CMU S13 15-112 Term Project

# Some code in this module is adapted from color_histogram.py,
# which is provided in the OpenCV-2.4.4 release
# Go here for OpenCV downloads: http://opencv.org/downloads.html
# The code that I did not write is clearly marked as follows:

            # I did not write this code:
            ##############################
            # " Code I didn't write"
            ##############################

# I also did not write any of the numpy, cv, cv2, video, 
# sys, Tkinter, or getopt modules.

import numpy as np
import cv2
import video
import sys
import getopt
from coloranalytics import colorByHSV, colorByRGB, colorByRGB2
#from Tkinter import Label
from geometry import *

fnt = cv2.FONT_HERSHEY_PLAIN
fntScale = 0.5

# Quick mapping from string to hex for cube sticker colors
colorCodes = {
    'red': '#ff0000',
    'green': '#00ff00',
    'blue': '#0000ff',
    'orange': '#ff8800',
    'yellow': '#ffff00',
    'white': '#ffffff',
    'gray': '#888888'
}

# Object attribute container
class Struct(): pass

def colorTuple(s):
    # Converts a color string to a color tuple.

    if type(s) == tuple:
        return s
    elif type(s) != str:
        # fallback value
        s = '#888888'

    s = s.lower()
    if s[0] != '#':
        if s in colorCodes:
            s = colorCodes[s]
        else:
            # fallback value
            s = '#888888'

    base = 0x10
    red = int(s[1:3], base)
    green = int(s[3:5], base)
    blue = int(s[5:7], base)
    return (blue, green, red) # OpenCV uses BGR

def selectionColor(x, y, data):
    # Takes a click (x,y) and returns the color of the palette at that point
    if (data.colorSelectionStartY <= y <= 
        data.colorSelectionStartY + data.colorSelectionHeight):
        xNow = data.colorSelectionStartX
        for color in data.colorSelections:
            if xNow <= x <= xNow + data.colorSelectionWidth:
                return color
            xNow += data.colorSelectionWidth

def suff(i):
    return 'st' if i==1 else 'nd' if i==2 else 'rd' if i==3 else 'th'

def onMouse(e, x, y, flags, param, data):
    if e == 0:
        # Movement
        pass
    elif e == 1:
        # Click down
        pass
    elif e == 4:
        # Release mouse button
        index = data.cube.faceClicked(x, y)
        #print 'index', index
        if index is not None:
            data.showingSelector = True
            #print 'now showing selector!'
            data.selectionIndex= index
        else:
            if data.showingSelector:
                newColor = selectionColor(x, y, data)
                if newColor is not None:
                    data.cube.setColor(data.selectionIndex, newColor)

class Streamer(object):
    def __init__(self, stream):
        self.index = 0
        self.stream = stream
    def __iter__(self):
        return self
    def next(self):
        while self.index != len(self.stream.events):
            if self.stream.events[self.index][0] == 'face':
                break
            self.index += 1
        else:
            raise StopIteration
        
        prevTurnIndex = self.index
        prevTurn = None
        while prevTurnIndex >= 0:
            if self.stream.events[prevTurnIndex][0] == 'turn':
                prevTurn = self.stream.events[prevTurnIndex][1]
                break
            prevTurnIndex -= 1

        prevFaceIndex = self.index - 1
        prevFace = None
        while prevFaceIndex >= 0:
            if self.stream.events[prevFaceIndex][0] == 'face':
                prevFace = self.stream.events[prevFaceIndex][1]
                break
            prevFaceIndex -= 1

        nextTurnIndex = self.index
        nextTurn = None
        while nextTurnIndex < len(self.stream.events):
            if self.stream.events[nextTurnIndex][0] == 'turn':
                nextTurn = self.stream.events[nextTurnIndex][1]
                break
            nextTurnIndex += 1

        nextFaceIndex = self.index + 1
        nextFace = None
        while nextFaceIndex < len(self.stream.events):
            if self.stream.events[nextFaceIndex][0] == 'face':
                nextFace = self.stream.events[nextFaceIndex][1]
                break
            nextFaceIndex += 1

        currentFace = self.stream.events[self.index][1]

        data = Struct()
        data.currentFace = currentFace
        data.prevFace = prevFace
        data.nextFace = nextFace
        data.prevTurn = prevTurn
        data.nextTurn = nextTurn

        self.index += 1

        return data

class Stream(object):
    def __init__(self):
        self.events = [ ]
    def logFace(self, a):
        L = [ a[:3], a[3:6], a[6:] ]
        self.events.append(('face', L))
    def logTurn(self, turn):
        self.events.append(('turn', turn))
    def __iter__(self):
        return Streamer(self)

def averageRGB(img):
    red = 0
    green = 0
    blue = 0
    num = 0
    for y in xrange(len(img)):
        if y%10 == 0:
            a = img[y]
            for x in xrange(len(a)):
                if x%10 == 0:
                    b = img[y][x]
                    num += 1
                    red += b[0]
                    green += b[1]
                    blue += b[2]
    red /= num
    green /= num
    blue /= num
    return (red, green, blue)
    #return (blue, green, red)

def histMode(hist, maxAmt):
    bin_count = int(hist.shape[0])
    maxAmount = int(hist[0])
    maxIndex = 0
    numZero = 0
    numTotal = 0
    for i in xrange(bin_count):
        h = int(hist[i])
        if h == 0: numZero += 1
        numTotal += 1
        if h > maxAmount:
            maxIndex = i
            maxAmount = h
    val = int(maxAmt * maxIndex / bin_count)
    return val

class DemoCube(object):
    directions = (K_HAT, J_HAT, I_HAT, -J_HAT, -I_HAT, -K_HAT)
    ups = (-J_HAT, K_HAT, K_HAT, K_HAT, K_HAT, -I_HAT)
    rights = (I_HAT, I_HAT, -J_HAT, -I_HAT, J_HAT, J_HAT)

    def __init__(self):
        self.colors = ['gray'] * 54
        self.grabbedColors = ['gray'] * 54
        (self.width, self.height) = (400, 500)
        self.dim = {'width': self.width, 'height': self.height}
        self.faceIndex = 0
        self.transitionSpeed = 1
        self.camera = Camera(Vector(2, -4, 10), Vector(0,0,0), pi/5, self.dim)

        #added for indicating box
        #flashing
        self.waitingColor = False # wait for changing color
        self.flashLight = False

    @staticmethod
    def faceInfo(i):
        faceIndex = i / 9
        norm = DemoCube.directions[faceIndex]
        up = DemoCube.ups[faceIndex]
        right = DemoCube.rights[faceIndex]
        faceCenter = norm * 1.5
        faceCenter = faceCenter - ((i / 3)%3 - 1) * up
        faceCenter = faceCenter - (i%3 - 1) * right
        return (faceCenter, norm, up, right)

    def adjustCamera(self):
        destination = (DemoCube.directions[self.faceIndex]) ^ 1
        current = (self.camera.view) ^ 1
        
        delta = destination ** current
        if delta >0.9 :
            factor = 40# 180 dgree turn need large movement at first
        else:
            factor = (delta+1)*3.0+1 # ratation speed
            
        currentPos = self.camera.pos
        destinationPos = self.camera.origin + destination * (currentPos.mag)
        deltaY = destinationPos ** self.camera.up
        deltaX = destinationPos ** self.camera.right
        deltaX *= 0.1*factor
        deltaY *= 0.1*factor
        self.camera.rotate((deltaX, deltaY))

            
    def faceClicked(self, x, y):
        for i in xrange(len(self.colors)):
            (center, norm, up, right) = self.faceInfo(i)
            if norm ** (center - self.camera.pos) < 0:
                corners = (center + up * 0.5 + right * 0.5,
                           center + up * 0.5 - right * 0.5,
                           center - up * 0.5 - right * 0.5,
                           center - up * 0.5 + right * 0.5)
                corners = [corner.flatten(self.camera) for corner in corners]
                corners = [(int(corner[0]), int(corner[1])) for corner in corners]
                for corner in xrange(len(corners) - 1):
                    prev = (corner - 1) % len(corners)
                    cursor = Vector(x - corners[corner][0], y - corners[corner][1], 0)
                    prevVect = Vector(corners[prev][0] - corners[corner][0],
                                      corners[prev][1] - corners[corner][1], 0)
                    nextVect = Vector(corners[corner+1][0] - corners[corner][0],
                                      corners[corner+1][1] - corners[corner][1], 0)
                    if ((prevVect * cursor) ** (cursor * nextVect) < 0):
                        break
                else:
                    return i

    def draw(self, vis):
        self.adjustCamera()
        for i in xrange(len(self.colors)):
            (center, norm, up, right) = self.faceInfo(i)
            if norm ** (center - self.camera.pos) < 0:
                corners = (center + up * 0.5 + right * 0.5,
                           center + up * 0.5 - right * 0.5,
                           center - up * 0.5 - right * 0.5,
                           center - up * 0.5 + right * 0.5)
                corners = [corner.flatten(self.camera) for corner in corners]
                corners = [(int(corner[0]), int(corner[1])) for corner in corners]
#                cv.FillConvexPoly(cv.fromarray(vis), 
#                    corners, colorTuple(self.colors[i]), lineType=4, shift=0)
                points = np.array(corners)
                cv2.fillConvexPoly(np.asarray(vis), 
                    points, colorTuple(self.colors[i]), lineType=4, shift=0)


        for i in xrange(len(self.colors)):
            (center, norm, up, right) = self.faceInfo(i)
            if norm ** (center - self.camera.pos) < 0:
                corners = (center + up * 0.5 + right * 0.5,
                           center + up * 0.5 - right * 0.5,
                           center - up * 0.5 - right * 0.5,
                           center - up * 0.5 + right * 0.5)
                corners = [corner.flatten(self.camera) for corner in corners]
                corners = [(int(corner[0]), int(corner[1])) 
                            for corner in corners]

                for j in xrange(len(corners)):
                    k = (j + 1) % (len(corners))
#                    cv.Line(cv.fromarray(vis), corners[j], corners[k], (0,0,0))
                    cv2.line(np.asarray(vis), corners[j], corners[k], (0,0,0))

        ############# plot color map ###########
        w = 20
        xoffset = 20
        yoffset = 20

        # in waiting color phase, do not update grabbedcolor
        # it helps to compare the grabbed colors to calculated ones
        # does not work with self.grabbedColors = self.colors
        if not self.waitingColor :
            for i in xrange(len(self.colors)):
                self.grabbedColors[i] = self.colors[i]
        
        for i in xrange(len(self.grabbedColors)):
            # 2 layers, each layer contains 27 blocks
            # inverse x, so use 3-i
            # gap 30 between each 2 9-block
            x = 2-i%3+(i/3)*3 # inverse x for each line
            xgap = (x%27)/9*w*3 + (x%3)*5 + ((x%27)/9)*30

            ####   3x3 height  9 for each    gap 30
            ygap = i/27*w*3 + ((i%9)/3)*5 + (i/27)*30
            x0 = w*(x%3)+xoffset + xgap
            x1 = x0+w
            y0 = w*((i%9)/3)+self.height+yoffset+ygap
            y1 = y0+w
            cv2.rectangle(np.asarray(vis),(x0,y0),(x1,y1),colorTuple(self.grabbedColors[i]),-1)
        ##### indicate the current face ##########
        x0 = xoffset + self.faceIndex%3 * (w*3+30)
        y0 = yoffset + self.height + self.faceIndex/3 * (w*3+30)
        x1 = x0 +w*3+10
        y1 = y0 +w*3+10

        #test if camera is stable
        destination = (DemoCube.directions[self.faceIndex]) ^ 1
        current = (self.camera.view) ^ 1
        if destination ** current < -0.8:
            self.flashLight = True
        else:
            self.flashLight = not self.flashLight
        cv2.rectangle(np.asarray(vis),(x0,y0),(x1,y1),(0,255*self.flashLight,0))
##        if self.waiting :
##            cv2.rectangle(np.asarray(vis),(x0,y0),(x1,y1),(0,255,255))
        ##### ######################### ##########
    def setColors(self, colors, faceIndex):
        if faceIndex > 5:
            return
        i = faceIndex * 9
        for c in colors:
            self.colors[i] = c
            i += 1

    def setColor(self, index, color):
        self.colors[index] = color

    def toStream(self):
        stream = Stream()
        stream.logFace(self.colors[:9])
        stream.logTurn('up')
        stream.logFace(self.colors[9:18])
        stream.logTurn('right')
        stream.logFace(self.colors[18:27])
        stream.logTurn('right')
        stream.logFace(self.colors[27:36])
        stream.logTurn('right')
        stream.logFace(self.colors[36:45])
        stream.logTurn('up')
        stream.logFace(self.colors[45:])

##        stream.events = [('face', [['orange', 'red', 'orange'],
##                                   ['orange', 'orange', 'orange'],
##                                   ['orange', 'orange', 'orange']]),
##                         ('turn', 'up'),
##                         ('face', [['white', 'white', 'white'],
##                                   ['white', 'white', 'white'],
##                                   ['white', 'white', 'white']]),
##                         ('turn', 'right'),
##                         ('face', [['green', 'green', 'green'],
##                                   ['orange', 'green', 'green'],
##                                   ['green', 'green', 'green']]),
##                         ('turn', 'right'),
##                         ('face', [['yellow', 'yellow', 'yellow'],
##                                   ['yellow', 'yellow', 'yellow'],
##                                   ['yellow', 'yellow', 'yellow']]),
##                         ('turn', 'right'),
##                         ('face', [['blue', 'blue', 'blue'],
##                                   ['blue', 'blue', 'blue'],
##                                   ['blue', 'blue', 'blue']]),
##                         ('turn', 'up'),
##                         ('face', [['red', 'red', 'red'],
##                                   ['red', 'red', 'green'],
##                                   ['red', 'red', 'red']])]
        
##        stream.events = [('face', [['orange', 'orange', 'orange'],
##                                   ['orange', 'orange', 'orange'],
##                                   ['orange', 'orange', 'orange']]),
##                         ('turn', 'up'),
##                         ('face', [['white', 'white', 'white'],
##                                   ['white', 'white', 'white'],
##                                   ['white', 'white', 'white']]),
##                         ('turn', 'right'),
##                         ('face', [['green', 'green', 'green'],
##                                   ['green', 'green', 'green'],
##                                   ['green', 'green', 'green']]),
##                         ('turn', 'right'),
##                         ('face', [['yellow', 'yellow', 'yellow'],
##                                   ['yellow', 'yellow', 'yellow'],
##                                   ['yellow', 'yellow', 'yellow']]),
##                         ('turn', 'right'),
##                         ('face', [['blue', 'blue', 'blue'],
##                                   ['blue', 'blue', 'blue'],
##                                   ['blue', 'blue', 'blue']]),
##                         ('turn', 'up'),
##                         ('face', [['red', 'red', 'red'],
##                                   ['red', 'red', 'red'],
##                                   ['red', 'red', 'red']])]
##        stream.events = [('face', [['yellow', 'red', 'white'],
##                                   ['yellow', 'orange', 'white'],
##                                   ['yellow', 'orange', 'white']]),
##                         ('turn', 'up'),
##                         ('face', [['orange', 'white', 'red'],
##                                   ['orange', 'white', 'red'],
##                                   ['green', 'green', 'green']]),
##                         ('turn', 'right'),
##                         ('face', [['green', 'orange', 'green'],
##                                   ['green', 'green', 'green'],
##                                   ['orange', 'yellow', 'red']]),
##                         ('turn', 'right'),
##                         ('face', [['orange', 'yellow', 'red'],
##                                   ['orange', 'yellow', 'red'],
##                                   ['blue', 'blue', 'blue']]),
##                         ('turn', 'right'),
##                         ('face', [['blue', 'blue', 'blue'],
##                                   ['blue', 'blue', 'blue'],
##                                   ['orange', 'white', 'red']]),
##                         ('turn', 'up'),
##                         ('face', [['white', 'red', 'yellow'],
##                                   ['white', 'red', 'yellow'],
##                                   ['white', 'green', 'yellow']])]
##        stream.events = [('face', [['green', 'yellow', 'green'],
##                                   ['red', 'white', 'red'],
##                                   ['orange', 'yellow', 'orange']]),
##                         ('turn', 'up'),
##                         ('face', [['yellow', 'red', 'yellow'],
##                                   ['white', 'red', 'white'],
##                                   ['yellow', 'blue', 'yellow']]),
##                         ('turn', 'right'),
##                         ('face', [['orange', 'green', 'blue'],
##                                   ['green', 'green', 'red'],
##                                   ['orange', 'green', 'blue']]),
##                         ('turn', 'right'),
##                         ('face', [['white', 'orange', 'white'],
##                                   ['yellow', 'orange', 'yellow'],
##                                   ['white', 'green', 'white']]),
##                         ('turn', 'right'),
##                         ('face', [['green', 'blue', 'red'],
##                                   ['orange', 'blue', 'blue'],
##                                   ['green', 'blue', 'red']]),
##                         ('turn', 'up'),
##                         ('face', [['red', 'orange', 'blue'],
##                                   ['white', 'yellow', 'white'],
##                                   ['red', 'orange', 'blue']])]
        return stream



def cubeFromCam(app=None, callback=None):

    # I did not write this code:
    ##############################
    try:
        video_src = sys.argv[1]
    except:
        video_src = 0
    ##############################

    data = Struct()

    data.app = app
    data.after = None
    data.waiting = False
    data.callback = callback

    # I did not write this code:
    ##############################
    data.cam = video.create_capture(video_src)
    cv2.namedWindow('Cube Input')
    ##############################


    

    data.stream = Stream()
    data.delay = 20
    data.colorSelections = ['red', 'orange', 'yellow', 
                            'green', 'blue', 'white']
    data.colorSelectionStartX = 20
    data.colorSelectionStartY = 400
    data.colorSelectionWidth = 40
    data.colorSelectionHeight = 40
    data.cube = DemoCube()
    data.numLogged = 0
    data.showingSelector = False
    data.selectionIndex= 0
    mouse = lambda e,x,y,f,p: onMouse(e,x,y,f,p, data)
    cv2.setMouseCallback('Cube Input', mouse)

    (x, y, dx, dy, margin, rows, cols) = (400, 100, 100, 100, 10, 3, 3)
#    (x, y, dx, dy, margin, rows, cols) = (100, 100, 150, 150, 10, 3, 3)
    data.regions = [ ]
    for row in xrange(rows):
        for col in xrange(cols):
            data.regions.append((x + col * dx + margin,
                                 y + row * dy + margin,
                                 x + (col + 1) * dx - margin,
                                 y + (row + 1) * dy - margin))

    while timer(data): pass

def timer(data):

    # I did not write this code:
    ##############################
    ret, frame = data.cam.read()
    vis = np.zeros((800,1250,3), np.uint8)
    #vis = frame.copy()

    # copy camera video into vis
    x_offset=400
    y_offset=100
    vis[y_offset:y_offset+frame.shape[0], x_offset:x_offset+frame.shape[1]] = frame


    
    #hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv = cv2.cvtColor(vis, cv2.COLOR_BGR2HSV)

    mask = cv2.inRange(hsv, np.array((0., 10., 50.)),
                            np.array((180., 255., 255.)))
    ##############################

    mask2 = cv2.inRange(hsv, np.array((0., 0., 0.)), 
                             np.array((180., 255., 255.)))

    texts = [ ]
    colors = [ ]
    debugIndex = 0
    for (x0, y0, x1, y1) in data.regions:
        (w, h) = (x1 - x0, y1 - y0)
        (x0m, y0m, x1m, y1m) = (x0 + w/5, y0 + h/5, x1 - w/5, y1 - h/5)
        debugIndex +=1
        # I did not write this code:
        ##############################
        hsv_roi = hsv[y0m:y1m, x0m:x1m]
        mask_roi = mask[y0m:y1m, x0m:x1m]
        ##############################

        mask_roi2 = mask2[y0m:y1m, x0m:x1m]

        # I did not write this code:
        ##############################
        histHue = cv2.calcHist( [hsv_roi], [0], mask_roi, [50], [0, 180] )
        ##############################

        histSat = cv2.calcHist( [hsv_roi], [1], mask_roi2, [50], [0, 180] )
        histVal = cv2.calcHist( [hsv_roi], [2], mask_roi2, [50], [0, 180] )

        # I did not write this code:
        ##############################
        cv2.normalize(histHue, histHue, 0, 255, cv2.NORM_MINMAX);
        histHue = histHue.reshape(-1)
        ##############################

        histSat = histSat.reshape(-1)
        histVal = histVal.reshape(-1)

        hue = histMode(histHue, 180.)
        sat = histMode(histSat, 255.)
        val = histMode(histVal, 255.)

        rgb_inRegion = vis[y0m:y1m, x0m:x1m]

        avghsv = (hue, sat, val)
        avgrgb = averageRGB(rgb_inRegion)

        ###################################
            
        myrgb = np.uint8([[avgrgb]])
        myhsv = cv2.cvtColor(myrgb,cv2.COLOR_BGR2HSV)
        #print myrgb,myhsv,avghsv
        [[[h,s,v]]] = myhsv

        myavghsv = np.uint8([[avghsv]])
        [[[b,g,r]]] = cv2.cvtColor(myavghsv,cv2.COLOR_HSV2BGR)
        rgb_hsv = (int(b),int(g),int(r))

        #print myrgb,myhsv,avghsv
        
        color = colorByRGB2(avgrgb, h,s,v)#avghsv)

        #it is both ok to use 'green' or to use(0,255,0)
        #colors.append(color)
        colors.append(avgrgb)
        
        cv2.rectangle(vis, (x0, y0), (x1, y1), (255, 255, 255))
        cv2.circle(vis, ((x0+x1) / 2, (y0 + y1) / 2), 10, rgb_hsv, -1)

        outText = str(color)
        textSize = cv2.getTextSize(outText,fnt,fntScale,1)[0]
        tw = textSize[0]
        texts.append((vis.shape[1] -(x0+x1) / 2 - tw/2, (y0 + y1) / 2, outText))

        outText = str((h,s,v))
        textSize = cv2.getTextSize(outText,fnt,fntScale,1)[0]
        tw = textSize[0]
        texts.append((vis.shape[1] -(x0+x1) / 2 - tw/2, (y0 + y1) / 2 + 20, outText))
            

    vis = vis[::,::-1].copy()

    for (x, y, color) in texts:
        fill = (255,255,255) if color in ('blue', 'green', 'red') else (0,0,0)
        cv2.putText(vis, color, (x, y), fnt, fntScale, fill)

    cv2.rectangle(vis, (0, 0), (400, 1200), (0,0,0), -1)
    wid = vis.shape[1]
    cv2.rectangle(vis, (wid-400, 0), (wid, 1200), (0,0,0), -1)

    data.cube.setColors(colors, data.numLogged)
    data.cube.draw(vis)

    if data.waiting:
        help = ["Press spacebar to advance", 
                "to the next face.", 
                "or click on a square", 
                "to change its color."]
    else:
        i = data.numLogged+1
        help = ["Press spacebar to", 
                "lock this face.",
                "You may manually adjust", 
                "the cube once it is locked.",
                "You are currently logging the %d%s face." % (i, suff(i))]

    startY = 25
    startX = 25

    for h in help:
        white = (255,255,255)
        cv2.putText(vis, h,(startX, startY), fnt, 1, white)
        startY += 20

    tips = [ "Red looks like orange?",
    "Move somewhere with more light.",
    "Non-white looks like white?",
    "Tilt your cube up, down, left, or right.",
    "Still not working",
    "Press spacebar and then click on the",
    "incorrect color to manually select the",
    "color it should be.",
    "",
    "Press ESC to close this window."
    ]

    startY = 25
    startX = wid - 375

    for tip in tips:
        white = (255,255,255)
        cv2.putText(vis, tip, (startX, startY), fnt, 1, white)
        startY += 20

    if data.showingSelector:
        xNow = data.colorSelectionStartX
        yNow = data.colorSelectionStartY
        (wNow, hNow) = (data.colorSelectionWidth, data.colorSelectionHeight)
        for colorSelect in data.colorSelections:
            p1 = (xNow, yNow)
            p2 = (xNow + wNow, yNow + hNow)
            cv2.rectangle(vis, p1, p2, colorTuple(colorSelect), -1)
            xNow += wNow

    # I did not write this code:
    ##############################
    cv2.imshow('Cube Input', vis)

    ch = 0xff & cv2.waitKey(20) # Gets keyboard input
    ##############################

    if ch == 32: # Spacebar
##        #if data.cube.faceIndex <5 :
##        data.showingSelector = False
##        if data.waiting:
##            data.cube.faceIndex += 1
##        else:
##            data.stream.logFace(colors)
##            data.numLogged += 1
##        data.waiting = not data.waiting
##
##        if data.numLogged in (1, 5):
##            data.stream.logTurn('up')
##        else:
##            data.stream.logTurn('right')
##            
##        # to give waiting signal to cube
##        # to flash the indicating box
##        data.cube.waiting = data.waiting
        data.cube.faceIndex += 1
        if not data.cube.waitingColor:
            data.showingSelector = False
            data.stream.logFace(colors)
            data.numLogged += 1
            if data.numLogged in (1, 5):
                data.stream.logTurn('up')
            else:
                data.stream.logTurn('right')
            
        if data.numLogged == 6:

            data.cube.waitingColor = True
            demoCube = data.cube
            doit(demoCube)
            
            
        if data.cube.waitingColor:
            data.cube.faceIndex = data.cube.faceIndex % 6
   
    if ch == 27 : # Escape key
        
        data.numLogged = 6
        data.cube.faceIndex = 6
        
        data.callback(data.cube.toStream())
        #obj = data.cube.toStream()
        #print obj.events
        
        data.cam.release()
        # I did not write this code:
        ##############################
        cv2.destroyAllWindows()
        ##############################
        return False

    return True

def doit(demoCube):

           
    class centerColor():
        def __init__(self, s):
            self.colorName = s
            self.color = colorTuple(s)
            self.pureVector = Vector(self.color[0],self.color[1],self.color[2])# color expressed in vector
            self.faceIndex = -1
            self.realVector = self.pureVector# color expressed in vector
            self.norm = Vector(0,0,0)
            
        def getPosition(self):
            if self.faceIndex != -1:
                return 4 + self.faceIndex*9

        def setFaceInfoByNorm(self,config):
            for i,d in enumerate(DemoCube.directions):
                if d.isEqual(self.norm):
                    self.faceIndex = i
                    break
            for i,faceInfo in enumerate(config) :
                if self.faceIndex == i:
                    color = faceInfo.currentFace[1][1]
                    (r,g,b) = colorTuple(color)
                    self.realVector = Vector(r,g,b)
                    break
            
        def findMostPossibleCenterPosition(self,config):
            # config is from Stream() class
            # the colors are in the events string
            # but it also has 'data' in each faceInfo
            maxCorr = 0
            for i,faceInfo in enumerate(config) :
                color = faceInfo.currentFace[1][1]

                #the color can be names
                (r,g,b) = colorTuple(color)
                vec = Vector(r,g,b)
                #d = abs(2 - float(r+b)/g)
                #print i,(r,g,b)
                corr = centerColor.corrRgb(vec,self.pureVector)
                if maxCorr < corr:
                    maxCorr = corr
                    self.faceIndex = i
                    self.realVector = vec
                    self.norm = DemoCube.directions[i]

                
        @staticmethod        
        def most9similarColors(config):
            cells = [] # [(index,color,correlation)]
            for i,color in enumerate(demoCube.colors) :
                (r,g,b) = colorTuple(color)
                vec = Vector(r,g,b)
                corr = 0 #centerColor.corr(vec,self.realVector)
                cells.append([i,vec,corr])

                
            used = set()
            for FACE in FACES:# first draw centers
                demoCube.setColor(FACE[0].getPosition(),FACE[0].colorName)
                used.add(FACE[0].getPosition())
                
            for FACE in FACES:
                for i,cell in enumerate(cells):
                    vec = cell[1]
                    if FACE[0]==RED or FACE[0]==ORANGE :
                        corr = centerColor.corrHsv( vec,FACE[0].realVector )
                    else:
                        corr = centerColor.corrRgb( vec,FACE[0].realVector )
                    cells[i][2] = corr
                cells.sort(key = lambda cell : cell[2], reverse=True)
                i=0
                for cell in cells:
                    if cell[0] not in used:
                        demoCube.setColor( cell[0],FACE[0].colorName)
                        used.add(cell[0])
                        i +=1
                    if i== 8 : break

        # correlation between 2 vectors
        # equals to cos(angle)=<a.b>/|a|.|b|        
        @staticmethod
        def corrRgb(a,b):
            if type(a)==Vector and type(b)==Vector :
                return a ** b / (a.mag * b.mag)
            else:
                raise Exception('all vectors needed!')
            
        @staticmethod
        def rgb2hsv(r,g,b):
            rgb = np.uint8([[(r,g,b)]])
            hsv = cv2.cvtColor(rgb,cv2.COLOR_BGR2HSV)
            [[[h,s,v]]]=hsv
            return (h,s,v)

        # correlation between 2 HSV vectors
        # equals to cos(angle)=<a.b>/|a|.|b|        
        @staticmethod
        def corrHsv(a,b):
            if type(a)==Vector and type(b)==Vector :
                (x1,y1,z1) = centerColor.rgb2hsv(a.z,a.y,a.x)
                (x2,y2,z2) = centerColor.rgb2hsv(b.z,b.y,b.x)
                A = Vector(x1,y1,z1)
                B = Vector(x2,y2,z2)
                return A ** B / (A.mag * B.mag)
            else:
                raise Exception('all vectors needed!')
            
        # correlation between 2 vectors in 4-dimention
        @staticmethod
        def corr1(a,b):
            if type(a)==Vector and type(b)==Vector :
                A = a.x*b.x + a.y*b.y + a.z*b.z + a.mag*b.mag
                B = (a.x*a.x + a.x*a.x + a.z*a.z + a.mag*a.mag)*(b.x*b.x + b.y*b.y + b.z*b.z + b.mag*b.mag)
                B = B**0.5
                return A/B
            else:
                raise Exception('all vectors needed!')


            
            
    WHITE   = centerColor('white')
    GREEN   = centerColor('green')
    RED     = centerColor('red')
    ORANGE  = centerColor('orange')
    BLUE    = centerColor('blue')
    YELLOW  = centerColor('yellow')

    # if we want to use objects in list, the elements must
    # be in []. Does not work if:
    # FACES = [WHITE,RED,YELLOW,BLUE,GREEN,ORANGE]
    FACES = [[WHITE],[GREEN],[YELLOW],[BLUE],[RED],[ORANGE]]
    
    config = demoCube.toStream()

    WHITE.findMostPossibleCenterPosition(config)
    GREEN.findMostPossibleCenterPosition(config)
   
    if ( WHITE.faceIndex == GREEN.faceIndex):
        print 'green is too similar to white'
    if ( WHITE.norm // GREEN.norm):
        print 'White face is parallel to green face, which is wrong!'
    else:
        # the cross multiply of face directions
        # white.face x grean.face => red.face
        
        RED.norm =  WHITE.norm * GREEN.norm
        RED.setFaceInfoByNorm(config)

        #print RED.norm, RED.faceIndex
        
        ORANGE.norm = - RED.norm
        ORANGE.setFaceInfoByNorm(config)

        #print ORANGE.norm, ORANGE.faceIndex
        
        BLUE.norm = -GREEN.norm
        BLUE.setFaceInfoByNorm(config)
        
        YELLOW.norm = -WHITE.norm
        YELLOW.setFaceInfoByNorm(config)
        #print 'red' ,RED.getPosition(), RED.color
        #print 'orange',ORANGE.getPosition(), ORANGE.color
##        demoCube.setColor(RED.getPosition(), RED.color)
##        demoCube.setColor(ORANGE.getPosition(), ORANGE.color)
##        demoCube.setColor(BLUE.getPosition(), BLUE.color)
##        demoCube.setColor(YELLOW.getPosition(), YELLOW.color)
##        demoCube.setColor(WHITE.getPosition(), WHITE.color)
##        demoCube.setColor(GREEN.getPosition(), GREEN.color)



        centerColor.most9similarColors(config)

if __name__ == '__main__':
    cubeFromCam()
