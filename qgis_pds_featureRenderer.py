# -*- coding: utf-8 -*-
import random
from qgis.PyQt import QtGui, uic, QtCore
from qgis.core import *
from qgis.gui import QgsRendererWidget, QgsColorButton, QgsFieldExpressionWidget, QgsColorDialog
from qgis.PyQt.QtWidgets import *
import os
import ast
from .AttributeModel import *


class BubbleFeatureRenderer(QgsFeatureRenderer):
    def __init__(self, syms=None):
        super().__init__("BubbleFeatureRenderer")

        self.layerDiagramms = []

        self.mSymbol = syms
        if not self.mSymbol:
            self.mSymbol = QgsMarkerSymbol()
            geomLayer = QgsGeometryGeneratorSymbolLayer.create({})
            geomLayer.setGeometryExpression("piechart( 'oilmas', 'pwmas', @map_scale, 1, 5, 1)")
            self.mSymbol.changeSymbolLayer(0, geomLayer)
            geomLayer1 = QgsGeometryGeneratorSymbolLayer.create({})
            geomLayer1.setGeometryExpression("piechart( 'oilmas', 'pwmas', @map_scale, 1, 5, 2)")
            self.mSymbol.appendSymbolLayer(geomLayer1)
            self.mSymbol.appendSymbolLayer(QgsSvgMarkerSymbolLayer(''))

    @staticmethod
    def create(domElement, context):
        r = BubbleFeatureRenderer()

        try:
            r.layerDiagramms = ast.literal_eval(domElement.attribute('layerDiagramms'))
            print(r.layerDiagramms)
        except:
            pass

        return r

    def getLayerDiagramms(self):
        return self.layerDiagramms

    def symbolForFeature(self, feature, context):
        # sym = random.choice(self.syms)
        return self.mSymbol

    def startRender(self, context, fields):
        super().startRender(context, fields)

        if self.mSymbol:
            self.mSymbol.startRender(context, fields)

    def stopRender(self, context):
        super().stopRender(context)

        if self.mSymbol:
            self.mSymbol.stopRender(context)

    def usedAttributes(self, context):
        if self.mSymbol:
            return self.mSymbol.usedAttributes(context)
        else:
            return []

    def capabilities(self):
        return QgsFeatureRenderer.SymbolLevels #MoreSymbolsPerFeature May use more than one symbol to render a feature: symbolsForFeature() will return them.

    def legendSymbolItems(self):
        l = []
        l.append(QgsLegendSymbolItem(QgsSymbol.defaultSymbol(QgsWkbTypes.geometryType(QgsWkbTypes.Point)), 'Hello', '1'))
        l.append(QgsLegendSymbolItem(QgsSymbol.defaultSymbol(QgsWkbTypes.geometryType(QgsWkbTypes.Point)), 'Hello1', '2'))
        return l

    def clone(self):
        r = BubbleFeatureRenderer(self.mSymbol.clone())
        r.layerDiagramms = self.layerDiagramms[:]
        return r

    def save(self, doc, context):
        rendererElem = doc.createElement('renderer-v2')

        rendererElem.setAttribute('forceraster', '0')
        rendererElem.setAttribute('type', 'BubbleFeatureRenderer')

        rendererElem.setAttribute('layerDiagramms', str(self.layerDiagramms))

        symbols = {}
        symbols["0"] = self.mSymbol
        symbolsElem = QgsSymbolLayerUtils.saveSymbols(symbols, "symbols", doc, context)
        rendererElem.appendChild(symbolsElem)


        return rendererElem

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'featureRendererWidget_base.ui'))
class BubbleFeatureRendererWidget(QgsRendererWidget, FORM_CLASS):
    def __init__(self, layer, style, renderer):
        super().__init__(layer, style)

        self.setupUi(self)

        if renderer is None or renderer.type() != "BubbleFeatureRenderer":
            self.r = BubbleFeatureRenderer()
        else:
            self.r = renderer.clone()

        self.mDiagrammId = 0

        self.mIface = iface
        self.currentLayer = layer

        # Setup attributes tableView
        self.attributeModel = AttributeTableModel(
            [self.tr(u'Атрибут'), self.tr(u'Цвет фона'), self.tr(u'Цвет линии'), self.tr(u'Имя в легенде')], self)
        self.filteredModel = AttributeFilterProxy(self)
        self.filteredModel.setSourceModel(self.attributeModel)

        self.attributeTableView.setModel(self.filteredModel)
        self.attributeTableView.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

        exprDelegate = ExpressionDelegate(layer, True, self)
        self.attributeTableView.setItemDelegateForColumn(AttributeTableModel.ExpressionColumn, exprDelegate)

        colorDelegate = ColorDelegate(layer, self)
        self.attributeTableView.setItemDelegateForColumn(AttributeTableModel.ColorColumn, colorDelegate)
        colorDelegate2 = ColorDelegate(layer, self)
        self.attributeTableView.setItemDelegateForColumn(AttributeTableModel.ColorLineColumn, colorDelegate2)

        # Setup Labels TableView
        self.labelAttributeModel = AttributeLabelTableModel([self.tr(u'Атрибут'), self.tr(u'Цвет'),
                                                             self.tr(u'Показывать нули'), self.tr(u'С новой строки'),
                                                             self.tr(u'Проценты')], self)
        self.labelFilteredModel = AttributeFilterProxy(self)
        self.labelFilteredModel.setSourceModel(self.labelAttributeModel)

        self.labelAttributeTableView.setModel(self.labelFilteredModel)
        self.labelAttributeTableView.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

        labelExprDelegate = ExpressionDelegate(layer, False, self)
        self.labelAttributeTableView.setItemDelegateForColumn(AttributeTableModel.ExpressionColumn, labelExprDelegate)

        labelColorDelegate = ColorDelegate(layer, self)
        self.labelAttributeTableView.setItemDelegateForColumn(AttributeTableModel.ColorColumn, labelColorDelegate)

        # Add FieldExpression for maximum value calculate
        self.maxValueAttribute = QgsFieldExpressionWidget(self)
        self.maxValueAttribute.setLayer(self.currentLayer)
        self.maxValueAttribute.setFilters(QgsFieldProxyModel.Filters(8))
        self.maxValueAttribute.fieldChanged.connect(self.maxValueAttribute_fieldChanged)
        self.horizontalLayout.addWidget(self.maxValueAttribute)

        # self.layerDiagramms = []

        self.bubbleProps = {}

        self.isCurrentProd = True if self.currentLayer.customProperty(
            "qgis_pds_type") == 'pds_current_production' else False
        self.defaultUnitNum = 2 if self.isCurrentProd else 3

        self.updateWidgets()

        self.filteredModel.setFilter(self.currentDiagrammId)
        self.labelFilteredModel.setFilter(self.currentDiagrammId)

        self.labelAttributeTableView.resizeColumnsToContents()

    @property
    def layerDiagramms(self):
        return self.r.getLayerDiagramms()

    @property
    def currentDiagrammId(self):
        id = 0
        try:
            data = self.mDiagrammsListWidget.currentItem().data(Qt.UserRole)
            id = data.diagrammId
        except:
            pass

        return id

    @property
    def diagrammId(self):
        self.mDiagrammId = self.mDiagrammId + 1
        return self.mDiagrammId

    @pyqtSlot()
    def on_addAttributePushButton_clicked(self):
        curRow = self.attributeModel.rowCount()
        self.attributeModel.insertRow(curRow)

        self.attributeModel.setDiagramm(curRow, self.currentDiagrammId)
        self.filteredModel.setFilter(self.currentDiagrammId)

    @pyqtSlot()
    def on_deleteAttributePushButton_clicked(self):
        rows = [r.row() for r in self.attributeTableView.selectionModel().selectedIndexes()]
        rows.sort(reverse=True)
        for row in rows:
            self.attributeTableView.model().removeRow(row)

    @pyqtSlot()
    def on_addLabelAttributePushButton_clicked(self):
        curRow = self.labelAttributeModel.rowCount()
        self.labelAttributeModel.insertRow(curRow)

        self.labelAttributeModel.setDiagramm(curRow, self.currentDiagrammId)
        self.labelFilteredModel.setFilter(self.currentDiagrammId)

    @pyqtSlot()
    def on_deleteLabelAttributePushButton_clicked(self):
        rows = [r.row() for r in self.labelAttributeTableView.selectionModel().selectedIndexes()]
        rows.sort(reverse=True)
        for row in rows:
            self.labelAttributeTableView.model().removeRow(row)

    def createMyStruct(self):
        newName = u'Диаграмма {}'.format(len(self.layerDiagramms) + 1)
        return {'name': newName, 'scale': 300000, 'scaleType':0, 'scaleAttribute':'',
                        'scaleMinRadius': 3, 'scaleMaxRadius': 15,
                        'fixedSize': 15, 'diagrammId': self.diagrammId}

    def addDiagramm(self):
        d = self.createMyStruct()
        self.layerDiagramms.append(d)

        item = QListWidgetItem(d['name'])
        item.setData(Qt.UserRole, d)
        self.mDiagrammsListWidget.addItem(item)
        self.mDeleteDiagramm.setEnabled(len(self.layerDiagramms) > 1)

    @pyqtSlot()
    def on_mAddDiagramm_clicked(self):
        self.addDiagramm()


    def updateWidgets(self):
        self.mDiagrammsListWidget.clear()

        if len(self.layerDiagramms) < 1:
            self.layerDiagramms.append(self.createMyStruct())

        self.mDeleteDiagramm.setEnabled(len(self.layerDiagramms) > 1)
        for d in self.layerDiagramms:
            name = d['name']
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, d)
            self.mDiagrammsListWidget.addItem(item)

        self.mDiagrammsListWidget.setCurrentRow(0)

    def createExpressionContext(self):
        context = QgsExpressionContext()
        context.appendScope(QgsExpressionContextUtils.globalScope())
        context.appendScope(QgsExpressionContextUtils.projectScope(QgsProject.instance()))
        context.appendScope(QgsExpressionContextUtils.mapSettingsScope(self.mIface.mapCanvas().mapSettings()))
        context.appendScope(QgsExpressionContextUtils.layerScope(self.currentLayer))

        return context

    # SLOTS
    # Toggle diagramm size type (Fixed/Scaled)
    def on_fixedSizeRadioButton_toggled(self, isOn):
        self.fixedDiagrammSize.setEnabled(isOn)
        self.scaledSizeFrame.setEnabled(not isOn)

        idx = self.mDiagrammsListWidget.currentRow()
        if idx >= 0:
            self.layerDiagramms[idx]['scaleType'] = 0 if isOn else 1

    @pyqtSlot(float)
    def on_fixedDiagrammSize_valueChanged(self, value):
        idx = self.mDiagrammsListWidget.currentRow()
        if idx >= 0:
            self.layerDiagramms[idx]['fixedSize'] = value

    @pyqtSlot(str)
    def maxValueAttribute_fieldChanged(self, fieldName):
        idx = self.mDiagrammsListWidget.currentRow()
        if idx >= 0:
            self.layerDiagramms[idx]['scaleAttribute'] = fieldName

    # Calculate max value for diagramm size attribute
    @pyqtSlot()
    def on_scalePushButton_clicked(self):
        idx = self.mDiagrammsListWidget.currentRow()
        if not self.currentLayer or idx < 0:
            return;

        maxValue = 0.0;

        isExpression = self.maxValueAttribute.isExpression()
        sizeFieldNameOrExp = self.maxValueAttribute.currentText()
        if isExpression:
            exp = QgsExpression(sizeFieldNameOrExp)
            context = self.createExpressionContext()
            exp.prepare(context)
            if not exp.hasEvalError():
                features = self.currentLayer.getFeatures()
                for feature in features:
                    context.setFeature(feature)
                    val = exp.evaluate(context)
                    if val:
                        maxValue = max(maxValue, float(val))
        else:
            attributeNumber = self.currentLayer.fields().lookupField(sizeFieldNameOrExp)
            maxValue = float(self.currentLayer.maximumValue(attributeNumber))

        self.scaleEdit.setValue(maxValue);
        self.layerDiagramms[idx]['scale'] = maxValue

    # Change current diagramm
    def on_mDiagrammsListWidget_currentRowChanged(self, row):
        if row < 0:
            return

        diagramm = self.layerDiagramms[row]

        self.scaleEdit.setValue(diagramm['scale'])
        self.titleEdit.setText(diagramm['name'])
        self.maxValueAttribute.setField(diagramm['scaleAttribute'])
        self.minDiagrammSize.setValue(diagramm['scaleMinRadius'])
        self.maxDiagrammSize.setValue(diagramm['scaleMaxRadius'])
        self.fixedDiagrammSize.setValue(diagramm['fixedSize'])
        self.fixedSizeRadioButton.setChecked(diagramm['scaleType'] == 0)
        self.scaledSizeRadioButton.setChecked(diagramm['scaleType'] == 1)

        self.filteredModel.setFilter(self.currentDiagrammId)
        self.labelFilteredModel.setFilter(self.currentDiagrammId)

    # Delete current diagramm
    def mDeleteDiagramm_clicked(self):
        if len(self.layerDiagramms) < 2:
            return

        idx = self.mDiagrammsListWidget.currentRow()
        if idx >= 0:
            for row in range(self.filteredModel.rowCount()):
                self.filteredModel.removeRow(row)

            for row in range(self.labelFilteredModel.rowCount()):
                self.labelFilteredModel.removeRow(row)

            self.mDiagrammsListWidget.takeItem(idx)
            del self.layerDiagramms[idx]

        self.mDeleteDiagramm.setEnabled(len(self.layerDiagramms) > 1)

    # Edit diagramm title finished
    def on_titleEdit_editingFinished(self):
        idx = self.mDiagrammsListWidget.currentRow()
        if idx >= 0:
            self.layerDiagramms[idx]['name'] = self.titleEdit.text()
            item = self.mDiagrammsListWidget.item(idx)
            item.setText(self.titleEdit.text())

    def scaleValueEditingFinished(self):
        idx = self.mDiagrammsListWidget.currentRow()
        if idx >= 0:
            self.layerDiagramms[idx].scale = self.scaleEdit.value()

    @pyqtSlot(float)
    def on_maxDiagrammSize_valueChanged(self, val):
        self.minDiagrammSize.blockSignals(True)
        self.minDiagrammSize.setMaximum(val)
        self.minDiagrammSize.blockSignals(False)
        idx = self.mDiagrammsListWidget.currentRow()
        if idx >= 0:
            self.layerDiagramms[idx].scaleMaxRadius = val

    @pyqtSlot(float)
    def on_minDiagrammSize_valueChanged(self, val):
        idx = self.mDiagrammsListWidget.currentRow()
        if idx >= 0:
            self.layerDiagramms[idx].scaleMinRadius = val

    def getCoordinatesForPercent(self, percent):
        x = math.cos(2 * math.pi * percent)
        y = math.sin(2 * math.pi * percent)
        return (x, y)

    def fluidByCode(self, code):
        for f in bblInit.fluidCodes:
            if f.code == code:
                return f
        return None

    def renderer(self):
        return self.r


class BubbleFeatureRendererMetadata(QgsRendererAbstractMetadata):
    def __init__(self):
        super().__init__("BubbleFeatureRenderer", "PUMA+ Bubble renderer")

    def createRenderer(self, domElement, context):
        return BubbleFeatureRenderer.create(domElement, context)

    def createRendererWidget(self, layer, style, oldRenderer):
        return BubbleFeatureRendererWidget(layer, style, oldRenderer)


# QgsApplication.rendererRegistry().addRenderer(BubbleFeatureRendererMetadata())