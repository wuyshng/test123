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
        self.suite_mappings = {}
        self.test_counts = {}

    def start_suite(self, suite, result):
        if not suite.tests:
            self.test_counts = {}

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
        self.testCaseFragment = self.get_test_case_fragment(test.longname)
        self.signal.emit(self.results, self.countTestResult, self.testCaseFragment)

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

    def get_test_case_fragment(self, longname):
        parts = longname.split('.')
        suite_path = parts[:-1]
        
        fragment_parts = []
        current_path = []
        
        for suite in suite_path:
            current_path.append(suite)
            path_key = '.'.join(current_path)

            if path_key not in self.suite_mappings:
                parent_path = '.'.join(current_path[:-1])
                if parent_path in self.suite_mappings:
                    existing_numbers = set()
                    for existing_path in self.suite_mappings:
                        if existing_path.startswith(parent_path + '.'):
                            existing_numbers.add(self.suite_mappings[existing_path])
                    next_number = 1
                    while next_number in existing_numbers:
                        next_number += 1
                    self.suite_mappings[path_key] = next_number
                else:
                    self.suite_mappings[path_key] = 1
            
            fragment_parts.append(f"s{self.suite_mappings[path_key]}")
        
        suite_key = '.'.join(suite_path)
        if suite_key not in self.test_counts:
            self.test_counts[suite_key] = 1
        test_number = self.test_counts[suite_key]
        fragment_parts.append(f"t{test_number}")
        
        self.test_counts[suite_key] += 1
        
        return '-'.join(fragment_parts)

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

    def run(self):
        self.add_parent_suite_to_selected_tests(self.parentSuite)
        self.testSuites = os.path.basename(self.robotFilePath)
        try:
            run(self.robotFilePath, suite=self.testSuites, test=self.selectedTests, outputdir=self.outputDir,
                listener=RobotListener(self.stop_event, self.logSignal, self.signal))

            if not self.stop_event.is_set():
                self.finishedSignal.emit("All tests completed.")
            else:
                self.finishedSignal.emit("Test execution stopped by user.")

        except Exception as e:
            print(f"Error: {str(e)}")

    def processResults(self, message, value, fragment):
        self.countTestResult = value

        for fileName, testName, testStatus in message:
            testInfo = f"{fileName}:::{testName}:::{testStatus}"
            self.testCountSignal.emit(self.countTestResult)
            self.testResultSignal.emit(testInfo, fragment)

    def add_parent_suite_to_selected_tests(self, parentSuite):
        self.selectedTests = [
            f"{parentSuite}.{test}" if not test.startswith(parentSuite) else test
            for test in self.selectedTests
        ]

    def stop(self):
        self.stop_event.set()
