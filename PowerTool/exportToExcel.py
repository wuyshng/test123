import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton, QToolBar, QAction, QFileDialog
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

class TableExporter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.table_widget = QTableWidget()
        self.table_widget.setRowCount(3)
        self.table_widget.setColumnCount(2)

        for i in range(3):
            for j in range(2):
                item = QTableWidgetItem(f"Item {i}-{j}")
                self.table_widget.setItem(i, j, item)

        export_action = QAction("Export to Excel", self)
        export_action.triggered.connect(self.export_to_excel)

        toolbar = QToolBar()
        toolbar.addAction(export_action)
        self.addToolBar(toolbar)

        self.setCentralWidget(self.table_widget)
        self.setWindowTitle("Table Data Exporter")
        self.show()

    def export_to_excel(self):
        df = pd.DataFrame(index=range(self.table_widget.rowCount()), columns=range(self.table_widget.columnCount()))

        for row in range(self.table_widget.rowCount()):
            for column in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, column)
                if item is not None:
                    df.at[row, column] = item.text()

        file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Excel Files (*.xlsx)")

        if file_name:
            wb = Workbook()
            ws = wb.active

            for r in dataframe_to_rows(df, index=False, header=False):
                ws.append(r)

            wb.save(file_name)

app = QApplication(sys.argv)
window = TableExporter()
sys.exit(app.exec_())