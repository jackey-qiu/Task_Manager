from PyQt5 import QtCore
from PyQt5.QtWidgets import QCheckBox, QRadioButton, QDialog, QTableWidgetItem, QHeaderView, QAbstractItemView, QInputDialog, QDialog,QShortcut
from PyQt5.QtCore import Qt, QTimer, QEventLoop, QThread, QModelIndex
from PyQt5.QtGui import QTransform, QFont, QBrush, QColor, QIcon, QImage, QPixmap
from pyqtgraph.Qt import QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PyQt5 import uic, QtWidgets
import PyQt5
#The following three lines are necessary as a detoure to the incompatibiltiy of Qt5 APP showing in Mac Big Sur OS
#This solution seems non-sense, since the matplotlib is not used in the app.
#But if these lines are removed, the app GUI is not gonna pop up.
#This situation may change in the future.
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("TkAgg")
import qdarkstyle
import sys,os,copy
import cv2
import logging
import time, datetime
import functools
import pandas as pd
from pymongo import MongoClient
try:
    from . import locate_path
except:
    import locate_path
script_path = locate_path.module_path_locator()

class PandasModel(QtCore.QAbstractTableModel):
    """
    Class to populate a table view with a pandas dataframe
    """
    def __init__(self, data, tableviewer, main_gui, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._data = data
        self.tableviewer = tableviewer
        self.main_gui = main_gui

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role):
        if index.isValid():
            if role in [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole]:
                return str(self._data.iloc[index.row(), index.column()])
            if role == QtCore.Qt.BackgroundRole and index.row()%2 == 0:
                return QtGui.QColor('DeepSkyBlue')
                # return QtGui.QColor('green')
            if role == QtCore.Qt.BackgroundRole and index.row()%2 == 1:
                return QtGui.QColor('aqua')
                # return QtGui.QColor('lightGreen')
            if role == QtCore.Qt.ForegroundRole and index.row()%2 == 1:
                return QtGui.QColor('black')
            '''
            if role == QtCore.Qt.CheckStateRole and index.column()==0:
                if self._data.iloc[index.row(),index.column()]:
                    return QtCore.Qt.Checked
                else:
                    return QtCore.Qt.Unchecked
            '''
        return None

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        '''
        if role == QtCore.Qt.CheckStateRole and index.column() == 0:
            if value == QtCore.Qt.Checked:
                self._data.iloc[index.row(),index.column()] = True
            else:
                self._data.iloc[index.row(),index.column()] = False
        else:
        '''
        if str(value)!='':
            self._data.iloc[index.row(),index.column()] = str(value)
        #if self._data.columns.tolist()[index.column()] in ['select','archive_data','user_label','read_level']:
        #    self.main_gui.update_meta_info_paper(paper_id = self._data['paper_id'][index.row()])
        self.dataChanged.emit(index, index)
        self.layoutAboutToBeChanged.emit()
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rowCount(0), self.columnCount(0)))
        self.layoutChanged.emit()
        self.tableviewer.resizeColumnsToContents() 
        return True

    def update_view(self):
        self.layoutAboutToBeChanged.emit()
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rowCount(0), self.columnCount(0)))
        self.layoutChanged.emit()

    def headerData(self, rowcol, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._data.columns[rowcol]         
        if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            return self._data.index[rowcol]         
        return None

    def flags(self, index):
        if not index.isValid():
           return QtCore.Qt.NoItemFlags
        else:
            return (QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable)

    def sort(self, Ncol, order):
        """Sort table by given column number."""
        self.layoutAboutToBeChanged.emit()
        self._data = self._data.sort_values(self._data.columns.tolist()[Ncol],
                                        ascending=order == QtCore.Qt.AscendingOrder, ignore_index = True)
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rowCount(0), self.columnCount(0)))
        self.layoutChanged.emit()

