import random, math
from cmu_112_graphics import *

class Dot(object):
    def __init__(self, cx, cy, r):
        self.cx, self.cy = cx, cy
        self.r = r
        self.color = self.randomColor()
        self.dead = False
        self.dying = False
        self.counter = 0
        self.dirX, self.dirY = self.randomDirection()
    
    def randomColor(self):
        colors = ['#CCE1F2', '#C6F8E5', '#FBF7D5', '#F9DED7', '#F5CDDE', '#E2BEF1',
                  '#94BB86', '#FFFE9C', '#FFFFC6', '#FFC8D7', '#FFB684', '#92ACE5']
        return random.choice(colors)

    def randomDirection(self):
        self.dirX = 2*math.cos(random.randint(-180, 180))
        self.dirY = 2*math.sin(random.randint(-180, 180))
        return self.dirX, self.dirY
        
    def timerFired(self, app):
        if not self.dead:
            self.cx += self.dirX
            self.cy += self.dirY
            self.counter += 1
            if self.counter >= 100:
                self.r -= 0.3
                self.dying = True
                
        if self.r <= 0:
            self.dead = True

    def redrawAll(self, app, canvas):
        if self.dead != True:
            canvas.create_oval(self.cx-self.r, self.cy-self.r,
                            self.cx+self.r, self.cy+self.r,
                            fill = self.color)

class InstrumentThrown(object):
    def __init__(self, instrument, width, height):
        self.instrument = instrument
        self.width, self.height = width, height
        self.x = 45
        self.y = self.height/2 - 20
        self.r = self.height/2 - 20
        self.dead = False
        self.angle = math.radians(180)
    
    def timerFired(self, app):
        if not self.dead:
            self.x = app.width/2-30 + self.r * math.cos(self.angle)
            self.y = app.height/2 + self.r * math.sin(self.angle)
            self.angle += math.radians(5)
            if self.x >= app.width-220 and self.y <= app.height/1.5:
                self.dead = True
        
    def redrawAll(self, app, canvas):
        if not self.dead:
            canvas.create_image(self.x, self.y, image=ImageTk.PhotoImage(app.images[self.instrument]))

class Button(object):
    def __init__(self, song, count):
        self.song = song
        self.count = count
        self.y0 = 70 + self.count*15 + self.count*2
        self.y1 = 85 + self.count*15 + self.count*2
        self.color = "black"
    
    def mouseMoved(self, app, event):
        # If mouse in boundaries of button
        if event.y >= self.y0 and event.y < self.y1 and event.x < app.width/2:
            self.color = "#303030"
        else:
            self.color = "black"
    
    def mousePressed(self, app, event):
        # If button was clicked in boundaries
        if event.y >= self.y0 and event.y < self.y1 and event.x < app.width/2:
            app.songChosen = self.song
            app.songChosenPath = app.songs[self.song]
            app.mode = "selectDifficulty"

    def redrawAll(self, app, canvas):
        canvas.create_rectangle(10, self.y0, app.width/2-10, self.y1, outline="light grey", width=1, fill=self.color)
        canvas.create_text(app.width/4, (self.y0+self.y1)/2, text=self.song, fill='white', font="ComicSansMS 10")

class YTButton(object):
    def __init__(self):
        self.color = "black"
    
    def mouseMoved(self, app, event):
        # If mouse in boundaries of button
        if event.y >= app.height/2+30 and event.y < app.height-30 and event.x > app.width/2:
            self.color = "red"
        else:
            self.color = "black"

    def redrawAll(self, app, canvas):
        canvas.create_rectangle(app.width/2+30, app.height/2+30, app.width-30, app.height-30, outline="light grey", width=1, fill=self.color)
        canvas.create_image(3*app.width/4, app.height-100, image=ImageTk.PhotoImage(app.images['youtube']))




    