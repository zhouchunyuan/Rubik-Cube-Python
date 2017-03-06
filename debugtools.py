# debugtools.py
# by Chunyuan March 2017

from cube import Cube,CubeState 

def show_state(cubeState):
    cells = cubeState#self.cube.state.state
    for z in xrange(3):
        for y in xrange(3):
            for x in xrange(3):
                pieceID = cells[z][y][x][0]
                orientation = cells[z][y][x][1]
                color = Cube.faceColors[pieceID]
                #wybgor
                ccode = '|'.join([ c[:1] for c in color])
                #using "{:<2}".format(str(pieceID)) to pad
                print "{:>2}".format(str(pieceID)),
                print "{:>3}".format(str(orientation)),
                print "({:^5})".format(ccode),
            print ''
        print ''

# expand all faces to confirm orienatation
def show_all_faces(cubeState): # need self.cube.state.state           
                       
            cells = cubeState
            keys = CubeState.keys
            #keys = { 2: Vector(0,0,1),
            #         1: Vector(0,1,0),
            #         0: Vector(1,0,0)}

            # get the color vectors [I_HAT,-I_HAT...-K_HAT]
            axes = Cube.directions.keys()

            # create an inverse dict from Cube.directions
            # e.g. {'green':I_HAT, ... }
            color2directions = {}
            for key, color in Cube.directions.items():
                color2directions[color]=key
            
            axis = axes[6-1]
            z = 0 # bottom as white
            for y in xrange(3):
                for x in xrange(3):
                    pieceID = cells[z][y][x][0]
                    orientation = cells[z][y][x][1]
                    color = Cube.faceColors[pieceID]
                    # find out which color is facing the axis direction
                    # here is the cell face directions example:
                    # e.g.  '021' =>    pos_for_2 is '1'
                    #                   pos_for_1 is '0'
                    #                   pos_for_0 is '2'
                    # and as for white surface, we need the pos_for_2 info
                    pos_for_2 = 0
                    if orientation / 100 == 2:
                        pos_for_2 = 2
                    elif (orientation / 10) % 10 == 2:
                        pos_for_2 = 1
                    else:
                        pos_for_2 = 0
                    colorCodeVector = keys[pos_for_2]
                    for c in color:
                        if color2directions[c] // colorCodeVector:
                            print "{:<6}".format(c),
                            break
                print ''
            print''
            
            axis = axes[5-1]
            z = 2 # top as yellow
            for y in xrange(3):
                for x in xrange(3):
                    pieceID = cells[z][y][x][0]
                    orientation = cells[z][y][x][1]
                    color = Cube.faceColors[pieceID]
                    # find out which color is facing the axis direction
                    # here the cell face directions => position
                    # e.g.  '021' =>    pos_for_2 is '1'
                    #                   pos_for_1 is '0'
                    #                   pos_for_0 is '2'
                    # and as for yellow surface, we need the pos_for_2 info
                    if orientation / 100 == 2:
                        pos_for_2 = 2
                    elif (orientation / 10) % 10 == 2:
                        pos_for_2 = 1
                    else:
                        pos_for_2 = 0
                    colorCodeVector = keys[pos_for_2]
                    for c in color:
                        if color2directions[c] // colorCodeVector:
                            print "{:<6}".format(c),
                            break
                print ''
            print''
            
            axis = axes[4-1]
            y = 0 # back as orange
            for z in xrange(3):
                for x in xrange(3):
                    pieceID = cells[z][y][x][0]
                    orientation = cells[z][y][x][1]
                    color = Cube.faceColors[pieceID]
                    # find out which color is facing the axis direction
                    # here the cell face directions => position
                    # e.g.  '021' =>    pos_for_2 is '1'
                    #                   pos_for_1 is '0'
                    #                   pos_for_0 is '2'
                    # and as for orange surface, we need the pos_for_1 info
                    if orientation / 100 == 1:
                        pos_for_1 = 2
                    elif (orientation / 10) % 10 == 1:
                        pos_for_1 = 1
                    else:
                        pos_for_1 = 0
                    colorCodeVector = keys[pos_for_1]
                    for c in color:
                        if color2directions[c] // colorCodeVector:
                            print "{:<6}".format(c),
                            break
                print ''
            print''

            axis = axes[3-1]
            y = 2 # front as red
            for z in xrange(3):
                for x in xrange(3):
                    pieceID = cells[z][y][x][0]
                    orientation = cells[z][y][x][1]
                    color = Cube.faceColors[pieceID]
                    # find out which color is facing the axis direction
                    # here the cell face directions => position
                    # e.g.  '021' =>    pos_for_2 is '1'
                    #                   pos_for_1 is '0'
                    #                   pos_for_0 is '2'
                    # and as for red surface, we need the pos_for_1 info
                    if orientation / 100 == 1:
                        pos_for_1 = 2
                    elif (orientation / 10) % 10 == 1:
                        pos_for_1 = 1
                    else:
                        pos_for_1 = 0
                    colorCodeVector = keys[pos_for_1]
                    for c in color:
                        if color2directions[c] // colorCodeVector:
                            print "{:<6}".format(c),
                            break
                print ''
            print''

            axis = axes[2-1]
            x = 0 # left as blue
            for z in xrange(3):
                for y in xrange(3):
                    pieceID = cells[z][y][x][0]
                    orientation = cells[z][y][x][1]
                    color = Cube.faceColors[pieceID]
                    # find out which color is facing the axis direction
                    # here the cell face directions => position
                    # e.g.  '021' =>    pos_for_2 is '1'
                    #                   pos_for_1 is '0'
                    #                   pos_for_0 is '2'
                    # and as for blue surface, we need the pos_for_0 info
                    if orientation / 100 == 0:
                        pos_for_0 = 2
                    elif (orientation / 10) % 10 == 0:
                        pos_for_0 = 1
                    else:
                        pos_for_0 = 0
                    colorCodeVector = keys[pos_for_0]
                    for c in color:
                        if color2directions[c] // colorCodeVector:
                            print "{:<6}".format(c),
                            break
                print ''
            print''

            axis = axes[1-1]
            x = 2 # left as blue
            for z in xrange(3):
                for y in xrange(3):
                    pieceID = cells[z][y][x][0]
                    orientation = cells[z][y][x][1]
                    color = Cube.faceColors[pieceID]
                    # find out which color is facing the axis direction
                    # here the cell face directions => position
                    # e.g.  '021' =>    pos_for_2 is '1'
                    #                   pos_for_1 is '0'
                    #                   pos_for_0 is '2'
                    # and as for blue surface, we need the pos_for_0 info
                    if orientation / 100 == 0:
                        pos_for_0 = 2
                    elif (orientation / 10) % 10 == 0:
                        pos_for_0 = 1
                    else:
                        pos_for_0 = 0
                    colorCodeVector = keys[pos_for_0]
                    for c in color:
                        if color2directions[c] // colorCodeVector:
                            print "{:<6}".format(c),
                            break
                print ''
            print''

if __name__ == '__main__':
    print 'main'
