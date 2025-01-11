import os
import serial
from time import sleep
from PyQt5 import QtCore
from commonVariable import *
from PyQt5.QtCore import pyqtSignal
from DownloadManager import DownloadManager
from FlashManager import FlashManager

class AutomateQFIL(QtCore.QThread):
    signal = pyqtSignal(str)
    progressSignal = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.boardName = None
        self.isRunning = False
        self.runDownloadOnly = False
        self.runFlashOnly = False
        self.ArduinoPort = NO_PORT_CONNECTED
        self.downloadFromURL = NO_IMAGE_URL
        self.vcmDevice = UNKNOWN_ID
        self.imageVersion = NO_IMAGE_VERSION

    def run(self):
        try:
            self.initQFILManager()
            self.handleAutomateQFIL()
        except Exception as e:
            self.signal.emit(f"Error during AutomateQFIL process: {e}")

    def initQFILManager(self):
        self.boardDir = os.path.join(os.path.dirname(os.getcwd()), "images", self.boardName, self.imageVersion)
        self.setupDownloadManager()
        self.setupFlashManager()
    
    def setupDownloadManager(self):
        self.mDownloadManager = DownloadManager()
        self.mDownloadManager.imageVersion = self.imageVersion
        self.mDownloadManager.downloadSignal.connect(self.signal)
        self.mDownloadManager.downloadProgressSignal.connect(self.progressSignal)
    
    def setupFlashManager(self):
        self.mFlashManager = FlashManager(self.boardName, self.boardDir)
        self.mFlashManager.vcmDevice = self.vcmDevice
        self.mFlashManager.imageVersion = self.imageVersion
        self.mFlashManager.flashSignal.connect(self.signal)
        self.mFlashManager.flashProgressSignal.connect(self.progressSignal)

    def handleAutomateQFIL(self):
        if self.runDownloadOnly and not self.runFlashOnly:
            self.handleDownload()
        elif self.runFlashOnly and not self.runDownloadOnly:
            self.handleFlash()
        elif self.runDownloadOnly and self.runFlashOnly:
            self.handleDownloadAndFlash()

    def handleDownload(self):
        self.isRunning = True
        try:
            if self.downloadFromURL != NO_IMAGE_URL:
                self.mDownloadManager.downloadFromURL = self.downloadFromURL

            self.mDownloadManager.boardName = self.boardName
            result = self.mDownloadManager.handleDownloadImage()
            self.isRunning = False
            return result
        
        except Exception as e:
            self.isRunning = False
            self.signal.emit(f"Error during download: {e}")
            return False
    
    def handleFlash(self):
        self.isRunning = True
        try:
            self.mFlashManager.handleFlashImage()
            self.isRunning = False
        except Exception as e:
            self.isRunning = False
            self.signal.emit(f"Error during flash: {e}")
    
    def handleDownloadAndFlash(self):
        if not self.handleDownload():
            self.signal.emit("Download failed, skipping flash.\n")
            return
        self.handleFlash()
        
    def stop(self):
        if self.isRunning == True:
            if self.mDownloadManager.isDownloading == True:
                self.mDownloadManager.stop()
            if self.mFlashManager.isFlashing == True:
                self.mFlashManager.stop()
            self.isRunning = False
            self.exit()
