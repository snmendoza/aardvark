# -*- coding: utf-8 -*-

# This file is part of Argos.
# 
# Argos is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Argos is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Argos. If not, see <http://www.gnu.org/licenses/>.

""" Some simple Config Tree Items
"""
import logging
import numpy as np

from .basecti import BaseCti, CtiEditor, InvalidInputError
from libargos.qt import Qt, QtCore, QtGui, getQApplicationInstance
from libargos.utils.misc import NOT_SPECIFIED


logger = logging.getLogger(__name__)

# Use setIndexWidget()?
        
# TODO: QCompleter? See demos/spreadsheet/spreadsheetdelegate.py
# TODO: FloatCti using QDoubleSpinBox
# TODO: Nullable bool with tri-state checkbox
# TODO: Date selector.
# TODO: Color selector (transparency) 
# TODO: Font selector?
# TODO: None takes data of parent


class StringCti(BaseCti):
    """ Config Tree Item to store a string. It can be edited with a QLineEdit.
        The string can have an optional maximum length.

    """
    def __init__(self, nodeName, data=NOT_SPECIFIED, defaultData='', 
                 maxLength=None):
        """ Constructor. 
        
            :param maxLength: maximum length of the string
            
            For the (other) parameters see the BaseCti constructor documentation.
        """
        super(StringCti, self).__init__(nodeName, data=data, defaultData=defaultData)
        
        # We could define a mask here as well but since that very likely will be rarely used, 
        # we don't want to store it for each cti. You can make a subclass if you need it. 
        self.maxLength = maxLength


    def _enforceDataType(self, data):
        """ Converts to str so that this CTI always stores that type. 
        """
        return str(data)    
        
    
    @property
    def debugInfo(self):
        """ Returns the string with debugging information
        """
        return "maxLength = {}".format(self.maxLength)
    
    
    def createEditor(self, delegate, parent, _option):
        """ Creates a QSpinBox for editing. 
            :type option: QStyleOptionViewItem        
        """
        editor = QtGui.QLineEdit(parent)
        if self.maxLength is not None:
            editor.setMaxLength(self.maxLength)
        return editor
        
        
    def setEditorValue(self, editor, data):
        """ Provides the editor widget with a data to manipulate.
        """
        lineEditor = editor
        lineEditor.setText(data)
        
        
    def getEditorValue(self, editor):
        """ Gets data from the editor widget.
        """
        lineEditor = editor
        return lineEditor.text()



class IntegerCti(BaseCti):
    """ Config Tree Item to store an integer. It can be edited using a QSinBox.
    """
    def __init__(self, nodeName, data=NOT_SPECIFIED, defaultData=0, 
                 minValue = None, maxValue = None, stepSize = 1):
        """ Constructor
            
            :param minValue: minimum data allowed when editing (use None for no minimum)
            :param maxValue: maximum data allowed when editing (use None for no maximum)
            :param stepSize: steps between values when ediging (default = 1)
                    
            For the (other) parameters see the BaseCti constructor documentation.
        """
        super(IntegerCti, self).__init__(nodeName, data=data, defaultData=defaultData)
        
        self.minValue = minValue
        self.maxValue = maxValue
        self.stepSize = stepSize

    
    def _enforceDataType(self, data):
        """ Converts to int so that this CTI always stores that type. 
        """
        return int(data)
        
    
    @property
    def debugInfo(self):
        """ Returns the string with debugging information
        """
        return "min = {}, max = {}, step = {}".format(self.minValue, self.maxValue, self.stepSize)
    
    
    def createEditor(self, delegate, parent, _option):
        """ Creates a QSpinBox for editing. 
            :type option: QStyleOptionViewItem
        """
        spinBox = QtGui.QSpinBox(parent)

        if self.minValue is None:
            spinBox.setMinimum(np.iinfo('i').min)
        else: 
            spinBox.setMinimum(self.minValue) 

        if self.maxValue is None:
            spinBox.setMaximum(np.iinfo('i').max)
        else: 
            spinBox.setMaximum(self.maxValue) 

        spinBox.setSingleStep(self.stepSize)
        return spinBox
        
        
    def setEditorValue(self, spinBox, data):
        """ Provides the spin box editor widget with a data to manipulate.
        """
        spinBox.setValue(data)
        
        
    def getEditorValue(self, spinBox):
        """ Gets data from the spin box editor widget.
        """
        spinBox.interpretText()
        data = spinBox.value()
        return data

        

