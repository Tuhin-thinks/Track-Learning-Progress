import json
import os
import sys
from functools import partial
from typing import List

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QComboBox,
                             QDialog, QFileDialog, QMainWindow, QMessageBox,
                             QTableWidget, QTableWidgetItem)

from UI import app_main, new_problems_dialog

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
    count = 0
    if selected_rows:
        row_indices = []
        for row_index in selected_rows:
            row_indices.append(row_index.row())
        row_indices.sort(key=lambda x: -1 * x)
        for row in row_indices:  # sorted in descending order
            table_widget.removeRow(row)
            count += 1
    return count

def setColortoRow(table, rowIndex, color:str):
    for j in range(table.columnCount()):
        try:
            table.item(rowIndex, j).setBackground(QColor(color))
        except AttributeError:
            pass

def delete_all_rows(table_widget: QTableWidget):
    """
    Just pass table_widget object, and all rows will be deleted
    """
    row_count = table_widget.rowCount()
    table_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
    setSel(list(range(row_count)), table_widget)
    remove_row_all_table(table_widget)
    table_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)


class AddProblems(QDialog):
    get_results = pyqtSignal(list)

    def __init__(self, prob_id):
        super(AddProblems, self).__init__()
        self.ui = new_problems_dialog.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowModality(Qt.ApplicationModal)

        self.prob_id = prob_id

        self.ui.lineEdit_probId.setText(str(self.prob_id))
        self.ui.pushButton_save.clicked.connect(self.validate)
        self.ui.pushButton_cancel.clicked.connect(self.close)

    def validate(self):
        problem_name = self.ui.lineEdit_name.text()
        topic = self.ui.lineEdit_topic.text()
        problem_link = self.ui.lineEdit_link.text()
        is_done = self.ui.comboBox.currentText()
        problem_id = self.ui.lineEdit_probId.text()

        flag = True
        for item in [problem_name, problem_link, topic]:
            if not (item is not None and item != ''):
                flag = False
        if flag:
            self.get_results.emit([problem_id, topic, problem_name, problem_link, is_done])
            self.close()
        else:
            showMessage("Invalid value", "You left some values empty, please try to enter them again", 'error')


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
        self.ui.pushButton_add_prob.clicked.connect(self.add_problem)
        self.ui.pushButton_remove_prob.clicked.connect(self.remove_record)

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
            isDone = 0 if is_done == 'No' else 1
            self.insert_problems_row(isDone)
            self.insert_table_row(temp_row)
            if isDone:
                setColortoRow(self.ui.tableWidget_problems, self.ui.tableWidget_problems.rowCount()-1, 'green')
            else:
                setColortoRow(self.ui.tableWidget_problems, self.ui.tableWidget_problems.rowCount()-1, 'red')
            self.last_id = id

    def insert_table_row(self, row_data):
        """
        Adds data to an empty row in the table
        :param row_data: data to be inserted in a row in the table
        :return:
        """
        row_count = self.ui.tableWidget_problems.rowCount()
        self.ui.tableWidget_problems.setItem(row_count - 1, 0, QTableWidgetItem(str(row_data[0])))
        self.ui.tableWidget_problems.setItem(row_count - 1, 1, QTableWidgetItem(str(row_data[1])))
        self.ui.tableWidget_problems.setItem(row_count - 1, 2, QTableWidgetItem(str(row_data[2])))

        self.ui.tableWidget_problems.cellWidget(row_count - 1, 3).setCurrentIndex(0 if row_data[3] == 'No' else 1)

    def show_cell_data(self, row_no, column):
        data_text = self.ui.tableWidget_problems.item(row_no, 2).text()
        if self.ui.tableWidget_problems.cellWidget(row_no, 3).currentIndex() == 0:
            self.ui.label_complete_def.setText(data_text + f'<br>Link: <a href="{self.links[row_no]}">{self.links[row_no]}</a>')
        else:
            self.ui.label_complete_def.setText(
                data_text + ' <strong>[COMPLETED]</strong>' + f'<br>Link: <a href="{self.links[row_no]}">{self.links[row_no]}</a>')

    def insert_problems_row(self, current_index=0):
        """
        Creates an empty row in the table (with combobox)
        :param current_index:
        :return:
        """
        row_count = self.ui.tableWidget_problems.rowCount()
        comboBox = QComboBox(self.ui.tableWidget_problems)
        comboBox.addItems(["No", "Yes"])
        comboBox.setStyleSheet('background-color: red;')
        comboBox.currentIndexChanged.connect(partial(self.check_changed_index, comboBox))
        comboBox.setCurrentIndex(current_index)

        self.ui.tableWidget_problems.insertRow(row_count)
        self.ui.tableWidget_problems.setCellWidget(row_count, 3, comboBox)
    
    def check_changed_index(self, comboBox, index):
        if index == 0: # no
            comboBox.setStyleSheet('background-color: red;')
        else:
            comboBox.setStyleSheet('background-color: green;')
            


    def save_data(self, mode='save', no_message=False):
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
            if not no_message:
                showMessage("File Saved", f"Data File saved at <em>{DEFAULT_FILE}</em>", 'info')
        elif mode == 'save-as':
            file_name = openFileNameDialog(self, filter="json file (*.json)")
            if file_name:
                with open(file_name, 'w') as json_file:
                    json.dump(all_data, json_file, indent=3)
                showMessage("File Saved", f"Data File saved at <em>{file_name}</em>", 'info')
                self.ui.statusbar.showMessage("File Saved!")

    def add_problem(self):
        self.add_prob_window = AddProblems(int(self.last_id) + 1)
        self.add_prob_window.get_results.connect(self.add_to_json)
        self.add_prob_window.show()

    def add_to_json(self, problem_data):
        problem_id, topic, problem_name, problems_link, is_done = problem_data[0], problem_data[1], problem_data[2], problem_data[3], problem_data[4]
        self.insert_problems_row(0 if is_done == 'No' else 1)
        self.insert_table_row([problem_id, topic, problem_name, is_done])
        self.last_id = problem_id
        self.save_data(no_message=True)  # updates record

    def remove_record(self):
        rows_deleted = remove_row_all_table(self.ui.tableWidget_problems)
        self.save_data(no_message=True)  # update records
        self.ui.statusbar.showMessage(f"{rows_deleted} rows removed, records have been updated",1000)  # show update for 1 sec


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = AppWindow()
    w.show()
    sys.exit(app.exec_())
