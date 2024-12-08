import sys
from PyQt5.QtWidgets import QApplication, QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QCheckBox
from PyQt5.QtCore import Qt

class CheckboxTableApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 400, 300)
        self.setWindowTitle('Checkbox Table Example')

        table = QTableWidget()
        table.setColumnCount(6)
        table.setRowCount(3)
        table.setHorizontalHeaderLabels(['Item', 'Select'])

        for row in range(3):
            item = QTableWidgetItem(f'Item {row+1}')
            table.setItem(row, 0, item)

            checkbox = QCheckBox()
            checkbox_item = QWidget()
            checkbox_layout = QVBoxLayout()
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)  # Align the checkbox to the center
            checkbox_item.setLayout(checkbox_layout)
            table.setCellWidget(row, 2, checkbox_item)

        layout = QVBoxLayout()
        layout.addWidget(table)
        self.setLayout(layout)

        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = CheckboxTableApp()
    sys.exit(app.exec_())