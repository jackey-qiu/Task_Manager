from PyQt5 import QtCore
from PyQt5.QtWidgets import QCheckBox, QRadioButton, QDialog, QTableWidgetItem, QHeaderView, QAbstractItemView, QInputDialog, QDialog,QShortcut
from PyQt5.QtCore import Qt, QTimer, QEventLoop, QThread
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
import sys,os
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

    def set_time_label(self):
        now = datetime.datetime.now()
        time_ = now.strftime("%H:%M:%S")
        year = now.year
        month = now.month
        day = now.day
        weekday = now.weekday()
        weekday_map = {0:'Monday',1:'Tuesday',2:'Wednesday',3:'Thursday',4:'Friday',5:'Saturday',6:'Sunday'}
        self.label_date.setText('{}-{}-{}, {}'.format(year, month, day, weekday_map[weekday]))
        self.label_time.setText(time_)
        self.task_widget.update()
        self.lineEdit_current_task.setText(self.task_widget.current_task[0])
        self.lineEdit_end.setText(self.task_widget.task_info[self.task_widget.current_task[0]][1])

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
        df = pd.DataFrame({'task_labels':task_labels,'begin_time':begins,'end_time':ends, 'date':dates, 'note':task_notes})
        self.pandas_model = PandasModel(data = pd.DataFrame(df), tableviewer = self.tableView_task, main_gui = self)
        self.tableView_task.setModel(self.pandas_model)
        self.tableView_task.resizeColumnsToContents()
        self.tableView_task.setSelectionBehavior(PyQt5.QtWidgets.QAbstractItemView.SelectRows)

if __name__ == "__main__":
    QApplication.setStyle("windows")
    app = QApplication(sys.argv)
    #get dpi info: dots per inch
    screen = app.screens()[0]
    dpi = screen.physicalDotsPerInch()
    myWin = MyMainWindow()
    #app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    myWin.show()
    sys.exit(app.exec_())
