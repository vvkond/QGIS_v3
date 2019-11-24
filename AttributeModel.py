
# -*- coding: utf-8 -*-

from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.gui import QgsColorButton, QgsFieldExpressionWidget, QgsColorDialog
from .bblInit import *

#Table model for attribute TableView
class AttributeTableModel(QAbstractTableModel):
    ExpressionColumn = 0
    ColorColumn = 1
    ColorLineColumn = 2
    DescrColumn = 3
    FilterColumn = 4
    def __init__(self, headerData, parent=None, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self.arraydata = []
        self.headerdata = headerData

    def clearRows(self):
        self.beginResetModel()
        self.arraydata = []
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self.arraydata)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headerdata)

    def insertRows(self, row, count, parent = QModelIndex()):
        if row < 0:
            row = 0

        self.beginInsertRows(parent, row, count + row - 1)
        for i in range(0, count):
            newRow = ['', QColor(255, 0, 0), QColor(0, 0, 0), '', '']
            self.arraydata.insert(i + row, newRow)

        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent = QModelIndex()):
        self.beginRemoveRows(parent, row, row + count -1)
        for r in range(0, count):
            del self.arraydata[r + row]
        self.endRemoveRows()

        return True

    def data(self, index, role):
        if not index.isValid():
            return None

        r = index.row()
        c = index.column()
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return self.arraydata[r][c]
        elif role == Qt.DecorationRole and c == AttributeTableModel.ColorColumn:
            return self.arraydata[r][c]
        elif role == Qt.DecorationRole and c == AttributeTableModel.ColorLineColumn:
            return self.arraydata[r][c]

        return None

    def setDiagramm(self, row, value):
        if row >= 0 and row < len(self.arraydata):
            self.arraydata[row][self.getFilterColumn()] = value


    def diagramm(self, row):
        if row >= 0 and row < len(self.arraydata) and len(self.arraydata[row])>self.getFilterColumn():
            return self.arraydata[row][self.getFilterColumn()]
        else:
            return 'No Diag ' + str(row)

    def getFilterColumn(self):
        return AttributeTableModel.FilterColumn

    def setData(self, index, value, role):
        if not index.isValid():
            return False

        if role == Qt.EditRole:
            self.arraydata[index.row()][index.column()] = value
            return True

        return False

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headerdata[col]
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

        return flags

#Table model for Labels TableView
class AttributeLabelTableModel(AttributeTableModel):
    ShowZeroColumn = 2
    NewLineColumn = 3
    IsPercentColumn = 4
    FilterColumn = 5
    def __init__(self, headerData, parent=None):
        AttributeTableModel.__init__(self, headerData, parent)

    def getFilterColumn(self):
        return AttributeLabelTableModel.FilterColumn

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() > AttributeTableModel.ColorColumn:
            flags = flags | Qt.ItemIsUserCheckable
        else:
            flags = flags | Qt.ItemIsEditable

        return flags

    def data(self, index, role):
        if not index.isValid():
            return None

        if index.column() > AttributeTableModel.ColorColumn:
            if role == Qt.CheckStateRole:
                return self.arraydata[index.row()][index.column()]
            else:
                return None
        else:
            return AttributeTableModel.data(self, index, role)

    def setData(self, index, value, role):
        if not index.isValid():
            return False

        if role == Qt.CheckStateRole and index.column() > AttributeTableModel.ColorColumn:
            self.arraydata[index.row()][index.column()] = value
            return True
        else:
            return AttributeTableModel.setData(self, index, value, role)


    def insertRows(self, row, count, parent = QModelIndex()):
        if row < 0:
            row = 0

        self.beginInsertRows(parent, row, count + row - 1)
        for i in range(0, count):
            newRow = ['', QColor(0, 0, 0), Qt.Unchecked, Qt.Unchecked, Qt.Unchecked, '']
            self.arraydata.insert(i + row, newRow)

        self.endInsertRows()
        return True


#Filter table model
class AttributeFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        QSortFilterProxyModel.__init__(self, parent)
        self.filter = 0

    def setFilter(self, f):
        self.filter = f
        self.invalidateFilter()

    def filterAcceptsRow(self, sourceRow, sourceParent):
        index1 = self.sourceModel().index(sourceRow, 0, sourceParent)

        id = self.sourceModel().diagramm(index1.row())
        return self.filter == id


#Expression delegate
class ExpressionDelegate(QStyledItemDelegate):
    def __init__(self, layer, isDescr, parent=None):
        QStyledItemDelegate.__init__(self, parent)

        self.currentLayer = layer
        self.isDescription = isDescr

    def createEditor(self, parent, option, index):

        self.initStyleOption(option, index)

        fieldEx = QgsFieldExpressionWidget(parent)
        fieldEx.setLayer(self.currentLayer)
        fieldEx.setField(index.data())

        return fieldEx

    def updateEditorGeometry(self, editor, option, index):
        if editor:
            editor.setGeometry(option.rect)

    def setModelData(self, editor, model, index):
        text = editor.currentText()
        model.setData(index, text, Qt.EditRole)

        if self.isDescription:
            index1 = model.index(index.row(), AttributeTableModel.DescrColumn)
            descr = model.data(index1, Qt.DisplayRole)

            if not descr or len(descr) < 2:
                model.setData(index1, text, Qt.EditRole)
                model.dataChanged.emit(index1, index1)

#Color delegate
class ColorDelegate(QStyledItemDelegate):
    def __init__(self, layer, parent=None):
        QStyledItemDelegate.__init__(self, parent)

        self.currentLayer = layer
        self.newColor = QColor()

    def createEditor(self, parent, option, index):

        self.initStyleOption(option, index)

        self.newColor = QColor(index.data(Qt.DecorationRole))
        colorEd = QgsColorDialog(parent)
        colorEd.setColor(self.newColor)
        return colorEd

    def paint(self, painter, option, index):
        self.initStyleOption(option, index)

        clr = QColor(index.data(Qt.DecorationRole))
        painter.setBrush(clr)
        painter.drawRect(option.rect.adjusted(3, 3, -3, -3))

    def updateEditorGeometry(self, editor, option, index):
        if editor:
            pos = editor.parent().mapToGlobal(option.rect.topLeft())
            ww = editor.rect().width()
            hh = editor.rect().height()
            editor.setGeometry(pos.x() - ww/2, pos.y()-hh/2, ww, hh)


    def setModelData(self, editor, model, index):
        clr = editor.color()
        model.setData(index, clr, Qt.EditRole)
        model.dataChanged.emit(index, index)
