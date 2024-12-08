import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QCheckBox, QTableWidgetItem, QWidget, QVBoxLayout
from robot.api.parsing import ModelVisitor, Token

class LoadRobotTestCase(ModelVisitor):
    def __init__(self, tableWidget, startRow, TCcheckBoxList):
        super().__init__()
        self.tableWidget = tableWidget
        self.currentRow = startRow
        self.fileTestCases = {}
        self.TCcheckBoxList = TCcheckBoxList

    def visit_File(self, node):
        self.tableWidget.insertRow(self.currentRow)

        fileCheckbox = QCheckBox()
        fileCheckboxWidget = QWidget()
        fileCheckboxLayout = QVBoxLayout()
        fileCheckboxLayout.addWidget(fileCheckbox)
        fileCheckboxLayout.setAlignment(Qt.AlignCenter)
        fileCheckboxWidget.setLayout(fileCheckboxLayout)
        self.tableWidget.setCellWidget(self.currentRow, 0, fileCheckboxWidget)

        currentFile = str(os.path.basename(node.source))
        self.tableWidget.setItem(self.currentRow, 1, QTableWidgetItem(currentFile))

        fileItem = self.tableWidget.item(self.currentRow, 1)
        fileItem.setTextAlignment(Qt.AlignCenter)

        fileRow = self.currentRow
        self.fileTestCases[fileRow] = []

        fileCheckbox.stateChanged.connect(lambda state, row=fileRow: self.toggleTestCaseCheckboxes(row, state))

        self.currentRow += 1
        self.generic_visit(node)

    def visit_TestCase(self, node):
        self.tableWidget.insertRow(self.currentRow)

        checkbox = QCheckBox()
        checkboxWidget = QWidget()
        checkboxLayout = QVBoxLayout()
        checkboxLayout.addWidget(checkbox)
        checkboxLayout.setAlignment(Qt.AlignCenter)
        checkboxWidget.setLayout(checkboxLayout)
        self.tableWidget.setCellWidget(self.currentRow, 0, checkboxWidget)

        self.tableWidget.setItem(self.currentRow, 2, QTableWidgetItem(node.name))

        testSteps = []
        for step in node.body:
            if step.type == Token.KEYWORD:
                stepText = f"{step.keyword}    {' '.join(step.args)}" if step.args else step.keyword
                testSteps.append(stepText)
        self.tableWidget.setItem(self.currentRow, 3, QTableWidgetItem("\n".join(testSteps)))
        self.tableWidget.setItem(self.currentRow, 4, QTableWidgetItem(""))
        self.tableWidget.setItem(self.currentRow, 5, QTableWidgetItem(""))

        self.tableWidget.resizeRowToContents(self.currentRow)

        fileRow = max(self.fileTestCases.keys())
        self.fileTestCases[fileRow].append(self.currentRow)
        self.TCcheckBoxList[self.currentRow] = checkbox

        self.currentRow += 1

    def toggleTestCaseCheckboxes(self, fileRow, state):
        isChecked = state == Qt.Checked
        for testCaseRow in self.fileTestCases[fileRow]:
            checkboxWidget = self.tableWidget.cellWidget(testCaseRow, 0)
            if checkboxWidget:
                checkbox = checkboxWidget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(isChecked)
