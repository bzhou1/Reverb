import numpy as np
import pyaudio
from cmu_112_graphics import *

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100

# Referenced for beat detection through the comparison of sound energy
# http://archive.gamedev.net/archive/reference/programming/features/beatdetection/default.html


class BeatDetection:
    def __init__(self):
        self.chunksPerSecond=43
        # Initializes ring buffer
        self.localEnergyBuffer = np.zeros(self.chunksPerSecond)
        self.bufferIndex = 0
        self.beatRange = 0

    def beatDetect(self, signal):
        # Separating/isolating channel data from stereo audio (two-channel audio)
        signal.shape = -1,2
        signal = signal.T
        # Find and normalize the instant energy of the audio
        instantEnergy = sum((signal[0][x]**2 + signal[1][x]**2) for x in range(len(signal[0]))) / int(0x1fff80058)
        localEnergyAvg = self.localEnergyBuffer.mean()
        localEnergyVar = self.localEnergyBuffer.var()

        beatSensitivity = (-0.0025714*localEnergyVar) + 1.5142857

        # Resets ring buffer & places instantEnergy at respective location
        if self.bufferIndex == self.chunksPerSecond:
            self.bufferIndex = 0
        self.localEnergyBuffer[self.bufferIndex] = instantEnergy
        self.bufferIndex += 1
        
        # Makes sure beat is somewhat loud
        beat = (abs(instantEnergy) > abs(beatSensitivity*localEnergyAvg)) and instantEnergy > 10

        if beat:
            return True
        return None