class MyMainWindow(QMainWindow):
    def __init__(self, parent = None):
        super(MyMainWindow, self).__init__(parent)
        #load GUI ui file made by qt designer
        ui_path = os.path.join(script_path,'task_manager.ui')
        uic.loadUi(ui_path,self)
        self.widget_terminal.update_name_space('main_gui',self)
        self.timer_update_time = QTimer(self)
        self.timer_update_time.timeout.connect(self.set_time_label)
        self.timer_update_time.start(1000)
        self.pushButton_init.clicked.connect(self.init_task_table)
        self.pushButton_show_hide.clicked.connect(self.show_or_hide_editor)
        self.pushButton_save.clicked.connect(self.save_task_table)
        self.comboBox_task_files.activated.connect(self.set_task_file)
        self.pushButton_transfer.clicked.connect(self.transfer_data)
        self.pushButton_insert_row.clicked.connect(self.insert_one_row)
        self.pushButton_remove_rows.clicked.connect(self.remove_selected_rows)
        self.load_task_files()
        self.init_task_file()
        self.init_task_table()

    def transfer_data(self):
        now = datetime.datetime.now()
        data = copy.deepcopy(self.pandas_model2._data)
        data['date'] = now.strftime("%Y-%m-%d") 
        self.pandas_model = PandasModel(data = data, tableviewer = self.tableView_task, main_gui = self)
        self.tableView_task.setModel(self.pandas_model)
        self.tableView_task.resizeColumnsToContents()
        self.tableView_task.setSelectionBehavior(PyQt5.QtWidgets.QAbstractItemView.SelectRows)

    def insert_one_row(self):
        if len(self.tableView_task.selectionModel().selectedRows())==0:
            selected_row = len(self.pandas_model._data.index)-1
        else:
            selected_row = self.tableView_task.selectionModel().selectedRows()[0].row()
        new_data = {}
        for each in list(self.pandas_model._data.columns):
            items = self.pandas_model._data[each].tolist()
            if each=='task_label':
                new_data[each] = items[0:selected_row] + [items[selected_row]] + ['Task {}'.format(int(each.rsplit()[-1])+1) for each in items[selected_row:]]
            else:
                new_data[each] = items[0:selected_row] + [items[selected_row]] + items[selected_row:]
        self.pandas_model = PandasModel(data = pd.DataFrame(new_data), tableviewer = self.tableView_task, main_gui = self)
        self.tableView_task.setModel(self.pandas_model)
        self.tableView_task.resizeColumnsToContents()
        self.tableView_task.setSelectionBehavior(PyQt5.QtWidgets.QAbstractItemView.SelectRows)

    def remove_selected_rows(self):
        selected_rows = [each.row() for each in self.tableView_task.selectionModel().selectedRows()]
        new_data = {}
        for each in list(self.pandas_model._data.columns):
            items = self.pandas_model._data[each].tolist()
            new_items = [each_item for i, each_item in enumerate(items) if i not in selected_rows]
            if each == 'task_label':
                new_items = ['Task {}'.format(i) for i, item in enumerate(new_items)]
            new_data[each] = new_items
        self.pandas_model = PandasModel(data = pd.DataFrame(new_data), tableviewer = self.tableView_task, main_gui = self)
        self.tableView_task.setModel(self.pandas_model)
        self.tableView_task.resizeColumnsToContents()
        self.tableView_task.setSelectionBehavior(PyQt5.QtWidgets.QAbstractItemView.SelectRows)

    def load_task_files(self):
        self.comboBox_task_files.clear()
        self.comboBox_task_files.addItems(os.listdir(os.path.join(script_path,'task_files')))

    def show_or_hide_editor(self):
        if self.frame_2.isHidden():
            self.frame_2.show()
        else:
            self.frame_2.hide()

    def set_time_label(self):
        now = datetime.datetime.now()
        time_ = now.strftime("%H:%M:%S")
        year = now.year
        month = now.month
        day = now.day
        weekday = now.weekday()
        weekday_map = {0:'Monday',1:'Tuesday',2:'Wednesday',3:'Thursday',4:'Friday',5:'Saturday',6:'Sunday'}
        # self.label_date.setText('{}-{}-{},{}'.format(year, month, day, weekday_map[weekday]))
        self.label_time.setText(time_)
        task_info = self.formate_task_info_from_pandas_model()
        self.task_widget.update_task_info(task_info)
        self.task_widget.update()
        if self.task_widget.current_task[0]!=None:
            self.lineEdit_current_task.setText(self.task_widget.current_task[0])
            self.lineEdit_end.setText(self.task_widget.task_info[self.task_widget.current_task[0]][1])
            begin = datetime.datetime.strptime(self.task_widget.task_info[self.task_widget.current_task[0]][0], '%H:%M')
            end = datetime.datetime.strptime(self.task_widget.task_info[self.task_widget.current_task[0]][1], '%H:%M')
            self.lineEdit_task_lasting.setText('{} min'.format(int(round((end-begin).total_seconds()/60,0))))
            self.textEdit_note.setText(self.task_widget.task_info[self.task_widget.current_task[0]][-1])
        else:
            self.lineEdit_current_task.setText('None')
            self.lineEdit_end.setText('None')
            self.lineEdit_task_lasting.setText('None')
            self.textEdit_note.setText('None')

    def init_task_table(self):
        task_labels = []
        task_notes = []
        begins = []
        ends = []
        dates = []
        for i in range(self.spinBox_task_number.value()):
            task_labels.append('Task {}'.format(i+1))
            task_notes.append('Notes for Task {}'.format(i+1))
            begins.append('08:00')
            ends.append('12:00')
            dates.append('2021-05-23')
        df = pd.DataFrame({'task_label':task_labels,'begin_time':begins,'end_time':ends, 'date':dates, 'note':task_notes})
        self.pandas_model = PandasModel(data = pd.DataFrame(df), tableviewer = self.tableView_task, main_gui = self)
        self.tableView_task.setModel(self.pandas_model)
        self.tableView_task.resizeColumnsToContents()
        self.tableView_task.setSelectionBehavior(PyQt5.QtWidgets.QAbstractItemView.SelectRows)

    def save_task_table(self):
        daily = self.checkBox_daily.isChecked()
        lines = []
        if daily:
            file = 'task_file_daily_{}'.format(self.lineEdit_suffix.text())
        else:
            self.lineEdit_suffix.setText(self.pandas_model._data.loc[0]['date'])
            file = 'task_file_{}'.format(self.lineEdit_suffix.text())
        with open(os.path.join(script_path,'task_files',file),'w') as f:
            for i in range(len(self.pandas_model._data.index)):
                lines.append("{}+['{}','{}','{}']".format(*([f"Task {i+1}"]+self.pandas_model._data.loc[i][['begin_time','end_time','note']].tolist())))
            f.write('\n'.join(lines))
        self.load_task_files()

    def init_task_file(self):
        now = datetime.datetime.now()
        date = now.strftime("%Y-%m-%d")
        files = os.listdir(os.path.join(script_path,'task_files'))
        file = None
        for each in files:
            if each.endswith(date):
                file = each
                break
            else:
                pass
        if file == None:
            file = 'task_file_daily_default'
        self.comboBox_task_files.setCurrentText(file)
        self.set_task_file()

    def formate_task_info_from_pandas_model(self):
        raw_data = self.pandas_model2._data.to_dict('split')
        format_data = {}
        for i in range(len(raw_data['index'])):
            label, *items = raw_data['data'][i]
            format_data[label] = items
        return format_data

    def set_task_file(self):
        file = os.path.join(script_path, 'task_files', self.comboBox_task_files.currentText())
        with open(file,'r') as f:
            lines = f.readlines()
            task_info = {}
            task_details = {'task_label':[],'begin_time':[],'end_time':[],'note':[]}
            for each in lines:
                _label, _info = each.rstrip().rsplit('+')
                _info = eval(_info)
                task_info[_label] = _info
                task_details['task_label'].append(_label)
                task_details['begin_time'].append(_info[0])
                task_details['end_time'].append(_info[1])
                task_details['note'].append(_info[2])
            self.pandas_model2 = PandasModel(data = pd.DataFrame(task_details), tableviewer = self.tableView_task_details, main_gui = self)
            self.tableView_task_details.setModel(self.pandas_model2)
            self.tableView_task_details.resizeColumnsToContents()
            self.tableView_task_details.setSelectionBehavior(PyQt5.QtWidgets.QAbstractItemView.SelectRows)
                
            self.task_widget.update_task_info(task_info)
            # self.timer_update_time.stop()
            # time.sleep(0.5)
            # self.timer_update_time.start(1000)

if __name__ == "__main__":
    QApplication.setStyle("windows")
    app = QApplication(sys.argv)
    #get dpi info: dots per inch
    screen = app.screens()[0]
    dpi = screen.physicalDotsPerInch()
    myWin = MyMainWindow()
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    myWin.show()
    sys.exit(app.exec_())
