import wave
import os
import numpy as np
import pyaudio
import urllib.request
import re
import ast

from cmu_112_graphics import *
import time
from beatDetection import BeatDetection
from windowAnimations import *
from helperClasses import *


CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100

# Referenced for how Fast Fourier Transforms work
# https://www.nti-audio.com/en/support/know-how/fast-fourier-transform-fft

# Sprites made by Allison Lee (shared with her permission):
# https://www.linkedin.com/in/allison-lee-9b12931b8/

isBeat = False
p = pyaudio.PyAudio()
wf = wave.open('backgroundMusic.wav', "rb")
magnitude = None
beatCount = 0
keyScorePressed = False
mode = ""
difficulty = ""

beatDetection = BeatDetection()

# Initialize
def appStarted(app):
    app._title = 'Reverb'
    app.setSize(600, 400)
    app.timerDelay = 5
    app.stream = None
    app.mode = 'warning' # warning, startScreen, selectMode, selectDifficulty, playingGame, playingSandbox, paused, endingGame
    app.instruments = []
    app.buttons = []
    app.ytButton = YTButton()
    app.images = loadImages(app, 'pictures')
    app.songs = loadSongs(app, 'songs')
    app.isSearch = False
    app.isDownloading = False
    app.timerCount = 0
    app.score = 0
    app.pointStreak = 0
    app.paused = True
    app.pausedStart = None
    app.dots = []
    app.instrumentsThrown = []
    app.songChosen = ""
    app.songChosenPath = ""
    app.songDuration = wf.getnframes()/wf.getframerate()
    app.songStart = time.time()
    app.highScores = ast.literal_eval(loadHighScores(app))
    app.textX0 = 0

    # Window animations
    app.windowAnimationStart = False
    app.windowIsAnimated = False
    app.windowAnimations = {
                            'jitter': jitter, 
                            'bounce': bounce, 
                            'horizontal': horizontal,
                            'vertical': vertical,
                            'diagonal': diagonal,
                            'circle': circle
                            }
    app.windowAnimationsIntense = {
                            'switchSides': switchSides,
                            'fourCorners': fourCorners,
                            'underPopUp': underPopUp,
                            'flickerBW': flickerBW,
                            'flickerColor': flickerColorized
                            }
    app.underPopUp = True
    app.underPopUpDown = True
    app.circleAngle = math.radians(360)
    app.circleR = 40
    app.isLeft = True
    app.diagonalStart = True
    app.flickerBW = False
    app.flickerBWColor = "black"
    app.flickerColorized = False
    app.flickerColor = ""
    app.animationChosen = None
    app.animationBeatToggle = False
    app.animationBeatCount = 0
    tk = Tk()
    app.screenHeight = tk.winfo_screenheight()
    app.screenWidth = tk.winfo_screenwidth()
    app.x = app.screenWidth//2-300
    app.y = app.screenHeight//2-200
    tk.destroy()
    app.dx, app.dy = 1, 1
    app.x1, app.y1 = 1, 1
    app.setPosition(app.x, app.y)
    
    # Audio visualizer
    app.coords = []

    # Sprite idle/throw animation
    spriteThrowStrip = app.images['throwspritesheet']
    spriteIdleStrip = app.images['idlespritesheet']
    app.spriteIdle = [ ]
    app.spriteThrow = [ ]
    for i in range(8):
        sprite = spriteThrowStrip.crop((64*i, 0, 64+64*i, 64))
        app.spriteThrow.append(sprite)
    for i in range(24):
        sprite = spriteIdleStrip.crop((64*i, 0, 64+64*i, 64))
        app.spriteIdle.append(sprite)
    app.spriteThrowCounter = 0
    app.spriteIsThrow = False
    app.spriteIsIdle = True
    app.spriteIdleCounter = 0

    kosbieStrip = app.images['kosbie']
    app.kosbieIdleCounter = 0
    app.kosbieSprite = []
    for i in range(12):
        kosbie = kosbieStrip.crop((502*i, 0, 502+502*i, 396))
        app.kosbieSprite.append(kosbie)

# Makes sure the size of the window stays the same
def sizeChanged(app):
    app.setSize(600, 400)

# Referenced CMU 112 Notes for repr method - https://www.cs.cmu.edu/~112/notes/notes-strings.html
# Loads the previous high scores 
def loadHighScores(app):
    with open("scores.txt", "rt") as file:
        return file.read()

