#!/bin/env python3

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QPoint, QRect
from PIL.ImageQt import ImageQt
import signal

import decode

import functools

@functools.lru_cache(maxsize=30)
def getPixmap(z):
    try:
        image = ImageQt('0'+str(int(z))+'.webp')
    except FileNotFoundError:
        image = QImage(400, 400, QImage.Format_RGB888)

    return QPixmap.fromImage(image), image

class ImageLabel(QLabel):
    def __init__(self, pos, parent=None):
        super(ImageLabel, self).__init__(parent)
        self.setMouseTracking(True)
        self.set_pos(pos)

    def set_pos(self,pos):
        self.pos = pos
        self.offset = QPoint(200,200) - QPoint(int(pos[0]), int(pos[1]))
        self.update()


    def paintEvent(self, event):
        painter = QPainter(self)
        self.draw_background(painter)
        pen = QPen(QColor(255, 0, 0), 3)
        painter.setPen(pen)
        qpos = QPoint(int(self.pos[0]), int(self.pos[1]))+self.offset 
        painter.drawLine(qpos - QPoint(10, 0), qpos + QPoint(10, 0))
        painter.drawLine(qpos - QPoint(0, 10), qpos + QPoint(0, 10))
        str = f"""
X: {self.pos[0]}
Y: {self.pos[1]}
Z: {self.pos[2]}
        """
        if hasattr(self, 'overlay_text'):
            str += self.overlay_text()
        painter.drawText(QRect(0,0, 300,300), Qt.AlignLeft, str)


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() # - self.frameGeometry().topLeft()
            event.accept()

    # Print data of clicks in CSV format ready to put in a spreadsheet
    def mouseClickEvent(self, event):
        print(str = f"""
{self.pos[0]}, {self.pos[1]}, {self.pos[2]}
        """)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.offset += (event.globalPos() - self.drag_position)
            self.drag_position = event.globalPos()
            event.accept()

        pos = event.pos() - self.offset
        self.pos = (pos.x(), pos.y(), self.pos[2])
        if hasattr(self, 'onpositionchanged'):
            self.onpositionchanged(self.pos)

        self.update()

    def wheelEvent(self,event):
        self.pos = (self.pos[0], self.pos[1], (self.pos[2]+event.angleDelta().y()/120))
        self.update();

class InputImageLabel(ImageLabel):
    def __init__(self, z, parent=None):
        super(InputImageLabel, self).__init__(z, parent)

    def draw_background(self, painter):
        pixmap, img = getPixmap(int(self.pos[2]));

        painter.drawPixmap(self.offset.x(), self.offset.y(), pixmap)

class OutputImageLabel(ImageLabel):
    def __init__(self, z, parent=None):
        super(OutputImageLabel, self).__init__(z, parent)
        self.cache = dict()    # beware, this cache grows without bound.

    def overlay_text(self):
        other_pos = decode.translate_position(self.pos)
        return f"""Input coords:
X: {other_pos[0]}
Y: {other_pos[1]}
Z: {other_pos[2]}
        """

    def get_tile(self, pos, cached_only = False):
        if pos in self.cache:
            return self.cache[pos], False
        if cached_only:
            return None, True
        img = self.imagesource(pos)
        self.cache[pos] = (img, QPixmap.fromImage(img))
        return self.cache[pos], True

    def draw_background(self, painter):
        # goal is we gradually process and draw image tiles, and cache any drawn ones.
        positions = [ (x,y) for x in range(-1, 1) for y in range(-1, 1) ]

        positions.sort(key = lambda x: x[0]**2 + x[1]**2)
        
        base_pos = (int(self.pos[0]/100)*100, int(self.pos[1]/100)*100, int(self.pos[2]))
        done_one_uncached = False
        for a in positions:
            
            tile_pos = (base_pos[0] + a[0]*100, base_pos[1] + a[1]*100, base_pos[2])
            img, done_one_uncached = self.get_tile(tile_pos, done_one_uncached)
            if img:
                painter.drawPixmap(self.offset.x()+tile_pos[0], self.offset.y()+tile_pos[1], img[1])


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(500, 500)

        self.initUI()

    def initUI(self):
        vbox = QVBoxLayout()

        hbox = QHBoxLayout()
        


        img_label1 = InputImageLabel((0,0,5102))
        img_label2 = OutputImageLabel((0,0,0))
        self.outputLabel = img_label2
        img_label2.onpositionchanged = lambda pos: img_label1.set_pos(decode.translate_position(pos))

        img_label2.imagesource = lambda pos: decode.flatten(pos)


        hbox.addWidget(img_label1)
        hbox.addWidget(img_label2)

        vbox.addLayout(hbox)

        train_button = QPushButton('Train network more!', self)
        train_button.clicked.connect(self.train)
        vbox.addWidget(train_button)

        self.setLayout(vbox)

        self.setWindowTitle('Layered image browser')
        self.show()

    def train(self):
        decode.train()

        # clear out cached tiles.
        self.outputLabel.cache = dict()
        
        self.outputLabel.update()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.exit(app.exec_())