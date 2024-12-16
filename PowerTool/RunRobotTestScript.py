import os
import threading
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from robot import run
from robot.api import ExecutionResult, ResultVisitor


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
    ROBOT_LISTENER_API_VERSION = 3

    def __init__(self, stop_event, logSignal):
        self.stop_event = stop_event
        self.logSignal = logSignal
        self.lineWidth = 78
        self.maxLength = 69
    
    def start_suite(self, suite, result):
        self.testCount = 0
        self.testPassed = 0
        self.testFailed = 0
        self.testSkipped = 0

        # Log suite name and first line of documentation only for leaf suites
        if suite.tests:  # Suite has tests
            self.logSignal.emit(f"<pre>{'=' * self.lineWidth}</pre>")
            if suite.doc:
                first_line = suite.doc.strip().splitlines()[0]
                self.logSignal.emit(f"<pre>{suite.name} :: {first_line}</pre>")
            else:
                self.logSignal.emit(f"<pre>{suite.name}</pre>")
            self.logSignal.emit(f"<pre>{'=' * self.lineWidth}</pre>")

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
            test_name = test_name[:self.maxLength - 3] + "..."  # Truncate with '...'

        padded_test_name = test_name.ljust(self.maxLength)

        self.logSignal.emit(f"<pre>{padded_test_name} | {status} |</pre>")

        # Log failure or skip message
        if not result.passed:
            failure_message = result.message.strip()
            self.logSignal.emit(f"<pre>{failure_message}</pre>")
        
        self.logSignal.emit(f"<pre>{'-' * self.lineWidth}</pre>")

    def end_suite(self, suite, result):
        status = "FAIL" if self.testFailed else "PASS"
        status_color = "red" if self.testFailed else "green"

        if suite.doc:
            suite_name = f"{suite.name} :: {suite.doc.strip().splitlines()[0]}"
        else:
            suite_name = suite.name

        if len(suite_name) > self.maxLength:
            suite_name = suite_name[:self.maxLength - 3] + "..."
        padded_suite_name = suite_name.ljust(self.maxLength)

        self.logSignal.emit(f"<pre>{padded_suite_name} | <font color='{status_color}'>{status}</font> |</pre>")

        summary = f"{self.testCount} tests, {self.testPassed} passed, {self.testFailed} failed, {self.testSkipped} skipped"
        self.logSignal.emit(f"<pre>{summary}</pre>")

        self.logSignal.emit(f"<pre>{'=' * self.lineWidth}</pre>")

    def output_file(self, path):
        self.logSignal.emit(f"<pre>Output:  {path}</pre>")

    def log_file(self, path):
        self.logSignal.emit(f"<pre>Log:     {path}</pre>")

    def report_file(self, path):
        self.logSignal.emit(f"<pre>Report:  {path}</pre>")


class RunRobotTestScript(QtCore.QThread):
    testResultSignal = pyqtSignal(str)      # Signal to send test result
    testProgressSignal = pyqtSignal(str)    # Signal to update test progress
    finishedSignal = pyqtSignal(str)        # Signal to notify test finished
    logSignal = pyqtSignal(str)
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
                # self.testProgressSignal.emit(f"Running suite: {suite}")
                run(self.robotFilePath, suite=suite, test=tests, outputdir=self.outputDir,
                    listener=StopExecutionListener(self.stop_event, self.logSignal))
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
