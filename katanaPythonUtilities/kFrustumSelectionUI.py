# -*- coding: utf-8 -*-
__author__ = 'lvyuedong'

import os,sys
import traceback

import kUtility as ku
reload(ku)

from PyQt4.QtGui import QWidget, QColor
from PyQt4.QtCore import pyqtSignal

import ui_frustumSelection
reload(ui_frustumSelection)
from ui_frustumSelection import Ui_FrustumSelectionWidget

class FrustumSelectionUI(QWidget, Ui_FrustumSelectionWidget):
    progress_sgnl = pyqtSignal(int)
    helpline_sgnl = pyqtSignal(str)
    
    def __init__(self):
        QWidget.__init__(self)
        # set up the user interface from designer
        self.setupUi(self)
        # connect up the buttons
        self.createButton.clicked.connect(self.createNode)
        self.selectButton.clicked.connect(self.selectLowerSceneGraphLocations)
        # connect signals
        self.progress_sgnl.connect(self.progressBar.setValue)
        self.helpline_sgnl.connect(self.helpText.append)
        # set default text color
        self.text_color = QColor(166, 166, 166)
        self.error_color = QColor(255, 0, 0)
        
    def createNode(self):
        node_type = str(self.nodeTypeCombo.currentText())
        filter_type = str(self.filterTypeCombo.currentText())
        fov_h = self.fovH.value()
        fov_v = self.fovV.value()
        near = self.nearClipping.value()
        far = self.farClipping.value()
        step = self.step.value()
        is_animation = self.cameraAnimCheck.isChecked()
        
        self.helpText.clear()
        progress_bar = 0
        prune_list = None
        for i in ku.frustumSelectionIterator(filter_type=filter_type, fov_extend_h=fov_h, \
                        fov_extend_v=fov_v, nearD=near, farD=far, \
                        step=step, animation=is_animation):
            if isinstance(i, list):
                prune_list = i
                break
            elif isinstance(i, str):
                if i.lower().startswith('error'):
                    self.helpText.setTextColor(self.error_color)
                self.helpline_sgnl.emit(i)
                self.helpText.setTextColor(self.text_color)
            else:
                progress_bar = i
                self.progress_sgnl.emit(i)
        if prune_list:
            ku.createFrustumNode(prune_list=prune_list)
            
    def selectLowerSceneGraphLocations(self):
        w = self.width.value()
        h = self.height.value()
        d = self.depth.value()
        if not ku.selectSceneGraphByBound(maxWidth=w, maxHeight=h, maxDepth=d):
            self.helpText.setTextColor(self.error_color)
            self.helpline_sgnl.emit('Error: Please select a location in scene graph to proceed!')
            self.helpText.setTextColor(self.text_color)

'''
# generate ui_*.py file from *.ui
import PyQt4
uifile = 'frustumSelection.ui'
pyfile = 'ui_frustumSelection.py'
pyfile_obj = open(pyfile, mode='w')
PyQt4.uic.compileUi(uifile, pyfile_obj)
pyfile_obj.close()
'''
