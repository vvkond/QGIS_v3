# -*- coding: utf-8 -*-

from PyQt4 import QtGui, uic, QtCore
# from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import *
# from PyQt4.QtCore import *
from qgis import core, gui
from qgis.gui import QgsColorButtonV2
# from qgis.gui import *
# from qgscolorbuttonv2 import QgsColorButtonV2
from collections import namedtuple
from qgis_pds_production import *
from bblInit import *
import ast
import math

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'qgis_pds_prodsetup_base.ui'))

class QgisPDSProdSetup(QtGui.QDialog, FORM_CLASS):
    def __init__(self, iface, layer, parent=None):
        super(QgisPDSProdSetup, self).__init__(parent)

        self.setupUi(self)

        self.backColorEdit = QgsColorButtonV2(self)
        self.fluidGridLayout.addWidget(self.backColorEdit, 0, 1)
        QObject.connect(self.backColorEdit, SIGNAL("colorChanged(const QColor &)"), self.backColorChanged)

        self.lineColorEdit = QgsColorButtonV2(self)
        self.fluidGridLayout.addWidget(self.lineColorEdit, 1, 1)
        QObject.connect(self.lineColorEdit, SIGNAL("colorChanged(const QColor &)"), self.lineColorChanged)

        self.labelColorEdit = QgsColorButtonV2(self)
        self.labelGridLayout.addWidget(self.labelColorEdit, 0, 1)
        QObject.connect(self.labelColorEdit, SIGNAL("colorChanged(const QColor &)"), self.labelColorChanged)

        self.mIface = iface
        self.currentLayer = layer       

        self.standardDiagramms = {
                    "1_liquidproduction": MyStruct(name=u'Диаграмма жидкости', scale=300000, testval=1, unitsType=0, units=0, fluids=[1, 0, 1, 0, 0, 0, 0, 0]),
                    "2_liquidinjection": MyStruct(name=u'Диаграмма закачки', scale=300000, testval=1,unitsType=0, units=0, fluids=[0, 0, 0, 0, 1, 1, 0, 0]),
                    "3_gasproduction": MyStruct(name=u"Диаграмма газа", scale=300000, testval=1,unitsType=1, units=0, fluids=[0, 1, 0, 0, 0, 0, 0, 0]),
                    "4_condensatproduction": MyStruct(name=u"Диаграмма конденсата", scale=3000000, testval=1,unitsType=0, units=0, fluids=[0, 0, 0, 1, 0, 0, 0, 0])
                }

        self.layerDiagramms = []

        self.componentsList.clear()
        i = 1
        for fl in bblInit.fluidCodes:
            item = QtGui.QListWidgetItem(str(i)+". "+ QCoreApplication.translate('bblInit', fl.name))
            item.setData(Qt.UserRole, fl.code)
            item.setCheckState(Qt.Unchecked)
            self.componentsList.addItem(item)
            i = i + 1


        self.bubbleProps = None
        renderer = self.currentLayer.rendererV2()
        if renderer is not None and renderer.type() == 'RuleRenderer':
            root_rule = renderer.rootRule()
            for r in root_rule.children():
                for l in r.symbol().symbolLayers():
                    if l.layerType() == 'BubbleMarker':
                        self.bubbleProps = l.properties()
                        break
                if self.bubbleProps is not None:
                    break

        if self.bubbleProps is None:
            registry = QgsSymbolLayerV2Registry.instance()
            bubbleMeta = registry.symbolLayerMetadata('BubbleMarker')
            if bubbleMeta is not None:
                bubbleLayer = bubbleMeta.createSymbolLayer({})
                self.bubbleProps = bubbleLayer.properties()

        if self.bubbleProps is None:
            self.bubbleProps = {}

        #Read saved layer settings
        self.readSettings()

        # self.diagrammType.blockSignals(True)
        # self.diagrammType.clear()
        # for d in self.standardDiagramms:
        #     name = self.standardDiagramms[d].name
        #     self.diagrammType.addItem(name, d)
        # self.diagrammType.blockSignals(False)
    
        self.scaleUnitsMass.setVisible(False)
        self.scaleUnitsVolume.setVisible(False)
                 
        #set current diagramm
        # self.diagrammType.setCurrentIndex(self.diagrammType.findData(self.currentDiagramm))

        # diagramms =  self.currentDiagramm.split(';')
        if len(self.layerDiagramms) < 1:
            self.layerDiagramms.append(MyStruct(name=u'Диаграмма жидкости', scale=300000, testval=1, unitsType=0, units=0, fluids=[1, 0, 1, 0, 0, 0, 0, 0]))

        self.mDeleteDiagramm.setEnabled(len(self.layerDiagramms) > 0)
        for d in self.layerDiagramms:
            name = d.name
            item = QtGui.QListWidgetItem(name)
            item.setData(Qt.UserRole, d)
            self.mDiagrammsListWidget.addItem(item)

        return



    # SLOT
    def on_mDiagrammsListWidget_currentRowChanged(self, row):
        if row < 0:
            return

        item = self.mDiagrammsListWidget.item(row)
        diagramm = item.data(Qt.UserRole)
        self.scaleUnitsType.setCurrentIndex(diagramm.unitsType)
        self.scaleEdit.setValue(diagramm.scale)
        self.scaleUnitsMass.setCurrentIndex(diagramm.units)
        self.scaleUnitsVolume.setCurrentIndex(diagramm.units)
        self.titleEdit.setText(diagramm.name)

        self.scaleUnitsMass.setVisible(diagramm.unitsType == 0)
        self.scaleUnitsVolume.setVisible(diagramm.unitsType == 1)

        vec = diagramm.fluids
        for idx, v in enumerate(vec):
            self.componentsList.item(idx).setCheckState(Qt.Checked if v else Qt.Unchecked)

    def mAddDiagramm_clicked(self):
        newName = u'Диаграмма {}'.format(len(self.layerDiagramms)+1)
        d = MyStruct(name=newName, scale=300000, testval=1, unitsType=0, units=0,
                                            fluids=[0, 0, 0, 0, 0, 0, 0, 0])
        self.layerDiagramms.append(d)

        item = QtGui.QListWidgetItem(newName)
        item.setData(Qt.UserRole, d)
        self.mDiagrammsListWidget.addItem(item)

    # def diagrammTypeChanged(self, index):
    #     if index < 0:
    #         return
    #
    #     self.currentDiagramm = self.diagrammType.itemData(index)
    #     diagramm = self.standardDiagramms[self.currentDiagramm]
    #
    #     self.scaleUnitsType.setCurrentIndex(diagramm.unitsType)
    #     self.scaleEdit.setValue(diagramm.scale)
    #     self.scaleUnitsMass.setCurrentIndex(diagramm.units)
    #     self.scaleUnitsVolume.setCurrentIndex(diagramm.units)
    #
    #     self.scaleUnitsMass.setVisible(diagramm.unitsType == 0)
    #     self.scaleUnitsVolume.setVisible(diagramm.unitsType == 1)
    #
    #     vec = diagramm.fluids
    #     for idx, v in enumerate(vec):
    #         self.componentsList.item(idx).setCheckState(Qt.Checked if v else Qt.Unchecked)


    # SLOT
    def on_titleEdit_editingFinished(self):
        idx = self.mDiagrammsListWidget.currentRow()
        if idx >= 0:
            self.layerDiagramms[idx].name = self.titleEdit.text()
            item = self.mDiagrammsListWidget.item(idx)
            item.setText(self.titleEdit.text())


    def on_buttonBox_accepted(self):
        self.setup(self.currentLayer)

    # SLOT
    def on_buttonBox_clicked(self, btn):
        if self.buttonBox.buttonRole(btn) == QDialogButtonBox.ApplyRole:
            self.setup(self.currentLayer)


    # SLOT
    # def setup(self, editLayer):
    #
    #     self.applySettings()
    #
    #     maxDiagrammSize = self.maxDiagrammSize.value() / 2
    #     minDiagrammSize = self.minDiagrammSize.value() / 2
    #     dScale = self.scaleEdit.value()
    #
    #     code = self.diagrammType.itemData(self.diagrammType.currentIndex())
    #
    #
    #     vec = self.standardDiagramms[code].fluids
    #     if self.scaleUnitsType.currentIndex() == 0:
    #         scaleType = QgisPDSProductionDialog.attrFluidMass("")
    #     else:
    #         scaleType = QgisPDSProductionDialog.attrFluidVolume("")
    #
    #     prodFields = [ bblInit.fluidCodes[idx].code for idx, v in enumerate(vec) if v]
    #     prods = [ bblInit.fluidCodes[idx] for idx, v in enumerate(vec) if v]
    #
    #     koef = (maxDiagrammSize-minDiagrammSize) / dScale
    #
    #     editLayerProvider = editLayer.dataProvider()
    #
    #     uniqSymbols = {}
    #
    #     editLayer.startEditing()
    #
    #     idxOffX = editLayerProvider.fieldNameIndex('LablOffX')
    #     idxOffY = editLayerProvider.fieldNameIndex('LablOffY')
    #     if idxOffX < 0 or idxOffY < 0:
    #         editLayerProvider.addAttributes(
    #             [QgsField("LablOffX", QVariant.Double),
    #              QgsField("LablOffY", QVariant.Double)])
    #
    #     iter = editLayerProvider.getFeatures()
    #     for feature in iter:
    #         geom = feature.geometry()
    #         FeatureId = feature.id()
    #
    #         uniqSymbols[feature['SymbolCode']] = feature['SymbolName']
    #
    #         sum = 0
    #         for attrName in prodFields:
    #             attr = attrName+scaleType
    #             if feature[attr] is not None:
    #                 sum += feature[attr]
    #
    #         diagrammSize = minDiagrammSize + sum * koef
    #
    #         point = geom.asPoint()
    #         origX = point.x()
    #         origY = point.y()
    #
    #         offset = diagrammSize if diagrammSize < maxDiagrammSize else maxDiagrammSize
    #         if feature.attribute('LablOffset') is None:
    #             editLayer.changeAttributeValue(FeatureId, editLayerProvider.fieldNameIndex('LablOffX'), offset)
    #             editLayer.changeAttributeValue(FeatureId, editLayerProvider.fieldNameIndex('LablOffY'), -offset)
    #
    #         # editLayer.changeAttributeValue(FeatureId, editLayerProvider.fieldNameIndex('LablOffset'), offset)
    #
    #         editLayer.changeAttributeValue(FeatureId, editLayerProvider.fieldNameIndex('BubbleSize'), diagrammSize*2)
    #         editLayer.changeAttributeValue(FeatureId, editLayerProvider.fieldNameIndex('BubbleFields'), ','.join(prodFields))
    #         editLayer.changeAttributeValue(FeatureId, editLayerProvider.fieldNameIndex('ScaleType'), scaleType)
    #
    #     editLayer.commitChanges()
    #
    #     plugin_dir = os.path.dirname(__file__)
    #
    #     registry = QgsSymbolLayerV2Registry.instance()
    #
    #     symbol = QgsMarkerSymbolV2()
    #     bubbleMeta = registry.symbolLayerMetadata('BubbleMarker')
    #     if bubbleMeta is not None:
    #         bubbleLayer = bubbleMeta.createSymbolLayer(self.bubbleProps)
    #         bubbleLayer.setSize(0.001)
    #         bubbleLayer.setSizeUnit(QgsSymbolV2.MapUnit)
    #         symbol.changeSymbolLayer(0, bubbleLayer)
    #     else:
    #         symbol.changeSymbolLayer(0, QgsSvgMarkerSymbolLayerV2())
    #
    #     renderer = QgsRuleBasedRendererV2(symbol)
    #     root_rule = renderer.rootRule()
    #
    #     args = (self.standardDiagramms[code].name, self.standardDiagramms[code].scale)
    #     root_rule.children()[0].setLabel(u'{0} {1}'.format(*args))
    #     for symId in uniqSymbols:
    #         svg = QgsSvgMarkerSymbolLayerV2()
    #         svg.setPath(plugin_dir+"/svg/WellSymbol"+str(symId).zfill(3)+".svg")
    #         svg.setSize(4)
    #         svg.setSizeUnit(QgsSymbolV2.MM)
    #         symbol = QgsMarkerSymbolV2()
    #         symbol.changeSymbolLayer(0, svg)
    #
    #         rule = QgsRuleBasedRendererV2.Rule(symbol)
    #         rule.setLabel(uniqSymbols[symId])
    #
    #         args = ("SymbolCode", symId)
    #         rule.setFilterExpression(u'\"{0}\"={1}'.format("SymbolCode", symId))
    #         root_rule.appendChild(rule)
    #
    #     #add lift method
    #     # ggMeta = registry.symbolLayerMetadata('GeometryGenerator')
    #     # if ggMeta is not None:
    #     #     gg = ggMeta.createSymbolLayer({})
    #     #     gg.setGeometryExpression ("make_line(  make_point( $x, $y),  make_point( $x, $y+ \"BubbleSize\"/1.5 ))")
    #     #     gg.setSymbolType(QgsSymbolV2.Line)
    #     #     symbol = QgsMarkerSymbolV2()
    #     #     symbol.changeSymbolLayer(0, gg)
    #     #     rule = QgsRuleBasedRendererV2.Rule(symbol)
    #     #     rule.setLabel('flowing')
    #
    #     #     args = ("LiftMethod", "flowing")
    #     #     rule.setFilterExpression(u'\"{0}\"=\'{1}\''.format(*args))
    #     #     root_rule.appendChild(rule)
    #
    #
    #     for ff in prods:
    #         m = QgsSimpleMarkerSymbolLayerV2()
    #         m.setSize(4)
    #         m.setSizeUnit(QgsSymbolV2.MM)
    #         m.setColor(ff.backColor)
    #         symbol = QgsMarkerSymbolV2()
    #         symbol.changeSymbolLayer(0, m)
    #
    #         rule = QgsRuleBasedRendererV2.Rule(symbol)
    #         rule.setLabel(ff.name)
    #         rule.setFilterExpression(u'\"SymbolCode\"=-1')
    #         root_rule.appendChild(rule)
    #
    #     renderer.setOrderByEnabled(True)
    #     orderByClause = QgsFeatureRequest.OrderByClause('BubbleSize', False)
    #     orderBy = QgsFeatureRequest.OrderBy([orderByClause])
    #     renderer.setOrderBy(orderBy)
    #     editLayer.setRendererV2(renderer)
    #
    #     editLayer.triggerRepaint()
    #
    #     return

    def getCoordinatesForPercent(self, percent):
        x = math.cos(2 * math.pi * percent)
        y = math.sin(2 * math.pi * percent)
        return (x, y)


    def setup(self, editLayer):

        self.applySettings()

        project_path = QgsProject.instance().homePath() + u'/.svg'
        try:
            os.mkdir(project_path)
        except:
            pass

        maxDiagrammSize = self.maxDiagrammSize.value()
        minDiagrammSize = self.minDiagrammSize.value()

        editLayerProvider = editLayer.dataProvider()

        uniqSymbols = {}

        editLayer.startEditing()

        idxOffX = editLayerProvider.fieldNameIndex('LablOffX')
        idxOffY = editLayerProvider.fieldNameIndex('LablOffY')
        if idxOffX < 0 or idxOffY < 0:
            editLayerProvider.addAttributes(
                [QgsField("LablOffX", QVariant.Double),
                 QgsField("LablOffY", QVariant.Double)])

        idxSvg = editLayerProvider.fieldNameIndex('SVG')
        if idxSvg < 0 :
            editLayerProvider.addAttributes([QgsField("SVG", QVariant.String)])

        iter = editLayerProvider.getFeatures()
        for feature in iter:
            geom = feature.geometry()
            FeatureId = feature.id()

            uniqSymbols[feature['SymbolCode']] = feature['SymbolName']

            fileName = project_path + "/bbl{}.svg".format(FeatureId)
            text_file = open(fileName, "w")
            text_file.write(u'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
            text_file.write(u'<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 20010904//EN"\n')
            text_file.write(u'             "http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd">\n')
            text_file.write(u'<svg xmlns="http://www.w3.org/2000/svg"\n')
            # text_file.write(u'     width="10mm" height="10mm"\n')
            # text_file.write(u'     viewBox="0 0 {0} {1}">\n'.format(maxDiagrammSize, maxDiagrammSize) )
            text_file.write(u'     viewBox="-1 -1 2 2">\n')
            diagrammSize = 0
            for d in self.layerDiagramms:
                vec = d.fluids
                if self.scaleUnitsType.currentIndex() == 0:
                    scaleType = QgisPDSProductionDialog.attrFluidMass("")
                else:
                    scaleType = QgisPDSProductionDialog.attrFluidVolume("")

                prodFields = [bblInit.fluidCodes[idx].code for idx, v in enumerate(vec) if v]
                prods = [bblInit.fluidCodes[idx] for idx, v in enumerate(vec) if v]

                koef = (maxDiagrammSize - minDiagrammSize) / d.scale
                sum = 0
                for attrName in prodFields:
                    attr = attrName + scaleType
                    if feature[attr] is not None:
                        sum += feature[attr]

                if sum != 0:
                    cumulativeRadians = 0
                    for attrName in prodFields:
                        attr = attrName + scaleType
                        if feature[attr] is not None:
                            startX = math.cos(cumulativeRadians)
                            startY = math.sin(cumulativeRadians)
                            percent = feature[attr] / sum
                            cumulativeRadians =  cumulativeRadians + 2 * math.pi * percent
                            endX = math.cos(cumulativeRadians)
                            endY = math.sin(cumulativeRadians)
                            largeArcFlag = 1 #1 if percent > 0.5 else 0
                            text_file.write(u'<path fill="red" stroke="white" d="M {0} {1} A 1 1 0 {2} 1 {3} {4} L 0 0" />\n'
                                            .format(startX, startY, largeArcFlag, endX, endY))


                if minDiagrammSize + sum * koef > diagrammSize:
                    diagrammSize = minDiagrammSize + sum * koef
                # text_file.write(u'<circle fill="black" stroke="black" cx="0" cy="0" r="1" />\n')

            text_file.write(u'</svg>\n')
            text_file.close()
            editLayer.changeAttributeValue(FeatureId, editLayerProvider.fieldNameIndex('SVG'), fileName)

            point = geom.asPoint()

            offset = diagrammSize if diagrammSize < maxDiagrammSize else maxDiagrammSize
            if feature.attribute('LablOffset') is None:
                editLayer.changeAttributeValue(FeatureId, editLayerProvider.fieldNameIndex('LablOffX'), offset)
                editLayer.changeAttributeValue(FeatureId, editLayerProvider.fieldNameIndex('LablOffY'), -offset)

            editLayer.changeAttributeValue(FeatureId, editLayerProvider.fieldNameIndex('BubbleSize'), diagrammSize)
            editLayer.changeAttributeValue(FeatureId, editLayerProvider.fieldNameIndex('BubbleFields'),
                                           ','.join(prodFields))
            editLayer.changeAttributeValue(FeatureId, editLayerProvider.fieldNameIndex('ScaleType'), scaleType)

        editLayer.commitChanges()

        plugin_dir = os.path.dirname(__file__)

        registry = QgsSymbolLayerV2Registry.instance()

        symbol = QgsMarkerSymbolV2()
        svg = QgsSvgMarkerSymbolLayerV2()
        # svg.setPath(plugin_dir + "/svg/WellSymbol" + str(symId).zfill(3) + ".svg")
        svg.setSize(4)
        svg.setSizeUnit(QgsSymbolV2.MM)
        svg.setDataDefinedProperty('name', 'SVG')
        svg.setDataDefinedProperty('size', 'BubbleSize')
        symbol.changeSymbolLayer(0, svg)

        renderer = QgsRuleBasedRendererV2(symbol)
        root_rule = renderer.rootRule()

        # args = (self.standardDiagramms[code].name, self.standardDiagramms[code].scale)
        # root_rule.children()[0].setLabel(u'{0} {1}'.format(*args))
        for symId in uniqSymbols:
            svg = QgsSvgMarkerSymbolLayerV2()
            svg.setPath(plugin_dir + "/svg/WellSymbol" + str(symId).zfill(3) + ".svg")
            svg.setSize(4)
            svg.setSizeUnit(QgsSymbolV2.MM)
            symbol = QgsMarkerSymbolV2()
            symbol.changeSymbolLayer(0, svg)

            rule = QgsRuleBasedRendererV2.Rule(symbol)
            rule.setLabel(uniqSymbols[symId])

            args = ("SymbolCode", symId)
            rule.setFilterExpression(u'\"{0}\"={1}'.format("SymbolCode", symId))
            root_rule.appendChild(rule)


        for ff in prods:
            m = QgsSimpleMarkerSymbolLayerV2()
            m.setSize(4)
            m.setSizeUnit(QgsSymbolV2.MM)
            m.setColor(ff.backColor)
            symbol = QgsMarkerSymbolV2()
            symbol.changeSymbolLayer(0, m)

            rule = QgsRuleBasedRendererV2.Rule(symbol)
            rule.setLabel(ff.name)
            rule.setFilterExpression(u'\"SymbolCode\"=-1')
            root_rule.appendChild(rule)

        renderer.setOrderByEnabled(True)
        orderByClause = QgsFeatureRequest.OrderByClause('BubbleSize', False)
        orderBy = QgsFeatureRequest.OrderBy([orderByClause])
        renderer.setOrderBy(orderBy)
        editLayer.setRendererV2(renderer)

        editLayer.triggerRepaint()

        return


    def scaleValueEditingFinished(self):
        idx = self.mDiagrammsListWidget.currentRow()
        if idx >= 0:
            self.layerDiagramms[idx].scale = self.scaleEdit.value()
            # code = self.diagrammType.itemData(idx)
            # self.standardDiagramms[code].scale = self.scaleEdit.value()


    def scaleUnitsChanged(self, index):
        idx = self.mDiagrammsListWidget.currentRow()
        if idx >= 0:
            self.layerDiagramms[idx].unitsType = index
        # self.standardDiagramms[self.currentDiagramm].unitsType = index

        self.scaleUnitsMass.setVisible(index == 0)
        self.scaleUnitsVolume.setVisible(index == 1)


    def unitsChanged(self, index):
        idx = self.mDiagrammsListWidget.currentRow()
        if idx >= 0:
            self.layerDiagramms[idx].units = index
        # self.standardDiagramms[self.currentDiagramm].units = index


    def unitsChangedVol(self, index):
        idx = self.mDiagrammsListWidget.currentRow()
        if idx >= 0:
            self.layerDiagramms[idx].units = index+10
        # self.standardDiagramms[self.currentDiagramm].units = index+10


    def componentsItemClicked(self, item):
        # idx = self.diagrammType.currentIndex()
        # if idx >= 0:
        #     code = self.diagrammType.itemData(idx)
        idx = self.mDiagrammsListWidget.currentRow()
        if idx >= 0:
            val = self.layerDiagramms[idx]
            # val = self.standardDiagramms[code]
            row = self.componentsList.row(item)
            val.fluids[row] = 1 if item.checkState() == Qt.Checked else 0

#            self.backColorEdit.setColor(val.backColor

    def on_componentsList_currentRowChanged(self, row):
        if row < 0:
            return

        self.backColorEdit.blockSignals(True)
        self.lineColorEdit.blockSignals(True)
        self.labelColorEdit.blockSignals(True)
        self.showInPercent.blockSignals(True)

        self.backColorEdit.setColor(bblInit.fluidCodes[row].backColor)
        self.lineColorEdit.setColor(bblInit.fluidCodes[row].lineColor)
        self.labelColorEdit.setColor(bblInit.fluidCodes[row].labelColor)
        self.showInPercent.setChecked(bblInit.fluidCodes[row].inPercent);

        self.backColorEdit.blockSignals(False)
        self.lineColorEdit.blockSignals(False)
        self.labelColorEdit.blockSignals(False)
        self.showInPercent.blockSignals(False)
        return


    def on_showInPercent_clicked(self):
        row = self.componentsList.currentRow()
        if row < 0:
            return

        bblInit.fluidCodes[row].inPercent = 1 if self.showInPercent.isChecked() else 0
        return

    #SLOT
    def backColorChanged(self, color):
        row = self.componentsList.currentRow()
        if row < 0:
            return

        bblInit.fluidCodes[row].backColor = color
        return


    def lineColorChanged(self, color):
        row = self.componentsList.currentRow()
        if row < 0:
            return

        bblInit.fluidCodes[row].lineColor = color
        return


    def labelColorChanged(self, color):
        row = self.componentsList.currentRow()
        if row < 0:
            return

        bblInit.fluidCodes[row].labelColor = color
        return


    # def on_diagrammType_editTextChanged(self, text):
    #     idx = self.diagrammType.currentIndex()
    #     if idx >= 0:
    #         self.diagrammType.setItemText(idx, text);
    #         code = self.diagrammType.itemData(idx)
    #         self.standardDiagramms[code].name = text

    def on_addToTemplate_pressed(self):
        row = self.componentsList.currentRow()
        if row < 0:
            return

        tmpStr = self.templateExpression.text()
        self.templateExpression.setText(tmpStr + '-%' + str(row+1))


    #Read layer settings
    def readSettings(self):
        if self.readSettingsNew():
            return

        self.currentDiagramm = self.bubbleProps['diagrammType'] if 'diagrammType' in self.bubbleProps else '1_liquidproduction'
        self.maxDiagrammSize.setValue(float(self.bubbleProps["maxDiagrammSize"]) if 'maxDiagrammSize' in self.bubbleProps else 0.01)
        self.minDiagrammSize.setValue(float(self.bubbleProps["minDiagrammSize"]) if 'minDiagrammSize' in self.bubbleProps else 0.0)

        for d in self.standardDiagramms:
            val = self.standardDiagramms[d]
            name = self.bubbleProps['diagramm_name_'+d] if 'diagramm_name_'+d in self.bubbleProps else ''
            if name :
                val.name = name
            val.scale = float(self.bubbleProps['diagramm_scale_'+d]) if 'diagramm_scale_'+d in self.bubbleProps else val.scale
            val.unitsType =  int(self.bubbleProps['diagramm_unitsType_'+d]) if 'diagramm_unitsType_'+d in self.bubbleProps else val.unitsType
            val.units = int(self.bubbleProps['diagramm_units_'+d]) if 'diagramm_units_'+d in self.bubbleProps else val.units
            if 'diagramm_fluids_'+d in self.bubbleProps :
                val.fluids = QgsSymbolLayerV2Utils.decodeRealVector(self.bubbleProps['diagramm_fluids_'+d])
            self.standardDiagramms[d] = val

        scope = QgsExpressionContextUtils.layerScope(self.currentLayer)


        self.labelSizeEdit.setValue(float(self.bubbleProps['labelSize']) if 'labelSize' in self.bubbleProps else self.labelSizeEdit.value() )
        self.decimalEdit.setValue(int(self.bubbleProps['decimal']) if 'decimal' in self.bubbleProps else self.decimalEdit.value())
        self.templateExpression.setText(self.bubbleProps['labelTemplate'] if 'labelTemplate' in self.bubbleProps else self.templateExpression.text())
        self.showLineouts.setChecked(int(self.bubbleProps['showLineout']) if 'showLineout' in self.bubbleProps else 1)
        self.dailyProduction.setChecked(int(self.bubbleProps['dailyProduction']) if 'dailyProduction' in self.bubbleProps else 0)

        for fl in bblInit.fluidCodes:
            if 'fluid_background_'+fl.code in self.bubbleProps:
                fl.backColor = QgsSymbolLayerV2Utils.decodeColor(self.bubbleProps['fluid_background_'+fl.code])
            if 'fluid_line_color_'+fl.code in self.bubbleProps:
                fl.lineColor = QgsSymbolLayerV2Utils.decodeColor(self.bubbleProps['fluid_line_color_'+fl.code])
            if 'fluid_label_color_'+fl.code in self.bubbleProps:
                fl.labelColor = QgsSymbolLayerV2Utils.decodeColor(self.bubbleProps['fluid_label_color_'+fl.code])
            if 'fluid_inPercent_'+fl.code in self.bubbleProps:
                fl.inPercent = int(self.bubbleProps['fluid_inPercent_'+fl.code])

        return

    #Write layer settings
    def applySettings(self):
        self.saveSettings()

        # self.bubbleProps['diagrammType'] = self.currentDiagramm
        # self.bubbleProps["maxDiagrammSize"] = str(self.maxDiagrammSize.value())
        # self.bubbleProps["minDiagrammSize"] = str(self.minDiagrammSize.value())
        #
        # for d in self.standardDiagramms:
        #     val = self.standardDiagramms[d]
        #     self.bubbleProps['diagramm_name_'+d] = val.name
        #     self.bubbleProps['diagramm_scale_'+d] = str(val.scale)
        #     self.bubbleProps['diagramm_unitsType_'+d] = str(val.unitsType)
        #     self.bubbleProps['diagramm_units_'+d] = str(val.units)
        #     self.bubbleProps['diagramm_fluids_'+d] = QgsSymbolLayerV2Utils.encodeRealVector(val.fluids)
        #
        # self.bubbleProps['labelSize'] = str(self.labelSizeEdit.value())
        # self.bubbleProps['decimal'] = str(self.decimalEdit.value())
        # self.bubbleProps['labelTemplate'] = self.templateExpression.text()
        # self.bubbleProps['showLineout'] = str(int(self.showLineouts.isChecked()))
        # self.bubbleProps['dailyProduction'] = str(int(self.dailyProduction.isChecked()))
        # for fl in bblInit.fluidCodes:
        #     self.bubbleProps['fluid_background_'+fl.code] =  QgsSymbolLayerV2Utils.encodeColor(fl.backColor)
        #     self.bubbleProps['fluid_line_color_'+fl.code] = QgsSymbolLayerV2Utils.encodeColor(fl.lineColor)
        #     self.bubbleProps['fluid_label_color_'+fl.code] = QgsSymbolLayerV2Utils.encodeColor(fl.labelColor)
        #     self.bubbleProps['fluid_inPercent_'+fl.code] = str(fl.inPercent)

        return

    def readSettingsNew(self):
        count = self.currentLayer.customProperty("diagrammCount", 0)
        if count < 1:
            return False

        self.currentDiagramm = '1_liquidproduction'
        self.maxDiagrammSize.setValue(self.currentLayer.customProperty('maxDiagrammSize', 0.01))
        self.minDiagrammSize.setValue(self.currentLayer.customProperty('minDiagrammSize', 0.0))

        self.layerDiagramms = []
        for num in xrange(count):
            d = str(num+1)
            val = MyStruct()
            val.name = self.currentLayer.customProperty('diagramm_name_' + d, "--")
            val.scale = self.currentLayer.customProperty('diagramm_scale_' + d, 300000)
            val.unitsType = self.currentLayer.customProperty('diagramm_unitsType_' + d, 0)
            val.units = self.currentLayer.customProperty('diagramm_units_' + d, 0)
            val.fluids = self.currentLayer.customProperty('diagramm_fluids_' + d, [])
            self.layerDiagramms.append(val)

        self.labelSizeEdit.setValue(self.currentLayer.customProperty('labelSize', self.labelSizeEdit.value()))
        self.decimalEdit.setValue(self.currentLayer.customProperty('decimal', self.decimalEdit.value()))
        self.templateExpression.setText(self.currentLayer.customProperty('labelTemplate', self.templateExpression.text()))
        self.showLineouts.setChecked(self.currentLayer.customProperty('showLineout', True))
        self.dailyProduction.setChecked(self.currentLayer.customProperty('dailyProduction', False))
        for fl in bblInit.fluidCodes:
            fl.backColor = self.currentLayer.customProperty('fluid_background_' + fl.code, QColor(Qt.darkRed))
            fl.lineColor = self.currentLayer.customProperty('fluid_line_color_' + fl.code, QColor(Qt.black))
            fl.labelColor = self.currentLayer.customProperty('fluid_label_color_' + fl.code, QColor(Qt.black))
            fl.inPercent = self.currentLayer.customProperty('fluid_inPercent_' + fl.code, False)

        return True

    def saveSettings(self):
        self.currentLayer.setCustomProperty("diagrammCount", len(self.layerDiagramms))

        self.currentLayer.setCustomProperty("maxDiagrammSize", self.maxDiagrammSize.value())
        self.currentLayer.setCustomProperty("minDiagrammSize", self.minDiagrammSize.value())

        num = 1
        for val in self.layerDiagramms:
            d = str(num)
            self.currentLayer.setCustomProperty('diagramm_name_' + d, val.name)
            self.currentLayer.setCustomProperty('diagramm_scale_' + d, val.scale)
            self.currentLayer.setCustomProperty('diagramm_unitsType_' + d, val.unitsType)
            self.currentLayer.setCustomProperty('diagramm_units_' + d, val.units)
            self.currentLayer.setCustomProperty('diagramm_fluids_' + d, val.fluids)
            num = num + 1

        self.currentLayer.setCustomProperty('labelSize', self.labelSizeEdit.value())
        self.currentLayer.setCustomProperty('decimal', self.decimalEdit.value())
        self.currentLayer.setCustomProperty('labelTemplate', self.templateExpression.text())
        self.currentLayer.setCustomProperty('showLineout', self.showLineouts.isChecked())
        self.currentLayer.setCustomProperty('dailyProduction', self.dailyProduction.isChecked())
        for fl in bblInit.fluidCodes:
            self.currentLayer.setCustomProperty('fluid_background_' + fl.code, fl.backColor)
            self.currentLayer.setCustomProperty('fluid_line_color_' + fl.code, fl.lineColor)
            self.currentLayer.setCustomProperty('fluid_label_color_' + fl.code, fl.labelColor)
            self.currentLayer.setCustomProperty('fluid_inPercent_' + fl.code, fl.inPercent)