# Writes the current high scores to the scores.txt
def writeHighScores(app):
    with open("scores.txt", "wt") as file:
        file.write(repr(app.highScores))

# Recursively loads the images for Reverb and puts them in a dict
def loadImages(app, path, images={}):
    if os.path.isfile(path):
        pathName = path.split("/")
        fileName = pathName[2].split(".")
        images[fileName[0]] = app.loadImage(path)
        if "instruments" in pathName:
            app.instruments.append(pathName[2])
            images[pathName[2]] = app.loadImage(path)
    else:
        for filename in os.listdir(path):
            if filename == ".DS_Store":
                continue
            loadImages(app, path + '/' + filename)
    return images

# Recursively loads songs and auto-converts them to .wav
def loadSongs(app, path, songs={}):
    if os.path.isfile(path):
        pathName = path.split("/")
        fileName = pathName[1][:-4]
        if "'" in fileName:
            fileName = fileName.replace("'", "")
            os.rename(path, f"songs/{fileName}")
        if path.endswith(".wav"):
            songs[fileName] = path
            newButton = Button(fileName, len(app.buttons)+1)
            app.buttons.append(newButton)
        else:
            # Converts non-wav files to .wav and deletes the former
            os.system(f"""ffmpeg -loglevel quiet -i "{path}" -ar 44100 songs/'{fileName}'.wav""")
            os.system(f"rm '{path}'")
            songs[fileName] = "songs/" + fileName + ".wav"
            newButton = Button(fileName, len(app.buttons)+1)
            app.buttons.append(newButton)
            
    else:
        for filename in os.listdir(path):
            if filename == ".DS_Store":
                continue
            loadSongs(app, path + '/' + filename)
    return songs

# Starts a new audio stream depending on the mode
def newStream(app):
    # Stops song if there is one currently playing to reset
    if app.stream != None:
        app.stream.stop_stream()
    if app.mode == "playingSandbox":
        app.stream = p.open(format=FORMAT,
                    channels=1,
                    rate=RATE,
                    frames_per_buffer=CHUNK,
                    input=True,
                    stream_callback=callback) 
    else:
        # Starts song 
        app.songStart = time.time()
        app.songDuration = wf.getnframes()/wf.getframerate()
        app.score = 0
        app.pointStreak = 0
        app.stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        frames_per_buffer=CHUNK,
                        output=True,
                        stream_callback=callback)
        app.stream.start_stream()

# Pauses the music
def pauseStream(app):
    if app.paused:
        app.stream.stop_stream()
    elif not app.paused:
        app.stream.start_stream()
    app.paused = not app.paused
    
# Continuously updates audio data as the song is playing
def callback(in_data, frame_count, time_info, status):
    try:
        if mode == "playingSandbox":
            signal = in_data
        else:
            # Reads the audio file and returns a chunk in bytes
            signal = wf.readframes(frame_count)
        
        # Converts bytes into integers (a readable signal)
        intSignal = np.frombuffer(signal, dtype=np.int16)
        # Applies a Fast Fourier Transform to the readable signal
        fft = np.fft.fft(intSignal)
        # Scales and normalizes the magnitude of the FFT signal
        global magnitude
        magnitude = (np.abs(fft[0:CHUNK])) * 2 / (256*CHUNK) 

        result = beatDetection.beatDetect(intSignal)

        # Alters tapping grace period dependent on difficulty chosen
        if difficulty == "easy":
            offset = 10
        elif difficulty == "medium":
            offset = 6
        elif difficulty == "hard":
            offset = 3
        else: # Sandbox mode
            offset = 2

        if result != None:
            global isBeat, beatCount, keyScorePressed
            isBeat = True
            beatCount += 1
        # Grace period to score points if beat detected is too short
        elif beatCount < offset and beatCount != 0:
            isBeat = True
            beatCount += 1
            if beatCount == offset:
                isBeat = False
                beatCount = 0
        else: 
            isBeat = False
            beatCount = 0
            keyScorePressed = False
    except:
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    frames_per_buffer=CHUNK,
                    output=True,
                    stream_callback=callback)

    return (signal, pyaudio.paContinue)

# Continuously updates the audioVisualizer FFT coordinates
def audioVisualizer(app):
    # Makes sure timerFired doesn't start before there is readable audio data
    if app.timerCount == 0:
        time.sleep(0.1)
        app.timerCount = 1
    app.coords = []
    # Finds the frequency range
    app.fftX = np.linspace(0, RATE, CHUNK*2) /2 
    app.fftY = magnitude
    # Plots magnitude of FFT against the frequency range of the audio
    for i in range(CHUNK-1):
        app.coords.append((app.fftX[i], app.height/2-app.fftY[i], app.fftX[i+1], app.height/2-app.fftY[i+1]))

