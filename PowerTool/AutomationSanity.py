import os
import sys
import time
import logging
import schedule
from commonVariable import *
import serial.tools.list_ports
from Application import UI_Power_tool
from ArduinoManager import ArduinoManager
from AutomateReportOnCollab import AutomateReportOnCollab
from PyQt5.QtCore import QTimer, QEventLoop
from PyQt5.QtWidgets import QApplication, QMainWindow

# Configure logging
logging.basicConfig(
    filename='automationSanity.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class AutomationSanity:
    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        self.TestingTool = QMainWindow()
        self.mainApp = UI_Power_tool(self.TestingTool)
        self.TestingTool.show()
        self.mAutomateReportOnCollab = AutomateReportOnCollab()
        self.mAutomateReportOnCollab.createDailySanityPage()

        # Create timer for scheduling checks
        self.timer = QTimer()
        self.timer.timeout.connect(schedule.run_pending)
        self.timer.start(60000)

        # Initialize schedule
        schedule.every().day.at("10:00").do(self.runAutomatedSanity)
        logging.info("================ Automation sanity started ================")
        print("Automation is running. Close the application to stop.")

    def runAutomatedSanity(self):
        try:
            # for board in [JLR_VCM, JLR_TCUA]:
            for board in [JLR_TCUA, JLR_VCM]:
                self.mAutomateReportOnCollab.isError = ""
                self.boardName = board
                time.sleep(2)

                if not self.handleAutomateQFIL():
                    logging.warning(f"{self.boardName}: handleAutomateQFIL failed. Skipping handleAutomateSanity.")
                    self.mAutomateReportOnCollab.updateDailySanityPage(self.boardName)
                    continue

                if not self.turnOnVBATButton():
                    continue

                if not self.handleAutomateSanity():
                    logging.warning(f"{self.boardName}: handleAutomateSanity failed.")
                    continue

                self.mAutomateReportOnCollab.updateDailySanityPage(self.boardName)            
        except Exception as e:
            logging.error(f"{self.boardName}: Error during automation: {str(e)}")

    def checkDeviceStatus(self):
        return self.mainApp.mdeviceStatus == NORMAL
    
    def waitForDeviceReady(self, timeout=300):
        startTime = time.time()
        logging.info(f"{self.boardName}: Waiting for device to reach NORMAL status...")
        
        def check_status():
            if time.time() - startTime > timeout:
                logging.warning(f"{self.boardName}: Device did not reach NORMAL status within {timeout} seconds.")
                self.mAutomateReportOnCollab.isError = f"Device did not reach NORMAL status within {timeout} seconds."
                logging.warning(f"{self.boardName}: AutomateQFIL failed. Sanity test will not run.")
                loop.quit()
            elif self.checkDeviceStatus():
                logging.info(f"{self.boardName}: Device reached NORMAL status.")
                time.sleep(5)
                loop.quit()
        
        timer = QTimer()
        timer.timeout.connect(check_status)
        timer.start(1000)

        loop = QEventLoop()
        loop.exec_()

        if self.checkDeviceStatus():
            return True
        else:
            return False

    def handleAutomateQFIL(self):
        logging.info(f"{self.boardName}: Starting AutomateQFIL process.")
        try:
            self.turnOnVBATButton()
            if not self.waitForDeviceReady():
                return False
            
            self.mainApp.downloadImgButton.setChecked(True)
            self.mainApp.flashImgButton.setChecked(True)
            
            result = QEventLoop()
            self.mainApp.mAutomateQFIL.resultSignal.connect(lambda success: result.exit(0 if success else 1))
            self.mainApp.startFLButton.click()

            if result.exec_() != 0:
                logging.error(f"{self.boardName}: AutomateQFIL failed.")
                self.mAutomateReportOnCollab.isError = "Daily image build error."
                return False
            return True
        except Exception as e:
            logging.error(f"{self.boardName}: Error AutomateQFIL: {e}")
            return False
        
    def turnOnVBATButton(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if "USB-SERIAL CH340" in port.description or "Arduino Uno" in port.description:
                self.ArduinoPort = f"{port.device}"
                break

        if self.ArduinoPort != NO_PORT_CONNECTED:
            mArduinomgr = ArduinoManager(self.ArduinoPort)
            mArduinomgr.sendCommandRequest(BUB_OFF)
            mArduinomgr.sendCommandRequest(BOOT_OFF)
            mArduinomgr.sendCommandRequest(TCUA_VBAT_OFF)
            mArduinomgr.sendCommandRequest(VCM_VBAT_OFF)
            if self.boardName == JLR_VCM:
                mArduinomgr.sendCommandRequest(VCM_VBAT_ON)
            if self.boardName == JLR_TCUA:
                mArduinomgr.sendCommandRequest(TCUA_VBAT_ON)
            return True
        else:
            return False

    def handleAutomateSanity(self):
        logging.info(f"{self.boardName}: Starting sanity process.")
        try:
            if not self.loadRobotFile():
                return False
        
            if not self.startSanityTest():
                return False
            
            return True
        except Exception as e:
            logging.error(f"{self.boardName}: Error during sanity process: {e}")
            return False

    def loadRobotFile(self):
        logging.info(f"{self.boardName}: Loading Robot Framework files.")
        try:
            files = self.selectRobotFiles()
            if not files:
                return False
            self.mainApp.loadRobotTestCase(files)
            return True
        except Exception as e:
            logging.error(f"{self.boardName}: Error loading robot files: {e}")
            return False 

    def selectRobotFiles(self):
        boardPaths = {
            JLR_VCM: r"D:\01_TOOL\tiger-robot\testsuites_vcm",
            JLR_TCUA: r"D:\01_TOOL\tiger-robot\testsuites_tcua"
        }

        path = boardPaths.get(self.boardName)
        if not path or not os.path.isdir(path):
            logging.error("Invalid board name or directory.")
            return []

        files = [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

        if files:
            self.mainApp.robotFilePath = os.path.dirname(files[0])
            self.mainApp.parentSuite = os.path.basename(self.mainApp.robotFilePath)

        return files

    def startSanityTest(self):
        logging.info(f"{self.boardName}: Starting sanity test.")
        try:
            if not self.waitForDeviceReady():
                return False

            self.mainApp.startTaskButton.click()
            logging.info(f"{self.boardName}: Sanity test running...")
            while not self.mainApp.startTaskButton.isEnabled():
                QApplication.processEvents()
                time.sleep(0.1)
            print("All test finished")
            return True
        except Exception as e:
            logging.error(f"{self.boardName}: Error during sanity test: {e}")
            return False

    def run(self):
        return self.app.exec_()

def main():
    sanity = AutomationSanity()
    # QTimer.singleShot(1000, sanity.runAutomatedSanity)
    sys.exit(sanity.run())

if __name__ == "__main__":
    main()
