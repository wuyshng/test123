import os
import sys
import schedule
from time import sleep
import logging
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QThread, QObject, QTimer, QEventLoop
from Application import UI_Power_tool
from commonVariable import *

# Configure logging
logging.basicConfig(
    filename='automationSanity.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class AutomationSanity:
    def __init__(self):
        super().__init__()
        # Create Qt application
        self.app = QApplication(sys.argv)

        # Create QMainWindow instance first
        self.TestingTool = QMainWindow()
        
        # Create main application with TestingTool instance
        self.mainApp = UI_Power_tool(self.TestingTool)
        self.TestingTool.show()  # Show the main window, not the UI_Power_tool directly

        # Create timer for scheduling checks
        self.timer = QTimer()
        self.timer.timeout.connect(self.checkShedule)
        self.timer.start(60000)

        # Initialize schedule
        schedule.every().day.at("17:29:00").do(self.runAutomatedSanity)
        logging.info("Automation sanity started")
        print("Automation is running. Close the application to stop.")

    def runAutomatedSanity(self):
        try:
            self.mainApp.perfVersionButton.setChecked(True)
            self.mainApp.debugVersionButton.setChecked(True)
            sleep(5)
            if not self.handleAutomateQFIL():
                return False

            if not self.handleSanity():
                return False
            
        except Exception as e:
            logging.error(f"Error during automation: {str(e)}")

    def checkDeviceStatus(self):
        self.mainApp.mdeviceStatus = NORMAL
        self.deviceStatus = self.mainApp.mdeviceStatus
        logging.info(f"checkDeviceStatus: {self.deviceStatus}")
        if not self.deviceStatus == NORMAL:
            logging.error(f"Device is not ready to sanity. Please check your devices")
            return False
        return True

    def handleAutomateQFIL(self):
        logging.info(f"handleAutomateQFIL")
        try:
            if not self.checkDeviceStatus():
                return False
            
            self.mainApp.downloadImgButton.setChecked(True)
            self.mainApp.flashImgButton.setChecked(True)
            
            result = QEventLoop()

            def onResult(success):
                result.exit(0 if success else 1)

            self.mainApp.mAutomateQFIL.resultSignal.connect(onResult)
            self.mainApp.startFLButton.click()

            # Wait for QFIL to finish
            if result.exec_() != 0:
                logging.error("AutomateQFIL failed.")
                return False
                
            return True
        except Exception as e:
            logging.error(f"Error during AutomateQFIL process: {e}")
            return False

    def handleSanity(self):
        logging.info(f"handleSanity")
        try:
            if not self.loadRobotFile():
                return False
        
            if not self.startSanityTest():
                return False
            
            return True
        except Exception as e:
            logging.error(f"Error during sanity process: {e}")
            return False

    def loadRobotFile(self):
        try:
            logging.info("loadRobotFile")
            files = self.selectRobotFiles()
            print(f"files: {files}")
            logging.info(f"loadRobotFile, selected files: {files}")
            self.mainApp.loadRobotTestCase(files)
            return True
        except Exception as e:
            logging.error(f"Error during load robot files: {e}")
            return False 

    def selectRobotFiles(self):
        logging.info("selectRobotFiles")
        if self.mainApp.boardName == JLR_VCM:
            self.robotFilesPath = r"D:\01_TOOL\tiger-robot\testsuites_vcm"
        elif self.mainApp.boardName == JLR_TCUA:
            self.robotFilesPath = r"D:\01_TOOL\tiger-robot\testsuites_tcua"
        else:
            logging.error("Can not find board name")
            return []

        if not os.path.isdir(self.robotFilesPath):
            raise ValueError("The provided path is not a valid directory.")
        
        selected_files = [os.path.join(self.robotFilesPath, file) 
                        for file in os.listdir(self.robotFilesPath) 
                        if os.path.isfile(os.path.join(self.robotFilesPath, file))]
        logging.info(f"selected_files: {selected_files}")
        self.mainApp.robotFilePath = os.path.dirname(selected_files[0])
        self.mainApp.parentSuite = os.path.basename(self.mainApp.robotFilePath)
        return selected_files
        
    def startSanityTest(self):
        try:
            logging.info(f"startSanityTest")
            while not self.checkDeviceStatus():
                logging.info("Device status is not NORMAL, waiting...")
                time.sleep(1)

            if not self.checkDeviceStatus():
                return False
            
            self.mainApp.startTaskButton.click()
            logging.info(f"Running sanity test...")
            return True
        except Exception as e:
            logging.error(f"Error during run test: {e}")
            return False

    def checkShedule(self):
        """Check and run pending scheduled tasks"""
        schedule.run_pending()

    def run(self):
        """Start the application main loop"""
        return self.app.exec_()

def main():
    sanity = AutomationSanity()

    # Run the task once immediately for testing
    QTimer.singleShot(1000, sanity.runAutomatedSanity)
    
    # Start the application
    sys.exit(sanity.run())

if __name__ == "__main__":
    main()