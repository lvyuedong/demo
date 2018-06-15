# -*- coding: utf-8 -*-
__author__ = 'lvyuedong'

import os,sys
import traceback

import kUtility as ku
reload(ku)

from PyQt4.QtGui import QWidget, QColor
from PyQt4.QtCore import pyqtSignal, QThread

import ui_frustumSelection
reload(ui_frustumSelection)
from ui_frustumSelection import Ui_FrustumSelectionWidget

class SubProcess(QThread):
    # run the core function in a seperate thread
    updated = pyqtSignal(str, QColor)
    progress = pyqtSignal(float)
    success = pyqtSignal()
    fail = pyqtSignal()
    prune_list_signal = pyqtSignal(list)
    
    def __init__(self, func_select=0, main_ui=None):
        QThread.__init__(self)
        self.main_ui = main_ui
        self.isInterrupted = False
        self.text_color = QColor(166, 166, 166)
        self.error_color = QColor(255, 0, 0)
        self.green_color = QColor(0, 255, 0)
        self.yellow_color = QColor(255, 255, 0)
        self.func_dict = {0:self.createFrustumNode, 1:self.selectLowerSceneGraphLocations}
        self.function = self.func_dict[func_select]
    
    def interruption(self):
        self.isInterrupted = True
        
    def createFrustumNode(self):
        # get parameters from main UI
        node_type = str(self.main_ui.nodeTypeCombo.currentText())
        filter_type = str(self.main_ui.filterTypeCombo.currentText())
        fov_h = self.main_ui.fovH.value()
        fov_v = self.main_ui.fovV.value()
        near = self.main_ui.nearClipping.value()
        far = self.main_ui.farClipping.value()
        step = self.main_ui.step.value()
        is_animation = self.main_ui.cameraAnimCheck.isChecked()
        
        prune_list = None
        for i in ku.frustumSelectionIterator(filter_type=filter_type, fov_extend_h=fov_h, \
                                             fov_extend_v=fov_v, nearD=near, farD=far, \
                                             step=step, animation=is_animation):
            if self.isInterrupted:
                break
            if isinstance(i, float):
                # progress info
                self.progress.emit(i)
            elif isinstance(i, str):
                # general info or error
                if i.lower().startswith('error'):
                    self.updated.emit(i, self.error_color)
                else:
                    self.updated.emit(i, self.text_color)
            elif isinstance(i, list):
                # the returned list
                prune_list = i
                break
        
        if self.isInterrupted:
            self.updated.emit('User interrupted!', self.error_color)
            self.fail.emit()
            return
        
        if prune_list:
            self.prune_list_signal.emit(prune_list)
            self.success.emit()
        else:
            self.updated.emit('There is nothing under selected location should be pruned', self.yellow_color)
            self.success.emit()
            
    def selectLowerSceneGraphLocations(self):
        w = self.main_ui.width.value()
        h = self.main_ui.height.value()
        d = self.main_ui.depth.value()
        if not ku.selectSceneGraphByBound(maxWidth=w, maxHeight=h, maxDepth=d):
            self.updated.emit('Error: Please select a location in scene graph to proceed!', self.error_color)
            self.fail.emit()
            return
        self.progress.emit(100.0)
        self.updated.emit('Selection is done!', self.green_color)
        self.success.emit()
        
    def run(self):
        try:
            self.function()
        except:
            self.updated.emit(traceback.format_exc(), self.error_color)
            self.fail.emit()
            

class FrustumSelectionUI(QWidget, Ui_FrustumSelectionWidget):
    
    def __init__(self):
        QWidget.__init__(self)
        # set up the user interface from designer
        self.setupUi(self)
        self.text_color = QColor(166, 166, 166)
        self.error_color = QColor(255, 0, 0)
        self.green_color = QColor(0, 255, 0)
        self.yellow_color = QColor(255, 255, 0)
        # connect up the buttons
        self.createButton.clicked.connect(self.core, 0)
        self.selectButton.clicked.connect(self.core, 1)
        self.do_button = None
        self.stop_button = None
        
    def funcSelect(self, func_select):
        if func_select == 0:
            self.do_button = self.createButton
            self.stop_button = self.cancelButton_1
        elif func_select == 1:
            self.do_button = self.selectButton
            self.stop_button = self.cancelButton_2
            
    def core(self, func_select):
        self.funcSelect(func_select)
        self.helpText.clear()
        self.thread = SubProcess(func_select, self)
        self.thread.updated.connect(self.updatedHelpText)
        self.thread.progress.connect(self.updateProgressBar)
        self.thread.prune_list_signal.connect(self.createFrustumNode)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.restoreButtonStat)
        self.do_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.stop_button.clicked.connect(self.thread.interruption)
        self.stop_button.clicked.connect(self.disableCancelButton)
        self.stop_button.clicked.connect(self.exitCountDown)
        self.thread.start()
        
    def updatedHelpText(self, txt, color):
        self.helpText.setTextColor(color)
        self.helpText.append(txt)
        
    def updateProgressBar(self, progress):
        self.progressBar.setValue(int(progress))
        
    def exitCountDown(self):
        # wait for 5 seconds to exit the thread.
        # if time out, we will terminate the thread forcely.
        # Qthread.wait will return False if time out
        if not self.thread.wait(msecs=5000):
            self.thread.terminate()
            self.restoreButtonStat()
            
    def restoreButtonStat(self):
        self.do_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
    def disableCancelButton(self):
        self.stop_button.setEnabled(False)
        
    def createFrustumNode(self, prune_list):
        '''the createFrustumNode function used getNodeGraphView().getPointAdjustedToGroupNodeSpace
        functionn, this function can't be used in seperate thread, that's the reason we create
        prune node here
        '''
        if prune_list:
            ku.createFrustumNode(prune_list=prune_list)
            self.updatedHelpText('Prune node is created!', self.green_color)

'''
# generate ui_*.py file from *.ui
import PyQt4
uifile = 'frustumSelection.ui'
pyfile = 'ui_frustumSelection.py'
pyfile_obj = open(pyfile, mode='w')
PyQt4.uic.compileUi(uifile, pyfile_obj)
pyfile_obj.close()
'''