class BoolCti(BaseCti):
    """ Config Tree Item to store an integer. It can be edited using a QSpinBox.
    """
    def __init__(self, nodeName, data=NOT_SPECIFIED, defaultData=False):
        """ Constructor

            For the parameters see the BaseCti constructor documentation.
        """
        super(BoolCti, self).__init__(nodeName, data=data, defaultData=defaultData)

    
    def _enforceDataType(self, data):
        """ Converts to bool so that self.data always is of that type.
        """
        return bool(data)
        
        
    @property
    def displayValue(self):
        """ Returns empty string since a checkbox will displayed in the value column instead.  
        """
        return ""
   
    @property
    def valueColumnItemFlags(self):
        """ Returns Qt.ItemIsUserCheckable so that a check box will be drawn in the config tree.
            Note that the flags don't include Qt.ItemIsEditable to that createEditor will never
            be called. A checkbox is a special case regarding editing.
        """
        return Qt.ItemIsUserCheckable
        #return Qt.NoItemFlags
    

    @property
    def checkState(self):
        """ Returns how the checkbox for this cti should look like. Returns None for no checkbox. 
            :rtype: QtCheckState or None 
        """
        if self.data is True:
            return Qt.Checked
        elif self.data is False:
            return Qt.Unchecked
        elif self.data is None:
            return Qt.PartiallyChecked
        else:
            raise ValueError("Unexpected data: {!r}".format(self.data))

    @checkState.setter
    def checkState(self, checkState):
        """ Allows the data to be set given a Qt.CheckState.
        """
        if checkState == Qt.Checked:
            self.data = True
        elif checkState == Qt.Unchecked:
            self.data = False
        elif checkState is Qt.PartiallyChecked:
            self.data = None
        else:
            raise ValueError("Unexpected check state: {!r}".format(checkState))

    
    def createEditor(self, delegate, parent, _option):
        """ Creates a QCheckBox for editing. 
            :type option: QStyleOptionViewItem        
        """
        checkBox = QtGui.QCheckBox(parent)
        checkBox.setAutoFillBackground(True)
        checkBox.setFocusPolicy(Qt.StrongFocus) # See QAbstractItemDelegate.createEditor docs
        checkBox.clicked.connect(delegate.commitAndCloseEditor)
        return checkBox

        
    def setEditorValue(self, checkBox, data):
        """ Provides the check box editor widget with a data to manipulate.
        """
        checkBox.setChecked(data)
        
        
    def getEditorValue(self, checkBox):
        """ Gets data from the check box editor widget.
        """
        return checkBox.isChecked()

        
    def __paintDisplayValue(self, painter, option, data):
        """ Paints a check box on the painter.
        """
        checkBox = QtGui.QStyleOptionButton()
        
        checkBox.state = QtGui.QStyle.State_Enabled
        checkBox.rect = option.rect
        
        if data:
            checkBox.state = QtGui.QStyle.State_On | QtGui.QStyle.State_Enabled
        else:
            checkBox.state = QtGui.QStyle.State_Off | QtGui.QStyle.State_Enabled

        qApp = getQApplicationInstance()
        qApp.style().drawControl(QtGui.QStyle.CE_CheckBox, checkBox, painter)
        return True
    
                

