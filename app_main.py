import os
import json
import sys
from functools import partial

from PyQt5.QtWidgets import QApplication, QMainWindow, QComboBox, QTableWidgetItem, QMessageBox, QFileDialog, QAbstractItemView, QTableWidget
from PyQt5.QtCore import Qt
from typing import List
from UI import app_main

PREFERENCES_DIR = "./UI/preference/preference.config"
if not os.path.exists(os.path.dirname(PREFERENCES_DIR)):
    os.mkdir(os.path.dirname(PREFERENCES_DIR))
    with open(PREFERENCES_DIR, 'w') as preference:
        json.dump({}, preference, indent=3)
if not os.path.exists(PREFERENCES_DIR):
    with open(PREFERENCES_DIR, 'w') as preference:
        json.dump({}, preference, indent=3)

with open(PREFERENCES_DIR, 'r') as preferences_file:
    preferences = json.load(preferences_file)
if preferences:
    DEFAULT_FILE = preferences['default_file']
else:
    DEFAULT_FILE = 'FINAL450.json'


def update_preference(data):
    with open(PREFERENCES_DIR, 'w') as preference_update:
        json.dump(data, preference_update, indent=3)


def showMessage(title, text, message_type):
    if message_type == 'info':
        message = QMessageBox(QMessageBox.Information, title, text, QMessageBox.Ok)
        message.exec_()
    elif message_type == 'warning':
        message = QMessageBox(QMessageBox.Warning, title, text, QMessageBox.Close)
        message.exec_()
    elif message_type == 'error':
        message = QMessageBox(QMessageBox.Critical, title, text, QMessageBox.Retry)
        message.exec_()


def saveFileDialog(parent, title="Save Cracker Sheet", extension="Json File (*.json)"):
    options = QFileDialog.Options()
    fileName, _ = QFileDialog.getSaveFileName(parent, caption=title, filter=extension, options=options)
    if fileName:
        return fileName


def openFileNameDialog(parent, title="Open Cracker Sheet", filter="Json File (*.json)"):
    options = QFileDialog.Options()
    fileName, _ = QFileDialog.getOpenFileName(parent, caption=title, filter=filter, options=options)
    if fileName:
        return fileName


def setSel(selected: List[int], table_widget: QTableWidget):
    """
    Select all rows for the given index range
    """
    table_widget.setSelectionMode(QAbstractItemView.MultiSelection)
    for i in selected:
        table_widget.selectRow(i)


def remove_row_all_table(table_widget):
    """
    Select and Delete rows from table widget
    """
    table_widget: QTableWidget
    selected_rows = table_widget.selectionModel().selectedRows()
    if selected_rows:
        row_indices = []
        for row_index in selected_rows:
            row_indices.append(row_index.row())
        row_indices.sort(key=lambda x: -1 * x)
        for row in row_indices:  # sorted in descending order
            table_widget.removeRow(row)


def delete_all_rows(table_widget: QTableWidget):
    """
    Just pass table_widget object, and all rows will be deleted
    """
    row_count = table_widget.rowCount()
    table_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
    setSel(list(range(row_count)), table_widget)
    remove_row_all_table(table_widget)
    table_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)


