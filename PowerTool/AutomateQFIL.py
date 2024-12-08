from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from DownloadManager import DownloadManager
from FlashManager import FlashManager

class AutomateQFIL(QtCore.QThread):
    signal = pyqtSignal(str)
    progressSignal = pyqtSignal(int)
    def __init__(self):
        super().__init__()
        self.mDownloadManager = DownloadManager()
        self.mDownloadManager.downloadSignal.connect(self.signal)
        self.mDownloadManager.downloadProgressSignal.connect(self.progressSignal)

    def run(self):
        try:
            self.mDownloadManager.boardName = self.boardName
            self.mDownloadManager.handleDownloadImg()

            self.boardDir = self.mDownloadManager.boardDir
            self.mFlashManager = FlashManager(self.boardName, self.boardDir)
            self.mFlashManager.flashSignal.connect(self.signal)
            self.mFlashManager.flashProgressSignal.connect(self.progressSignal)
            self.mFlashManager.handleFlashImg()

        except Exception as e:
            self.signal.emit(f"Error during AutomateQFIL process: {e}")