# Based on user input, downloads the first result off of YouTube and imports it
def searchYT(app):
    app.isDownloading = True
    keywords = app.getUserInput("What would you like to search on YouTube?")
    if keywords != None:
        # URL formatting
        if len(keywords) > 1:
            keywords = keywords.replace(" ", "+")
        # Webscraping from https://codefather.tech/blog/youtube-search-python/
        # Returns the URL of the first result of search on YouTube
        html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + keywords)
        videoIDs = re.findall(r"watch\?v=(\S{11})", html.read().decode())
        url = "https://www.youtube.com/watch?v=" + videoIDs[0]
        # Downloads the first result from Youtube 
        os.system(f"youtube-dl -q -x -f 'bestaudio[ext=mp3]/bestaudio[ext=wav]/best' -o 'songs/%(title)s.%(ext)s' {url}")
        # Clears song buttons and reloads automatically 
        app.buttons = []
        loadSongs(app, 'songs')
        app.isDownloading = False

def appStopped(app):
    if app.stream != None:
        app.stream.stop_stream()
        app.stream.close()
    wf.close()
    p.terminate()

def warning_mousePressed(app, event):
    app.mode = "startScreen"
    newStream(app)

def warning_redrawAll(app, canvas):
    canvas.create_rectangle(0, 0, app.width, app.height, fill="black")
    canvas.create_image(app.width/2, 100, image=ImageTk.PhotoImage(app.images['warning']))
    canvas.create_image(app.width/2, 180, image=ImageTk.PhotoImage(app.images['warning1']))
    canvas.create_image(app.width/2, 210, image=ImageTk.PhotoImage(app.images['warning2']))
    canvas.create_image(app.width/2, 240, image=ImageTk.PhotoImage(app.images['warning3']))
    canvas.create_image(app.width/2, 350, image=ImageTk.PhotoImage(app.images['clickToProceed']))

def startScreen_mousePressed(app, event):
    app.mode = "directions"

def startScreen_timerFired(app):
    audioVisualizer(app)
    if time.time() - app.songStart >= app.songDuration:
        global wf
        wf = wave.open('backgroundMusic.wav', "rb")
        newStream(app)

def startScreen_redrawAll(app, canvas):
    canvas.create_rectangle(0, 0, app.width, app.height, fill="black")
    if app.coords != []:
        for (x0, y0, x1, y1) in app.coords:
            canvas.create_line(x0, y0, x1, y1, fill="light blue")
    else:
        canvas.create_line(0, app.height/2, app.width, app.height/2, fill="light blue")
    canvas.create_image(app.width/2, 100, image=ImageTk.PhotoImage(app.images['reverbTitle']))
    canvas.create_image(app.width/2, app.width/2, image=ImageTk.PhotoImage(app.images['clickToStart']))
    
def directions_timerFired(app):
    if time.time() - app.songStart >= app.songDuration:
        global wf
        wf = wave.open('backgroundMusic.wav', "rb")
        newStream(app)

def directions_keyPressed(app, event):
    if event.key == "Escape":
        app.mode = "startScreen"

def directions_mousePressed(app, event):
    app.mode = "selectMode"

def directions_redrawAll(app, canvas):
    canvas.create_rectangle(0, 0, app.width, app.height, fill="black")
    canvas.create_image(app.width/2, app.height/6, image=ImageTk.PhotoImage(app.images['directions']))
    canvas.create_image(app.width/2, app.height/3, image=ImageTk.PhotoImage(app.images['directions1']))
    canvas.create_image(app.width/2, app.height/3+30, image=ImageTk.PhotoImage(app.images['directions2']))
    canvas.create_image(app.width/2, app.height/3+90, image=ImageTk.PhotoImage(app.images['controls']))
    canvas.create_image(app.width/2, 2*app.height/3+30, image=ImageTk.PhotoImage(app.images['controls1']))
    canvas.create_image(app.width/2, 365, image=ImageTk.PhotoImage(app.images['clickToProceed']))

def selectMode_keyPressed(app, event):
    if event.key == "Escape":
        app.mode = "directions"

