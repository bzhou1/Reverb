from cmu_112_graphics import *
from tkinter import *
import math, random

# Window will glitch horizontally in place / "jitter" in place
def jitter(app):
    app.dx, app.dy = 1, 1
    app.x += 1
    if app.x >= app.screenWidth//2-290:
        app.x = app.screenWidth//2-310

# Window will bounce off the sides of the screeen
def bounce(app):
    app.x += 3*app.dx
    app.y += 3*app.dy
    if app.x >= app.screenWidth//2+115 or app.x <= 0:
        app.dx *= -1
    if app.y >= app.screenHeight//2 or app.y <= 30:
        app.dy *= -1

# Will move to the four corners of the screen at random times  
def fourCorners(app):
    app.setPosition(0,0)
    app.x1 += 20
    if app.x1 >= app.screenWidth-600:
        app.x1 = app.screenWidth-600
        app.setPosition(app.screenWidth-600, 0)
        app.y1 += 20
    if app.y1 >= app.screenHeight-300:
        app.y1 = app.screenHeight-300
        app.setPosition(app.screenWidth-600, app.screenHeight-300)
        app.x1 += -40
    if app.x1 <= 0:
        app.setPosition(0, app.screenHeight-300)
        app.y1 += -40
    if app.y1 <= 0:
        app.y1 = 0
        app.setPosition(0, 0)
        app.x1, app.y1 = 0, 0

# Will continue horizontally across the screen and speed up
def horizontal(app):
    app.dx += 1
    app.x += app.dx
    if app.x >= app.screenWidth:
        app.x = 0
        app.dx += 1

# Will continue vertically across the screen and speed up
def vertical(app):
    app.dy += 1
    app.y += app.dy
    if app.y >= app.screenHeight:
        app.y = 0
        app.dy += 1

# Will continue diagonally across the screen and speed up
def diagonal(app):
    if app.diagonalStart == True:
        app.x, app.y = 0, 0
        app.diagonalStart = False
    app.x += 10*app.dx
    app.y += 8*app.dy
    if app.x >= app.screenWidth or app.y >= app.screenHeight-30:
        app.x, app.y = 0, 0

# Will move in a circle on the screen
def circle(app):
    app.x = int(app.screenWidth//2-300 + app.circleR * math.cos(app.circleAngle))
    app.y = int(app.screenHeight//2-200 + app.circleR * math.sin(app.circleAngle))
    app.circleAngle += math.radians(5)

# Will switch from the left side to the right side at a fast pace
def switchSides(app):
    if app.isLeft:
        app.x = 50
        app.y = app.screenHeight//2-200
        app.isLeft = False
    elif not app.isLeft:
        app.x = app.screenWidth-650
        app.y = app.screenHeight//2-200
        app.isLeft = True

# Will go "under" the screen and pop up to the right & vice versa
def underPopUp(app):
    if app.underPopUp == True:
        app.x = 50
        app.y = app.screenHeight//2-200
        app.underPopUp = False
    if app.underPopUpDown == True:
        if app.y < app.screenHeight-100 and app.x < app.screenWidth//2-300:
            app.y += 8*app.dy
            if app.y > app.screenHeight-100:
                app.x = app.screenWidth-650
                app.underPopUpDown = False
        elif app.y < app.screenHeight-100 and app.x > app.screenWidth//2-300:
            app.y += 8*app.dy
            if app.y > app.screenHeight-100:
                app.x = 50
                app.underPopUpDown = False
    elif app.underPopUpDown == False:
        app.y -= 8*app.dy 
        if app.y < app.screenHeight//2-200:
            app.underPopUpDown = True

# Strobe light, black and white
def flickerBW(app):
    app.flickerBW = True
    if app.flickerBWColor == "black":
        app.flickerBWColor = "white"
    else:
        app.flickerBWColor = "black"

# Strobe light, colors
def flickerColorized(app):
    app.flickerColorized = True
    colors = ['#CCE1F2', '#C6F8E5', '#FBF7D5', '#F9DED7', '#F5CDDE', '#E2BEF1',
              '#94BB86', '#FFFE9C', '#FFFFC6', '#FFC8D7', '#FFB684', '#92ACE5']
    app.flickerColor = random.choice(colors)