from commonVariable import *
from sendSLDDCommand import slddCommand
from PyQt5.QtCore import pyqtSignal
from PyQt5 import QtCore
from time import sleep

class Timer(QtCore.QThread):
    signal = pyqtSignal(int)

    def __init__(self, timerId = 0, timeout = 0):
        super().__init__()
        self.timerId = timerId
        self.timeout = timeout

    def run(self):
        print(f"Start timer, timerId[{self.timerId}]")
        while self.timeout > 0:
            sleep(1)
            self.timeout = self.timeout -1
        print(f"Timer expired ! >> timerId[{self.timerId}]")
        self.signal.emit(self.timerId)

    def stop(self):
        print('Stopping thread...', self.timerId)