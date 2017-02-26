# app.py
# Chris Barker
# CMU S13 15-112 Term Project

import Tkinter
from Tkinter import N, E, S, W, ALL, BOTH

class App(object):
    """ docstring """
    def __init__(self, width=1280, height=720, name='App', bgColor = '#000000'):
        (self.width, self.height) = width, height
        self.name = name
        
        self.clock = 0
        self.dragging = False
        self.dragVal = (0,0)
        self.prevMouse = (0,0)
        self.bgColor = bgColor

        self.createWindow()
        self.bindEvents()
        self.initWrapper()
        self.timerWrapper()
        
        self.root.mainloop()
        
    def createWindow(self):
        self.root = Tkinter.Tk()
        self.root.title(self.name)
        self.canvas = Tkinter.Canvas(self.root, width=self.width,
                                     height=self.height, background=self.bgColor)
        self.canvas.pack(expand=True, fill=BOTH)
        
    def unbindAll(self):
        for event, tag in self.bindings:
            self.root.unbind(event, tag)
        self.bindings = [ ]
        
    def quit(self):
        self.unbindAll()
        self.canvas.after_cancel(self.after)
        self.root.quit()
        
    def bindEvents(self):
        self.bindings = [ ('<Button-1>', self.mousePressedWrapper),
            ('<KeyPress>', self.keyPressedWrapper),
            ('<KeyRelease>', self.keyReleasedWrapper),
            ('<ButtonRelease-1>', self.mousePressedWrapper),
            ('<B1-Motion>', self.mouseMovedWrapper),
        ]
        
        for i in xrange(len(self.bindings)):
            event = self.bindings[i][0]
            fn = self.bindings[i][1]
            # Store the binding as the event name and the Tkinter tag
            self.bindings[i] = (event, self.root.bind(event, fn))
            
    def initWrapper(self):
        self.delay = 20
        self.init()
    def init(self): pass
    
    def timerFired(self): pass
    def timerWrapper(self):
        self.redrawAllWrapper()
        self.timerFired()
        self.clock += 1
        self.after = self.canvas.after(self.delay, lambda: self.timerWrapper())
    
    def redrawAll(self): pass
    def redrawAllWrapper(self):
        self.redrawAll()

    def keyPressed(self, event): pass        
    def keyPressedWrapper(self, event):
        if event.keysym == 'Escape':
            if hasattr(self, 'cube'):
                if self.cube.helpState != self.cube.INGAME:
                    self.cube.helpState = self.cube.INGAME
                    self.cube.redraw()
                    return
            self.quit()
        else:
            self.keyPressed(event)
            if hasattr(self, 'inCam'):
                if self.inCam:
                    print event.keysym
            self.redrawAllWrapper()

    def keyReleased(self, event): pass
    def keyReleasedWrapper(self, event):
        self.keyReleased(event)
        self.redrawAllWrapper()
        
    def mousePressed(self, event): pass
    def mousePressedWrapper(self, event):
        self.dragging = True
        #self.dragVal = (0,0)
        self.prevMouse = (event.x, event.y)
        self.mousePressed(event)

    def mouseMoved(self, event): pass
    def mouseMovedWrapper(self, event):
        ndx = self.dragVal[0] if abs(self.dragVal[0]) > abs(event.x-self.prevMouse[0]) else (event.x-self.prevMouse[0])
        ndy = self.dragVal[1] if abs(self.dragVal[1]) > abs(event.y-self.prevMouse[1]) else (event.y-self.prevMouse[1])
        self.dragVal = (ndx, ndy)
        self.prevMouse = (event.x, event.y)
        self.mouseMoved(event)

    def mouseReleased(self, event): pass
    def mouseReleasedWrapper(self, event):
        self.mouseReleased(event)
        self.dragging = False

    def __str__(self):
        return 'App object size %sx%s' % (self.width, self.height)