class AppWindow(QMainWindow):
    def __init__(self):
        super(AppWindow, self).__init__()
        self.column_count = 4
        self.ui = app_main.Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.tableWidget_problems.setColumnCount(4)
        self.ui.tableWidget_problems.setHorizontalHeaderLabels(['Id', 'Topic', "Problem Name", "Is Done?"])
        global DEFAULT_FILE
        if not os.path.exists(DEFAULT_FILE):
            self.load_or_close()
        else:
            showMessage("File Loaded", f"DSA cracker sheet loaded from:{DEFAULT_FILE}", 'info')
        self.table_data = self.load_json()
        self.load_data(self.table_data)

        self.ui.tableWidget_problems.cellPressed.connect(self.show_cell_data)
        self.ui.pushButton_save.clicked.connect(partial(self.save_data, 'save'))
        self.ui.actionSave_As.triggered.connect(partial(self.save_data, 'save-as'))
        self.ui.actionShow_Pending_Problems.triggered.connect(partial(self.show_filtered, 'pending'))
        self.ui.actionShow_Completed_Problems.triggered.connect(partial(self.show_filtered, 'completed'))
        self.ui.actionLoad_Sheet.triggered.connect(self.load_or_close)

        self.ui.label_complete_def.setOpenExternalLinks(True)
        self.ui.label_complete_def.setTextInteractionFlags(Qt.LinksAccessibleByMouse)

    def load_or_close(self):
        global DEFAULT_FILE
        file_name = openFileNameDialog(self, "Open Cracker Sheet Problems Files", 'json file (*.json)')
        if file_name:
            DEFAULT_FILE = file_name
            update_preference({'default_file': file_name})
            self.ui.statusbar.showMessage("Preference file updated!")
        else:
            showMessage("Exiting Program", "DEFAULT FILE DOESN'T EXIST, CRACKER SHEET NOT SELECTED, EXITING PROGRAM", 'error')
            self.close()
        self.table_data = self.load_json()
        self.load_data(self.table_data)

    def show_filtered(self, filter_by):
        if filter_by == 'pending':
            row_count = self.ui.tableWidget_problems.rowCount()
            for row in range(row_count):
                is_hidden = self.ui.tableWidget_problems.cellWidget(row, 3).currentIndex()
                if is_hidden == 0:  # no
                    self.ui.tableWidget_problems.showRow(row)
                else:
                    self.ui.tableWidget_problems.hideRow(row)
        else:
            row_count = self.ui.tableWidget_problems.rowCount()
            for row in range(row_count):
                is_hidden = self.ui.tableWidget_problems.cellWidget(row, 3).currentIndex()
                if is_hidden == 0:  # no
                    self.ui.tableWidget_problems.hideRow(row)
                else:
                    self.ui.tableWidget_problems.showRow(row)

    @staticmethod
    def load_json():
        with open(DEFAULT_FILE, 'r') as data:
            table_data = json.load(data)
        return table_data

    def load_data(self, data):
        """
        :param parent:
        :param data: json dictionary
        :return:
        """
        delete_all_rows(self.ui.tableWidget_problems)  # All rows will be deleted before adding new ones
        if not data:
            data = {}
        prob_id, prob_name, topic, done = [], [], [], []
        self.links = []
        for k, v in data.items():
            if k == 'Problem:':
                for row in v:
                    id = row['ID']
                    name = row['Name']
                    link = row['Link']
                    prob_id.append(id)
                    prob_name.append(name)
                    self.links.append(link)
            elif k == 'Done [yes or no]':
                for row in v:
                    done.append(row)
            elif k == 'Topic:':
                for row in v:
                    topic.append(row)
        print(f"len problem_id: {len(prob_id)}, prob_name: {len(prob_name)}, topic: {len(topic)}, done:{len(done)}\n")
        for id, name, tpic, is_done in zip(prob_id, prob_name, topic, done):
            temp_row = [id, tpic, name, is_done]
            self.insert_problems_row(0 if is_done == 'No' else 1)
            self.insert_table_row(temp_row)

    def insert_table_row(self, row_data):
        row_count = self.ui.tableWidget_problems.rowCount()
        self.ui.tableWidget_problems.setItem(row_count - 1, 0, QTableWidgetItem(str(row_data[0])))
        self.ui.tableWidget_problems.setItem(row_count - 1, 1, QTableWidgetItem(str(row_data[1])))
        self.ui.tableWidget_problems.setItem(row_count - 1, 2, QTableWidgetItem(str(row_data[2])))

        self.ui.tableWidget_problems.cellWidget(row_count - 1, 3).setCurrentIndex(0 if row_data[-1] == 'No' else 1)

    def show_cell_data(self, row_no, column):
        data_text = self.ui.tableWidget_problems.item(row_no, 2).text()
        if self.ui.tableWidget_problems.cellWidget(row_no, 3).currentIndex() == 0:
            self.ui.label_complete_def.setText(data_text + f'<br>Link: <a href="{self.links[row_no]}">{self.links[row_no]}</a>')
        else:
            self.ui.label_complete_def.setText(
                data_text + ' <strong>[COMPLETED]</strong>' + f'<br>Link: <a href="{self.links[row_no]}">{self.links[row_no]}</a>')

    def insert_problems_row(self, current_index=0):
        row_count = self.ui.tableWidget_problems.rowCount()
        comboBox = QComboBox(self.ui.tableWidget_problems)
        comboBox.addItems(["No", "Yes"])
        comboBox.setCurrentIndex(current_index)

        self.ui.tableWidget_problems.insertRow(row_count)
        self.ui.tableWidget_problems.setCellWidget(row_count, 3, comboBox)

    def save_data(self, mode='save'):
        row_count = self.ui.tableWidget_problems.rowCount()
        all_data = {}
        ids = []
        problems = []
        topics = []
        is_dones = []
        for row in range(row_count):
            id = self.ui.tableWidget_problems.item(row, 0).text()
            ids.append(id)
            topic = self.ui.tableWidget_problems.item(row, 1).text()
            topics.append(topic)
            name = self.ui.tableWidget_problems.item(row, 2).text()
            problems.append({"ID": id, "Name": name, "Link": self.links[row]})
            is_done = self.ui.tableWidget_problems.cellWidget(row, 3).currentText()
            is_dones.append(is_done)
            all_data = {'Topic:': topics, "Problem:": problems, "Done [yes or no]": is_dones}
        if mode == 'save':
            with open(DEFAULT_FILE, 'w') as json_file:
                json.dump(all_data, json_file, indent=3)
            showMessage("File Saved", f"Data File saved at <em>{DEFAULT_FILE}</em>", 'info')
        elif mode == 'save-as':
            file_name = openFileNameDialog(self, filter="json file (*.json)")
            if file_name:
                with open(file_name, 'w') as json_file:
                    json.dump(all_data, json_file, indent=3)
                showMessage("File Saved", f"Data File saved at <em>{file_name}</em>", 'info')
                self.ui.statusbar.showMessage("File Saved!")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = AppWindow()
    w.show()
    sys.exit(app.exec_())
