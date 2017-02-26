# coloranalytics.py
# Chris Barker
# CMU S13 15-112 Term Project

from math import e

class Profile(object):
    def __init__(self, color, meanSat, meanHue, meanVal, meanSqSat, meanSqHue, meanSqVal):
        self.color = color
        self.meanSat = meanSat
        self.meanHue = meanHue
        self.meanVal = meanVal
        self.meanSqSat = meanSqSat
        self.meanSqHue = meanSqHue
        self.meanSqVal = meanSqVal

    def probability(self, h, s, v, hOff):
        h -= hOff
        hWeight = float(self.meanSqSat) / (max(self.meanSqHue, 1))
        vWeight = float(self.meanSqVal) / (max(self.meanSqVal, 1))
        sWeight = 1.

        weightSum = hWeight + sWeight + vWeight
        hWeight = hWeight / weightSum
        sWeight = sWeight / weightSum
        vWeight = vWeight / weightSum

        hWeight = 1.
        sWeight = vWeight = 0.

        devsH = ((h - self.meanHue) ** 2) / max(1., self.meanSqHue)
        devsS = ((s - self.meanSat) ** 2) / max(1., self.meanSqSat)
        devsV = ((v - self.meanVal) ** 2) / max(1., self.meanSqVal)

        prob = 0
        prob += hWeight * (e ** (-abs(devsH)))
        prob += sWeight * (e ** (-abs(devsS)))
        prob += vWeight * (e ** (-abs(devsV)))

        return prob

class Profiles(object):
    def __init__(self):
        with open('coloranalytics.txt') as file:
            data = eval(file.read())

        self.colorProfiles = [ ]
        self.hueOffset = 0
        self.rgbOffset = (0,0,0)

        for color in data:
            profile = [ ]
            profile.append(color)
            sats = [i[0] for i in data[color]]
            hues = [i[1] for i in data[color]]
            vals = [i[2] for i in data[color]]

            meanSat = float(sum(sats)) / len(sats)
            meanHue = float(sum(hues)) / len(hues)
            meanVal = float(sum(vals)) / len(vals)

            sqsSat = [(sat - meanSat)**2 for sat in sats]
            meanSqSat = float(sum(sqsSat)) / len(sqsSat)

            sqsHue = [(hue - meanHue)**2 for hue in hues]
            meanSqHue = float(sum(sqsHue)) / len(sqsHue)

            sqsVal = [(val - meanVal)**2 for val in vals]
            meanSqVal = float(sum(sqsVal)) / len(sqsVal)

            self.colorProfiles.append(Profile(color, meanSat, meanHue, meanVal,
                                            meanSqSat, meanSqHue, meanSqVal))

    def getColor(self, h, s, v):

        maxProb = -1
        maxProfile = None
        for profile in self.colorProfiles:
            prob = profile.probability(h,s,v, self.hueOffset)
            if prob > maxProb:
                maxProfile = profile
                maxProb = prob
        return maxProfile.color

def colorByHSV(hue, sat, val):
    # this is an optional feature not used in this release.
    return profiles.getColor(hue, sat, val)

def colorByRGB(*args):

    if len(args) == 4:
        (rgb, h, s, v) = args
    elif len(args) == 2:
        (rgb, hsv) = args
        (h, s, v) = hsv

    (blue, green, red) = rgb
    (blueOff, greenOff, redOff) = profiles.rgbOffset

    red += redOff
    green += greenOff
    blue += blueOff

    green = float(max(green, 1))
    red = float(max(red, 1))
    blue = float(max(blue, 1))

    if blue / red > 2 and blue / green > 2: 
        return 'blue'
    elif green / red > 2:
        return 'green'

    if h > 150 or h < 6:
        return 'red'
    elif h < 20 and s < 150:
        return 'white'
    elif h < 20:
        return 'orange'
    elif h < 50:
        return 'yellow'

    return 'white'

def colorByRGB2(*args):

    if len(args) == 4:
        (rgb, h, s, v) = args
    elif len(args) == 2:
        (rgb, hsv) = args
        (h, s, v) = hsv

    (blue, green, red) = rgb
    (blueOff, greenOff, redOff) = profiles.rgbOffset

    red += redOff
    green += greenOff
    blue += blueOff

    green = float(max(green, 1))
    red = float(max(red, 1))
    blue = float(max(blue, 1))


    if h >= 4 and h < 15 and s > 90 and s < 190 and v > 10 and v < 130:
        return 'red'
    elif h > 4 and h < 15 and s > 100 and s < 200 and v > 140:
        return 'orange'
    elif h > 25 and h < 40 :#and s > 100 and s < 140 and v > 150 and v < 190:
        return 'yellow'
    elif h > 50 and h < 70 :#and s > 80 and s < 190 and v > 80 and v < 180:
        return 'green'
    elif h >= 40 and h < 50 :
        if s > 100 and v < 180:
            return 'green'
        else:
            return 'yellow'
##    elif h > 10 and h < 110 and s > 120 and s < 255 and v > 30 and v < 190:
##        return 'blue'
##    elif h > 20 and h < 80 :#and s > 1 and s < 60 and v > 100 and v < 170:
##        return 'white'
    elif h > 75 and h < 110 :#and s > 1 and s < 60 and v > 100 and v < 170:
        if s > 1 and s < 100 and v > 100 and v < 255:
            return 'white'
        else:
            return 'blue'

    return 'gray'

profiles = Profiles()

def updateWhite(rgb):
    (red, green, blue) = rgb
    avg = (red + green + blue) / 3
    profiles.rgbOffset = (avg - red, avg - green, avg - blue)