def selectMode_mousePressed(app, event):
    if event.y >= app.height/2+30 and event.y < app.height-30 and event.x > app.width/2:
        searchYT(app)

    elif event.x > app.width/2 and event.y < app.height/2:
        app.mode = "playingSandbox"
        global mode, isBeat
        mode = "playingSandbox"
        isBeat = False
        app.stream.stop_stream()
        wf.close()
        newStream(app)
    
    for button in app.buttons:
        button.mousePressed(app, event)

def selectMode_timerFired(app):
    if len(app.buttons) >= 18:
        app.buttons.pop()
    if time.time() - app.songStart >= app.songDuration:
        global wf
        wf = wave.open('backgroundMusic.wav', "rb")
        newStream(app)
        
def selectMode_mouseMoved(app, event):
    for button in app.buttons:
        button.mouseMoved(app, event)
    app.ytButton.mouseMoved(app, event)

def selectMode_redrawAll(app, canvas):
    canvas.create_rectangle(0, 0, app.width, app.height, fill="black")
    canvas.create_line(app.width/2, 30, app.width/2, app.height-30, fill="white")
    canvas.create_image(app.width/4, 60, image=ImageTk.PhotoImage(app.images['songs']))
    canvas.create_image(2*app.width/3+50, app.height/4+20, image=ImageTk.PhotoImage(app.images['sandbox']))
    canvas.create_line(app.width/2+30, app.height/2, app.width-30, app.height/2, fill="white")
    for button in app.buttons:
        button.redrawAll(app, canvas)
    app.ytButton.redrawAll(app, canvas)
    if app.isDownloading:
        canvas.create_rectangle(30, app.height/3, app.width-30, 2*app.height/3, fill="red", outline="white")
        canvas.create_image(app.width/2, app.height/2, image=ImageTk.PhotoImage(app.images['isDownloading']))

def selectDifficulty_timerFired(app):
    if time.time() - app.songStart >= app.songDuration:
        global wf
        wf = wave.open('backgroundMusic.wav', "rb")
        newStream(app)
        
def selectDifficulty_keyPressed(app, event):
    if event.key == "Escape":
        app.mode = "selectMode"

def selectDifficulty_mousePressed(app, event):
    # Reset game
    global mode, difficulty, wf
    mode = "playingGame"
    app.mode = "playingGame"
    app.stream.stop_stream()
    app.windowAnimationStart = False
    app.windowIsAnimated = False
    app.score = 0
    wf = wave.open(app.songChosenPath, 'rb')
    newStream(app)

    # Select difficulty
    if event.x <= app.width/3:
        difficulty = "easy"
    elif event.x <= 2*app.width/3 and event.x > app.width/3:
        difficulty = "medium"
    elif event.x > 2*app.width/3:
        difficulty = "hard"

def selectDifficulty_redrawAll(app, canvas):
    canvas.create_rectangle(0, 0, app.width, app.height, fill="black")
    canvas.create_line(app.width/3, 30, app.width/3, app.height-30, fill="white")
    canvas.create_line(2*app.width/3, 30, 2*app.width/3, app.height-30, fill="white")
    canvas.create_image(app.width/6, app.height/2, image=ImageTk.PhotoImage(app.images['easy']))
    canvas.create_image(app.width/2+6, app.height/2, image=ImageTk.PhotoImage(app.images['medium']))
    canvas.create_image(5*app.width/6, app.height/2, image=ImageTk.PhotoImage(app.images['hard']))
    
def playingSandbox_timerFired(app):
    ############### DOTS ###############
    global isBeat
    if isBeat:
        for __ in range(3):
            newDot = Dot(app.width/2, app.height/2, random.randint(3,7))
            app.dots.append(newDot)
    else:
        isBeat = False

    for dot in app.dots:
        dot.timerFired(app)
    
    audioVisualizer(app)
    
def playingSandbox_keyPressed(app, event):
    if event.key == "Escape":
        global mode
        mode = "selectMode"
        app.mode = "selectMode"
        app.stream.stop_stream()
        app.stream.close()
        global wf 
        wf = wave.open('backgroundMusic.wav', "rb")
        newStream(app)

def playingSandbox_redrawAll(app, canvas):
    ############### AUDIO VISUALIZER ###############
    canvas.create_rectangle(0, 0, app.width, app.height, fill="black")
    if app.coords != []:
        for (x0, y0, x1, y1) in app.coords:
            canvas.create_line(x0, y0, x1, y1, fill="light blue")
    else:
        canvas.create_line(0, app.height/2, app.width, app.height/2, fill="light blue")
    
    for dot in app.dots:
        dot.redrawAll(app, canvas)
    
