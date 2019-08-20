# -*- coding:utf-8 -*-
# 继承 QMainWindow，执行视频播放及采用探针进行定位
# Author: 18521500408@163.com
# Date: 2019/08/20

import cv2
import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QSlider, QFileDialog, QWidget, QMessageBox
from PyQt5.QtGui import QImage, QPixmap
import qdarkstyle
from Window import Ui_Window


class SelectFile(QMainWindow):
    """ 打开对话框，选择特定后缀名的文件
    """
    def __init__(self, suffix):
        QWidget.__init__(self)
        self.setWindowTitle('OpenFile')
        _data = suffix.split('|')
        _data = ['*.' + d for d in _data]
        self.filename, _ = QFileDialog.getOpenFileName(self, '选择文件', os.getcwd(), ';'.join(_data))


class VideoPlayer(QMainWindow, Ui_Window):
    def __init__(self, parent=None):
        super(VideoPlayer, self).__init__(parent)
        self.setupUi(self)
        self.init_speed()

        self.load_video.clicked.connect(self.play_video)
        self.pause.clicked.connect(self.pause_video)
        self.pause_flag = False
        self.save_image.clicked.connect(self.save)
        self.img4save = None   # 待保存的图像数据
        self.fps = 40          # 正常播放时帧间隔 40 毫秒

        self.load_feature_list.clicked.connect(self.init_list)

        self.skip_pos = 0           # 点击feature list之后，需要跳转至的图像位置

    def init_slider(self, max_value):
        """ 初始化图像播放进度的滑动条
        :param max_value: 最大值
        :return: None
        """
        self.slider.setMinimum(0)
        self.slider.setMaximum(max_value)
        self.slider.setSingleStep(1)
        self.slider.setValue(0)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(5)
        self.slider.valueChanged.connect(self.nothing)

    def init_list(self):
        """ 读取存储节点位置的文件，写入list控件
        """
        sf = SelectFile('txt|csv')
        _file = sf.filename
        if not os.path.isfile(_file):
            return

        # 重新加载item list的时候需要首先清空列表，否则会出现 append 的现象
        self.feature_list.clear()
        try:
            with open(_file, "r", encoding="utf-8") as fh:
                line = fh.readline().strip()
                while line:
                    self.feature_list.addItem(line)
                    line = fh.readline().strip()
        except Exception as e:
            print("error: %s, when open file %s" % (e, _file))
            QMessageBox.warning(self,
                                "文件打开错误", "读取文件 %s 失败！\r\n\r\n请将此文件的编码格式转换为UTF-8格式！" % _file,
                                QMessageBox.Yes)

        self.feature_list.verticalScrollBar().valueChanged.connect(lambda: print("scroll"))

        # 单击触发绑定的槽函数
        self.feature_list.itemClicked.connect(self.list_clicked)

    def list_clicked(self, item):
        """ 单击选择需要查看的feature
        :param item: combobox 列表的index
        :return: None
        """
        _frame_idx = item.text().split(",")[0]
        try:
            self.skip_pos = int(_frame_idx)
        except Exception as e:
            print(e)
        print(self.skip_pos)

    def init_speed(self):
        """ 初始化视频播放的倍速设置
        :return: None
        """
        self.speed.clear()
        self.speed.insertItems(0, ['1', '0.5', '1.25', '2', '5', '10', '20'])

        self.speed.activated[str].connect(self.flush_speed)

    def flush_speed(self):
        """ 刷新视频播放速度
        :return:  None
        """
        _com_idx = self.speed.currentIndex()
        multi = self.speed.itemText(_com_idx)
        self.fps = int(40/float(multi))

    def save(self):
        """ 保存当前界面内的图象数据
        :return: None
        """
        filename, _ = QFileDialog.getSaveFileName(self, "保存图片", os.getcwd(),
                                                  "JPG Files (*.jpg);;BMP Files (*.bmp);;PNG Files (*.png)")

        if filename == "":
            print("\n取消保存")
            return

        cv2.imwrite(filename, self.img4save)

    def pause_video(self):
        """  关联 暂停|开始播放 按钮
        :return: None
        """
        if self.pause_flag:
            self.pause.setText("暂停播放")
            self.pause_flag = False
        else:
            self.pause.setText("开始播放")
            self.pause_flag = True
        print(self.pause_flag)

    @staticmethod
    def nothing(emp):
        """ do nothing """
        pass

    def play_video(self):
        """ 播放视频并使用视频探针进行定位
        :return: None
        """
        # 打开对话框选择视频文件
        sf = SelectFile('avi|mp4|mov')
        video = sf.filename

        cap = cv2.VideoCapture(video)
        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        self.init_slider(frames)

        loop_flag = 0
        pos = 0

        while True:
            if loop_flag == pos:
                loop_flag = loop_flag + 1
                self.slider.setValue(loop_flag)
            else:
                pos = self.slider.value()
                loop_flag = pos
                cap.set(cv2.CAP_PROP_POS_FRAMES, pos)

            ret, img = cap.read()

            self.refresh(img)
            cv2.waitKey(self.fps)

            if loop_flag == frames:
                break

            if self.pause_flag:
                cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
                loop_flag = pos

            if self.skip_pos:
                cap.set(cv2.CAP_PROP_POS_FRAMES, self.skip_pos)
                loop_flag = self.skip_pos
                pos = self.skip_pos
                self.skip_pos = 0

            if pos == frames - 1:
                pos = 1
                loop_flag = pos
                cap.set(cv2.CAP_PROP_POS_FRAMES, pos)

    def refresh(self, img):
        """ 在静态控件上展示图片
        :param img: 图像内容
        """
        try:
            height, width, channel = img.shape
            bytes_per_line = 3 * width
            qt_img = QImage(img.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            self.label.setPixmap(QPixmap.fromImage(qt_img))
            self.label.setScaledContents(True)
            self.img4save = img
        except Exception as e:
            print(e)

    def closeEvent(self, QCloseEvent):
        print("close window")
        sys.exit(0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # 加载蓝黑色背景
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    ui = VideoPlayer()
    ui.show()
    sys.exit(app.exec_())
