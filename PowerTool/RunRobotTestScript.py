import os
import threading
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from robot import run
from robot.api.interfaces import ListenerV3


class RobotListener(ListenerV3):
    def __init__(self, stop_event, logSignal, signal):
        self.stop_event = stop_event
        self.logSignal = logSignal
        self.signal = signal
        self.lineWidth = 78
        self.maxLength = 69
        self.suiteName = None
        self.testName = None
        self.testResult = None
        self.results = []
        self.countTestResult = 0

    def start_suite(self, suite, result):
        self.suiteName = suite.name.replace(" ", "_").lower() + ".robot"
        self.testCount = 0
        self.testPassed = 0
        self.testFailed = 0
        self.testSkipped = 0

        if suite.tests:
            self.logSignal.emit(f"<pre style='font-family: Consolas; font-size: 24px;'>{'=' * self.lineWidth}</pre>")
            if suite.doc:
                first_line = suite.doc.strip().splitlines()[0]
                self.logSignal.emit(f"<pre style='font-family: Consolas; font-size: 24px;'>{suite.name} :: {first_line}</pre>")
            else:
                self.logSignal.emit(f"<pre style='font-family: Consolas; font-size: 24px;'>{suite.name}</pre>")
            self.logSignal.emit(f"<pre style='font-family: Consolas; font-size: 24px;'>{'=' * self.lineWidth}</pre>")
    
    def start_test(self, test, result):
        self.results = []
        self.testName = test.name

    def end_test(self, test, result):
        if self.stop_event.is_set():
            raise SystemExit("Test execution stopped by user.")
        
        self.testCount += 1
        if result.passed:
            status = "<font color='green'>PASS</font>"
            self.testPassed += 1
        elif result.skipped:
            status = "<font color='yellow'>SKIP</font>"
            self.testSkipped += 1
        else:
            status = "<font color='red'>FAIL</font>"
            self.testFailed += 1

        test_name = test.name.strip()

        if len(test_name) > self.maxLength:
            test_name = test_name[:self.maxLength - 3] + "..."
        padded_test_name = test_name.ljust(self.maxLength)

        self.logSignal.emit(f"<pre style='font-family: Consolas; font-size: 24px;'>{padded_test_name} | {status} |</pre>")

        if not result.passed:
            failure_message = result.message.strip()
            self.logSignal.emit(f"<pre style='font-family: Consolas; font-size: 24px;'>{failure_message}</pre>")
        
        self.logSignal.emit(f"<pre style='font-family: Consolas; font-size: 24px;'>{'-' * self.lineWidth}</pre>")

        self.testResult = result.status
        self.results.append((self.suiteName, self.testName, self.testResult))
        self.countTestResult += 1
        self.testCaseFragment = test.id
        self.signal.emit(self.results, self.countTestResult, self.testCaseFragment)

    def end_suite(self, suite, result):
        status, status_color = (
            ("PASS", "green") if result.passed else
            ("FAIL", "red") if result.failed else
            ("SKIP", "yellow")
        )

        if suite.doc:
            suite_name = f"{suite.name} :: {suite.doc.strip().splitlines()[0]}"
        else:
            suite_name = suite.name

        if len(suite_name) > self.maxLength:
            suite_name = suite_name[:self.maxLength - 3] + "..."
        padded_suite_name = suite_name.ljust(self.maxLength)

        self.logSignal.emit(f"<pre style='font-family: Consolas; font-size: 24px;'>{padded_suite_name} | <font color='{status_color}'>{status}</font> |</pre>")

        summary = f"{self.testCount} tests, {self.testPassed} passed, {self.testFailed} failed, {self.testSkipped} skipped"
        self.logSignal.emit(f"<pre style='font-family: Consolas; font-size: 24px;'>{summary}</pre>")

        self.logSignal.emit(f"<pre style='font-family: Consolas; font-size: 24px;'>{'=' * self.lineWidth}</pre>")

    def output_file(self, path):
        self.logSignal.emit(f"<pre style='font-family: Consolas; font-size: 24px;'>Output:  {path}</pre>")

    def log_file(self, path):
        self.logSignal.emit(f"<pre style='font-family: Consolas; font-size: 24px;'>Log:     {path}</pre>")

    def report_file(self, path):
        self.logSignal.emit(f"<pre style='font-family: Consolas; font-size: 24px;'>Report:  {path}</pre>")

class RunRobotTestScript(QtCore.QThread):
    signal = pyqtSignal(list, int, str)
    testResultSignal = pyqtSignal(str, str) 
    finishedSignal = pyqtSignal(str)
    logSignal = pyqtSignal(str)
    testCountSignal = pyqtSignal(int)

    def __init__(self, selectedTests, robotFilePath, parentSuite, outputDir, tableWidget):
        super().__init__()
        self.countTestResult = 0
        self.selectedTests = selectedTests
        self.robotFilePath = robotFilePath
        self.parentSuite = parentSuite
        self.outputDir = outputDir
        self.tableWidget = tableWidget
        self.stop_event = threading.Event()  # Event to signal stopping execution
        self.signal.connect(self.processResults)
        self.result = False

    def run(self):
        self.addParentSuiteToSelectedTest(self.parentSuite)
        self.testSuites = os.path.basename(self.robotFilePath)
        try:
            run(self.robotFilePath, suite=self.testSuites, test=self.selectedTests, outputdir=self.outputDir,
                listener=RobotListener(self.stop_event, self.logSignal, self.signal))

            if not self.stop_event.is_set():
                self.finishedSignal.emit("All tests completed.")
                self.result = True
            else:
                self.result = False

        except Exception as e:
            print(f"Error: {str(e)}")

    def processResults(self, message, value, fragment):
        self.countTestResult = value

        for fileName, testName, testStatus in message:
            testInfo = f"{fileName}:::{testName}:::{testStatus}"
            self.testCountSignal.emit(self.countTestResult)
            self.testResultSignal.emit(testInfo, fragment)

    def addParentSuiteToSelectedTest(self, parentSuite):
        self.selectedTests = [
            f"{parentSuite}.{test}" if not test.startswith(parentSuite) else test
            for test in self.selectedTests
        ]

    def stop(self):
        self.stop_event.set()