def playingGame_timerFired(app):
    ############### SPRITE ###############
    if app.spriteIsIdle == True:
        app.spriteIdleCounter = (1 + app.spriteIdleCounter) % len(app.spriteIdle)
    elif app.spriteIsThrow == True:
        app.spriteThrowCounter = (1 + app.spriteThrowCounter) % len(app.spriteThrow)
        if app.spriteThrowCounter == 7:
            app.spriteIsThrow = False
            app.spriteIsIdle = True
            app.spriteIdleCounter = 0
    app.kosbieIdleCounter = (1 + app.kosbieIdleCounter) % len(app.kosbieSprite)
    for instrument in app.instrumentsThrown:
        instrument.timerFired(app)
    
    ############### WINDOW ANIMATIONS ###############
    app.setPosition(app.x, app.y)
    if time.time() - app.songStart >= app.songDuration/3:
        app.windowAnimationStart = True
    if time.time() - app.songStart >= 2*app.songDuration/3:
        app.windowAnimations.update(app.windowAnimationsIntense)
    if time.time() - app.songStart >= app.songDuration-2:
        app.animationBeatToggle = False
        app.animationBeatCount = 0
        app.windowIsAnimated = False
        app.x, app.y = app.screenWidth//2-300, app.screenHeight//2-200
        app.dx, app.dy = 1, 1
    if app.windowAnimationStart == True:
        # Resets animation-beat timer
        if isBeat == False and app.animationBeatToggle == False:
            app.animationBeatToggle = True
            app.animationBeatCount += 1
        elif isBeat == True:

            # Reset flicker window animations
            app.flickerBW = False
            app.flickerColorized = False

            # Resets window position & speed for future animations
            if app.animationBeatCount == 10:
                app.x, app.y = app.screenWidth//2-300, app.screenHeight//2-200
                app.dx, app.dy = 1, 1
            # Makes sure each window animation lasts for an appropriate time
            elif app.animationBeatToggle == True and app.animationBeatCount < 10:
                app.animationBeatToggle = False
                app.animationBeatCount += 1
            # Chooses random animation
            elif app.animationBeatToggle == True:
                app.animationBeatToggle = False
                app.animationBeatCount = 0
                app.animationChosen = random.choice(list(app.windowAnimations.keys()))
                app.windowIsAnimated = True
                app.x, app.y = app.screenWidth//2-300, app.screenHeight//2-200
                app.dx, app.dy = 1, 1
        else:
            app.animationBeatToggle = False
    if app.windowIsAnimated == True:
        app.windowAnimations[app.animationChosen](app)
    
    audioVisualizer(app)
    
    # "Song playing" text animation
    app.textX0 += 1
    if app.textX0 >= app.width:
        app.textX0 = 0
    
    ############### GAME ENDING ###############
    # Stops music, calculates high score scoreboard
    if time.time() - app.songStart >= app.songDuration:
        app.stream.stop_stream()
        app.mode = "endingGame"
        global mode
        mode = "endingGame"
        if app.songChosen not in app.highScores:
            app.highScores[app.songChosen] = [0, 0, 0, 0]
        for i in range(4):
            if app.score > int(app.highScores[app.songChosen][i]):
                app.highScores[app.songChosen].insert(i, app.score)
                if len(app.highScores[app.songChosen]) > 4:
                    app.highScores[app.songChosen].pop()
                break
        writeHighScores(app)
        app.setPosition(app.screenWidth//2-300, app.screenHeight//2-200)

def playingGame_keyPressed(app, event): 
    global keyScorePressed, mode
    if event.key == 'Space' and isBeat == True and keyScorePressed == False:
        app.score += 100
        app.pointStreak += 1
        # Extra points for point streak of 5+
        if app.pointStreak >= 5:
            app.score += app.score//1000 * 2
        # Makes sure cannot score more than once per beat
        keyScorePressed = True
        app.spriteIsIdle = False
        app.spriteIsThrow = True
        newInstrument = InstrumentThrown(random.choice(app.instruments), app.width, app.height)
        app.instrumentsThrown.append(newInstrument)

    # Resets point streak when player hits space offbeat
    elif event.key == 'Space' and isBeat == False:
        app.pointStreak = 0
    
    # Pauses current game
    if event.key == "p":
        mode = "paused"
        app.mode = "paused"
        app.pausedStart = time.time()
        pauseStream(app)
    
    # Ends current game prematurely
    elif event.key == "Escape":
        app.stream.stop_stream()
        app.mode = "endingGame"
        mode = "endingGame"
        if app.songChosen not in app.highScores:
            app.highScores[app.songChosen] = [0, 0, 0, 0]
        for i in range(4):
            if app.score > int(app.highScores[app.songChosen][i]):
                app.highScores[app.songChosen].insert(i, app.score)
                if len(app.highScores[app.songChosen]) > 4:
                    app.highScores[app.songChosen].pop()
                break
        writeHighScores(app)
        app.setPosition(app.screenWidth//2-300, app.screenHeight//2-200)

def playingGame_redrawAll(app, canvas):
    ############### AUDIO VISUALIZER ###############
    canvas.create_rectangle(0, 0, app.width, app.height, fill="black")
    canvas.create_text(50, 30, font="ComicSansMS 15", text=f"Score: {app.score}", fill="white")

    if app.coords != []:
        for (x0, y0, x1, y1) in app.coords:
            canvas.create_line(x0+50, y0, x1+50, y1, fill="light blue")
    else:
        canvas.create_line(0, app.height/2, app.width, app.height/2, fill="light blue")
    
    ############### SPRITE ###############
    if app.spriteIsIdle == True:
        sprite = app.spriteIdle[app.spriteIdleCounter]
    elif app.spriteIsThrow == True:
        sprite = app.spriteThrow[app.spriteThrowCounter]
    canvas.create_image(35, app.height/2, image=ImageTk.PhotoImage(sprite))
    kosbie = app.kosbieSprite[app.kosbieIdleCounter]
    canvas.create_image(app.width-80, app.height/2, image=ImageTk.PhotoImage(kosbie))

    for instrument in app.instrumentsThrown:
            instrument.redrawAll(app, canvas)
    
    if app.flickerBW:
        canvas.create_rectangle(0, 0, app.width, app.height, fill=app.flickerBWColor)
    if app.flickerColorized:
        canvas.create_rectangle(0, 0, app.width, app.height, fill=app.flickerColor)

    canvas.create_text(app.textX0, app.height-30, text=f"♫ song playing - {app.songChosen} ♫", fill="white", font="ComicSansMS 12")

def paused_keyPressed(app, event):
    if event.key == "p":
        pauseStream(app)
        app.mode = "playingGame"
        global mode 
        mode = "playingGame"

def paused_timerFired(app):
    app.songDuration += time.time() - app.pausedStart

def paused_redrawAll(app, canvas):
    canvas.create_rectangle(0, 0, app.width, app.height, fill="black")
    canvas.create_image(app.width/2, app.height/2-50, image=ImageTk.PhotoImage(app.images['paused']))
    canvas.create_image(app.width/2, app.height/2+50, image=ImageTk.PhotoImage(app.images['pressToUnpause']))

def endingGame_mousePressed(app, event):
    global mode
    mode = "selectMode"
    app.mode = 'selectMode'
    
def endingGame_redrawAll(app, canvas):
    canvas.create_rectangle(0, 0, app.width, app.height, fill="black")
    canvas.create_image(app.width/6, app.height/3, image=ImageTk.PhotoImage(app.images['score']))
    canvas.create_text(app.width/6, app.height/2-20, text=f'{app.score}', font="ComicSansMS 20", fill="white")
    canvas.create_line(app.width/3, 30, app.width/3, app.height-30, fill="white")
    canvas.create_image(2*app.width/3, app.height/6, image=ImageTk.PhotoImage(app.images['highScores']))
    canvas.create_text(app.width/2-35, 13*app.height/24, text=f'1:\n\n\n2:\n\n\n3:\n\n\n4:', font="CenturyGothic 20", fill="white")
    canvas.create_text(2*app.width/3, app.height/4 + 10, text=f'{app.highScores[app.songChosen][0]}', font="ComicSansMS 20", fill="white")
    canvas.create_text(2*app.width/3, 2*app.height/4 - 20, text=f'{app.highScores[app.songChosen][1]}', font="ComicSansMS 20", fill="white")
    canvas.create_text(2*app.width/3, 2*app.height/4 + 50, text=f'{app.highScores[app.songChosen][2]}', font="ComicSansMS 20", fill="white")
    canvas.create_text(2*app.width/3, 3*app.height/4 + 25, text=f'{app.highScores[app.songChosen][3]}', font="ComicSansMS 20", fill="white")

    canvas.create_image(app.width-65, app.height-30, image=ImageTk.PhotoImage(app.images['clickToProceed']))

runApp()
