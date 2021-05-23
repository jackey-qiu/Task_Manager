from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QBrush, QFont, QPen
from PyQt5.QtCore import Qt, QTimer
import sys
import numpy as np
import time
from datetime import datetime

class task_widget(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        #number of total channels in MVP
        self.task_info = {'Task 1':['08:00','09:30','05-23-2021'],'Task 2':['09:40','12:50','05-23-2021'],'Task 3':['12:50','22:00','05-23-2021'],'Task 4':['22:00','23:50','05-23-2021']}
        self.block_info = {}
        self.task_block_width = self.width()*0.7
        self.task_indicator_width = 2
        self.padding_left_right_top_bottom = [10,10,10,10]

    def get_total_time_in_seconds(self):
        keys = sorted(self.task_info.keys())
        begin = datetime.strptime(self.task_info[keys[0]][0], '%H:%M')
        end = datetime.strptime(self.task_info[keys[-1]][1], '%H:%M')
        return (end - begin).total_seconds()

    def transform_task_time_to_task_block_dim(self, task_name = 'Task 1'):
        task_time_total = self.get_total_time_in_seconds()
        current_task_time = (datetime.strptime(self.task_info[task_name][1], '%H:%M') - datetime.strptime(self.task_info[task_name][0], '%H:%M')).total_seconds()
        height = (self.height()-sum(self.padding_left_right_top_bottom[2:]))*(current_task_time/task_time_total)
        return height

    def get_all_task_blocks(self):
        keys = sorted(self.task_info.keys())
        self.task_names_sorted = list(keys)
        heights = []
        #rects = []
        for key in keys:
            heights.append(self.transform_task_time_to_task_block_dim(key))
        for i in range(len(keys)):
            if i == 0:
                pos = [10,self.padding_left_right_top_bottom[-2]]
            else:
                pos = [10,self.padding_left_right_top_bottom[-2]+sum(heights[0:i])]
            dim = [self.task_block_width, heights[i]]
            #rects.append(pos + dim)
            self.block_info[keys[i]] = pos + dim

    def get_actived_task(self):
        time_now = datetime.strptime(f"{datetime.now().hour}:{datetime.now().minute}",'%H:%M')
        for each in self.task_info:
            begin = datetime.strptime(self.task_info[each][0], '%H:%M')
            end = datetime.strptime(self.task_info[each][1], '%H:%M')
            if ((time_now - begin).total_seconds()>=0) and ((time_now - end).total_seconds()<0):
                percent = (time_now - begin).total_seconds()/(end-begin).total_seconds()
                self.current_task = [each, percent]
                return each, percent
            else:
                pass
        
    def paintEvent(self, e):
        # self.clear()
        qp = QPainter()
        qp.begin(self)
        self.get_all_task_blocks()
        current_task, rate = self.get_actived_task()
        for each in self.block_info:
            if each==current_task:
                self.draw_task_block(qp,task_label = each, color = [250,0,0], block_pos = self.block_info[each],time_begin = self.task_info[each][0], extra_marker = rate)
            else:
                self.draw_task_block(qp,task_label = each, color = [0,0,250], block_pos = self.block_info[each],time_begin = self.task_info[each][0])
        qp.end()

    def draw_markers(self,qp,rect,which_side = 'left',total_volume_in_ml = 12.5, marker_pos_in_ml = [2,4,6,8,10,12]):
        if which_side in ['left','right']:
            marker_length = rect[2]*0.1
        else:
            marker_length = rect[3]*0.1
        marker_pos_in_pix = []
        for each in marker_pos_in_ml:
            marker_pos_in_pix.append([rect[0],(each/total_volume_in_ml)*rect[3]+rect[1],rect[0]+marker_length,(each/total_volume_in_ml)*rect[3]+rect[1]])
        for each in marker_pos_in_pix:
            qp.drawLine(*each)
            qp.drawText(each[2],each[3],"{} ml".format(marker_pos_in_ml[marker_pos_in_pix.index(each)]))

    def draw_task_block(self, qp, task_label = 'Task 1', color = [0,0,250], block_pos = [10,20,30,40], time_begin = '', extra_marker = None):
        col = QColor(0, 0, 0)
        col.setNamedColor('#d4d4d4')
        qp.setPen(col)
        qp.setBrush(QColor(*color))
        qp.drawRect(*(block_pos))
        qp.setPen(QPen(QColor(250, 250, 250), 1, Qt.SolidLine, Qt.FlatCap, Qt.MiterJoin))
        #qp.setPen(col)
        qp.setFont(QFont("Arial", 14))
        qp.drawText(block_pos[0]+10,block_pos[1]+block_pos[-1]/2,task_label)
        qp.setPen(QPen(QColor(0, 0, 0), 1, Qt.SolidLine, Qt.FlatCap, Qt.MiterJoin))
        qp.drawText(block_pos[0]+5+block_pos[-2],block_pos[1],time_begin)
        if extra_marker!=None:
            qp.setPen(QPen(QColor(0, 250, 0), 2, Qt.SolidLine, Qt.FlatCap, Qt.MiterJoin))
            qp.drawLine(*[block_pos[0],block_pos[1]+block_pos[-1]*extra_marker,block_pos[0]+block_pos[2],block_pos[1]+block_pos[-1]*extra_marker])
            qp.setPen(QPen(QColor(0, 250, 0), 5, Qt.SolidLine, Qt.FlatCap, Qt.MiterJoin))
            qp.drawLine(*[block_pos[0],block_pos[1]+block_pos[-1]*extra_marker,block_pos[0],self.padding_left_right_top_bottom[-2]])
            qp.setPen(QPen(QColor(250, 0, 250), 2, Qt.SolidLine, Qt.FlatCap, Qt.MiterJoin))
            qp.drawText(block_pos[0]+block_pos[2]+5,block_pos[1]+block_pos[-1]*extra_marker,'Now')
