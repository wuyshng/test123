from robot import run
from robot.api import ExecutionResult, ResultVisitor
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
import os
import threading


class TestResultVisitor(ResultVisitor):
    signal = pyqtSignal(int)

    def __init__(self):
        self.countTestResult = 0
        self.results = []

    def visit_test(self, test):
        testName = test.name
        testStatus = test.status
        filePath = test.source
        fileName = os.path.basename(filePath).replace(".robot", "").strip()
        self.results.append((fileName, testName, testStatus))
        self.countTestResult += 1


class StopExecutionListener:
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, stop_event):
        self.stop_event = stop_event

    def start_test(self, name, attrs):
        if self.stop_event.is_set():
            raise SystemExit("Test execution stopped by user.")

    def end_test(self, name, attrs):
        pass


class RunRobotTestScript(QtCore.QThread):
    testResultSignal = pyqtSignal(str)  # Signal to send test result
    testProgressSignal = pyqtSignal(str)  # Signal to update test progress
    finishedSignal = pyqtSignal(str)  # Signal to notify test finished
    testCountSignal = pyqtSignal(int)

    def __init__(self, selectedTests, robotFilePath, outputDir, tableWidget):
        super().__init__()
        self.countTestResult = 0
        self.selectedTests = selectedTests
        self.robotFilePath = robotFilePath
        self.outputDir = outputDir
        self.tableWidget = tableWidget
        self.stop_event = threading.Event()  # Event to signal stopping execution

    def run(self):
        try:
            suiteTests = {}
            for test in self.selectedTests:
                suite, testName = test.split(".", 1)
                suiteTests.setdefault(suite, []).append(testName)

            for suite, tests in suiteTests.items():
                if self.stop_event.is_set():
                    break
                self.testProgressSignal.emit(f"Running suite: {suite}")
                run(self.robotFilePath, suite=suite, test=tests, outputdir=self.outputDir,
                    listener=StopExecutionListener(self.stop_event))
                self.processResults()

            if not self.stop_event.is_set():
                self.finishedSignal.emit("All tests completed.")
            else:
                self.finishedSignal.emit("Test execution stopped by user.")

        except Exception as e:
            print(f"Error: {str(e)}")

    def processResults(self):
        resultPath = os.path.join(self.outputDir, "output.xml")
        if not os.path.exists(resultPath):
            print("Result file does not exist!")
            return

        result = ExecutionResult(resultPath)
        visitor = TestResultVisitor()
        result.visit(visitor)

        self.countTestResult += visitor.countTestResult

        for fileName, testName, testStatus in visitor.results:
            testInfo = f"{fileName}:::{testName}:::{testStatus}"
            self.testCountSignal.emit(self.countTestResult)
            self.testResultSignal.emit(testInfo)

    def stop(self):
        self.stop_event.set()
        self.testProgressSignal.emit("Stopping tests.")
