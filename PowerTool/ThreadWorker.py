from PyQt5.QtCore import QThread, pyqtSignal

class WorkerThread(QThread):
    def __init__(self):
        super().__init__()
    # Define a signal to communicate with the main thread
    finished = pyqtSignal()

    def run(self):
        # Perform the long-running task here
        # You can emit signals to communicate with the main thread
        self.finished.emit()

    def start_worker(self):
        self.worker_thread.start()
    
    def stop_worker(self):
        self.worker_thread.quit()
        self.worker_thread.wait()



if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.start_worker()
    window.show()
    app.exec_()