class ChoiceCti(BaseCti):
    """ Config Tree Item to store a choice between strings.
    """
    def __init__(self, nodeName, data=NOT_SPECIFIED, defaultData=0, choices=None):
        """ Constructor
            data and defaultData are used to store the currentIndex.
            choices must be a list of string.
                    
            For the (other) parameters see the BaseCti constructor documentation.
        """
        super(ChoiceCti, self).__init__(nodeName, data=data, defaultData=defaultData)
        self.choices = [] if choices is None else choices
        
    
    def _enforceDataType(self, data):
        """ Converts to int so that this CTI always stores that type. 
        """
        return int(data)

    
    @property
    def displayValue(self):
        """ Returns the string representation of data for use in the tree view. 
        """
        return str(self.choices[self.data])
    
    
    @property
    def debugInfo(self):
        """ Returns the string with debugging information
        """
        return repr(self.choices)
    
    
    def createEditor(self, delegate, parent, _option):
        """ Creates a QComboBox for editing. 
            :type option: QStyleOptionViewItem
        """
        comboBox = QtGui.QComboBox()
        comboBox.addItems(self.choices)
        
        ctiEditor = CtiEditor(self, delegate, comboBox, parent=parent) 

        comboBox.activated.connect(ctiEditor.commitAndClose)        
        return ctiEditor
        
    
    def finalizeEditor(self, ctiEditor, delegate):
        """ Is called when the editor is closed. Disconnect signals.
        """
        comboBox = ctiEditor.mainEditor
        comboBox.activated.disconnect(ctiEditor.commitAndClose)      
        
        
    def setEditorValue(self, ctiEditor, index):
        """ Provides the combo box an data that is the current index.
        """
        comboBox = ctiEditor.mainEditor
        comboBox.setCurrentIndex(index)        
        
        
    def getEditorValue(self, ctiEditor):
        """ Gets data from the combo box editor widget.
        """
        comboBox = ctiEditor.mainEditor
        data = comboBox.currentIndex()
        return data
                


class ColorCti(BaseCti):
    """ Config Tree Item to store a color. 
    """
    def __init__(self, nodeName, data=NOT_SPECIFIED, defaultData=''):
        """ Constructor. 
            For the (other) parameters see the BaseCti constructor documentation.
        """
        super(ColorCti, self).__init__(nodeName, data=data, defaultData=defaultData)
        

    def _enforceDataType(self, data):
        """ Converts to str so that this CTI always stores that type. 
        """
        qColor = QtGui.QColor(data)    # TODO: store a RGB string?
        if not qColor.isValid():
            raise ValueError("Invalid color specification: {!r}".format(data))
        return qColor
        
        
    def _dataToJson(self, qColor):
        """ Converts data or defaultData to serializable json dictionary or scalar.
            Helper function that can be overridden; by default the input is returned.
        """
        return qColor.name()
    
    def _dataFromJson(self, json):
        """ Converts json dictionary or scalar to an object to use in self.data or defaultData.
            Helper function that can be overridden; by default the input is returned.
        """
        return QtGui.QColor(json) 

    
    @property
    def displayValue(self):
        """ Returns a string with the RGB value in hexadecimal (e.g. '#00FF88') 
        """
        return self._data.name().upper()    
        
    
    @property
    def debugInfo(self):
        """ Returns the string with debugging information
        """
        return ""
    
    
    def createEditor(self, delegate, parent, _option):
        """ Creates a QSpinBox for editing. 
            :type option: QStyleOptionViewItem
        """
        lineEditor = QtGui.QLineEdit(parent)
        regExp = QtCore.QRegExp(r'#?[0-9A-F]{6}', Qt.CaseInsensitive)
        validator = QtGui.QRegExpValidator(regExp, parent=lineEditor)
        lineEditor.setValidator(validator)
            
        return lineEditor
        
        
    def setEditorValue(self, lineEditor, qColor):
        """ Provides the editor widget with a data to manipulate.
        """
        lineEditor.setText(qColor.name().upper())
        
        
    def getEditorValue(self, lineEditor):
        """ Gets data from the editor widget.
        """
        text = lineEditor.text()
        if not text.startswith('#'):
            text = '#' + text

        validator = lineEditor.validator()
        if validator is not None:
            state, text, _ = validator.validate(text, 0)
            if state != QtGui.QValidator.Acceptable:
                raise InvalidInputError("Invalid input: {!r}".format(text))

        return text
    


                