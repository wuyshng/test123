import sys
from commonVariable import *
# Given the instruction of Test case

class testDatabase:
    def __init__(self):
        self.testCaseCounter = len(LIST_TC_NAME)

    def getTestCaseCounter(self, NAME = LIST_TC_NAME):
        self.testCaseCounter = len(NAME)
        return self.testCaseCounter

    def getTCName(self, testCase, NAME = LIST_TC_NAME):
        if testCase in NAME:
            return NAME[testCase]
        else:
            return NO_DATA_FOUND

    def getTestCaseDescription(self, testCase, DESCRIPTION = LIST_TEST_DESCRIPTION):
        if testCase in DESCRIPTION:
            return DESCRIPTION[testCase]
        else:
            return NO_DATA_FOUND

    def getTestCaseExpectedResult(self, testCase, EXPECTED_RES = LIST_EXPECTED_RESULT):
        if testCase in EXPECTED_RES:
            return EXPECTED_RES[testCase]
        else:
            return NO_DATA_FOUND

if __name__ == '__main__':
    tc = testDatabase()
    # print(tc.getTestCaseDescription(TEST_CASE_START))
    # print(tc.getTestCaseExpectedResult(TEST_CASE_START))
