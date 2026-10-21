# -*- coding: utf-8 -*-
# from PySide6.QtCore import Qt

import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt


class Graph(pg.GraphItem):
    def __init__(self):
        self.dragPoint = None
        self.dragOffset = None
        pg.GraphItem.__init__(self)

    def setData(self, **kwds):
        self.data = kwds
        if 'pos' in self.data:
            npts = self.data['pos'].shape[0]
            self.data['adj'] = np.array([[0, 1], [2, 3]], dtype=np.int32)
            self.data['data'] = np.empty(npts, dtype=[('index', int)])
            self.data['data']['index'] = np.arange(npts)
        self.updateGraph()

    def updateGraph(self):
        pg.GraphItem.setData(self, **self.data)

    def mouseDragEvent(self, ev):
        if ev.button() != Qt.MouseButton.LeftButton:
            ev.ignore()
            return
        if ev.isStart():
            pos_ev = ev.buttonDownPos()
            pts = self.scatter.pointsAt(pos_ev)
            if len(pts) == 0:
                ev.ignore()
                return
            self.dragPoint = pts[0]
            ind = pts[0].data()[0]
            self.dragOffset = self.data['pos'][ind] - pos_ev
        elif ev.isFinish():
            self.dragPoint = None
            return
        else:
            if self.dragPoint is None:
                return
            ind = self.dragPoint.data()[0]
            self.data['pos'][ind] = ev.pos() + self.dragOffset
            self.updateGraph()
        ev.accept()
