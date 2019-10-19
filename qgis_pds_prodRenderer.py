# -*- coding: utf-8 -*-

"""
/***************************************************************************
 QgisPDS
                                 A QGIS plugin
 PDS link
                              -------------------
        begin                : 2016-11-05
        git sha              : $Format:%H$
        copyright            : (C) 2016 by SoyuzGeoService
        email                :
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.PyQt import uic
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.core import *
from qgis.gui import *
from .bblInit import *
import random
import os,sys
import xml.etree.cElementTree as ET
import ast
import re
from datetime import datetime

try:
    from qgis.PyQt.QtCore import QString
except ImportError:
    # we are using Python3 so QString is not defined
    QString = type("")

class DiagrammSlice(MyStruct):
    backColor = QColor(Qt.red)
    lineColor = QColor(Qt.black)
    fieldName = ''
    percent = 0.0

class DiagrammDesc:
    def __init__(self, diagrammSize, slices,realSize=None):
        self.mDiagrammSize = diagrammSize
        self.mRealSize = realSize
        self.mSlices = slices

    def __repr__(self):
        return repr((self.mRealSize, self.mDiagrammSize, self.mSlices))
    def __str__(self):
        return self.__repr__()


def float_t(val):
    if val is None or (val and val.isNull()):
        val=0.0
    try:
        return float(val)
    except Exception as e:
        QgsMessageLog.logMessage("incorrect val for float {}={}\n{}".format(type(val),val,str(e)), 'BubbleSymbolLayer')
        #raise Exception("incorrect val for float {}={}\n{}".format(type(val),val,str(e)))

class BubbleSymbolLayer(QgsSimpleMarkerSymbolLayer):

    LAYERTYPE="BubbleDiagramm"
    DIAGRAMM_FIELDS = 'DIAGRAMM_FIELDS'
    LABEL_OFFSETX = 'labloffx'
    LABEL_OFFSETY = 'labloffy'
    BUBBLE_SIZE = 'bubblesize'
    DIAGRAMM_LABELS = 'bbllabels'
    DEBUG=False

    def __init__(self, props):
        super().__init__()

        ts=datetime.now()
        self.radius = 4.0
        self.color = QColor(255,0,0)

        self.showLineouts = True
        self.showLabels = True
        self.showDiagramms = True
        self.labelSize = 7.0
        self.diagrammStr = u''
        self.templateStr = None
        # self.labelDataSums = None

        self.attrsUsed = {OLD_NEW_FIELDNAMES[1], BubbleSymbolLayer.LABEL_OFFSETX, BubbleSymbolLayer.LABEL_OFFSETY,
                          BubbleSymbolLayer.BUBBLE_SIZE, BubbleSymbolLayer.DIAGRAMM_LABELS, BubbleSymbolLayer.DIAGRAMM_LABELS}

        try:
            self.showLineouts  = props[QString("showLineouts")]  == "True" if QString("showLineouts")  in props else True
            self.showLabels    = props[QString("showLabels")]    == "True" if QString("showLabels")    in props else True
            self.showDiagramms = props[QString("showDiagramms")] == "True" if QString("showDiagramms") in props else True
            self.labelSize     = float(props[QString("labelSize")]) if QString("labelSize")   in props else 7.0
            self.diagrammStr   = props[QString("diagrammStr")]      if QString("diagrammStr") in props else u'';
            self.templateStr   = props[QString("templateStr")]      if QString("templateStr") in props else u'';
            # self.labelDataSums = props[QString("labelDataSums")] if QString("labelDataSums") in props else None;
        except Exception as e:
            QgsMessageLog.logMessage('SET PROPERTY ERROR: ' +  str(e), 'BubbleSymbolLayer')


        self.diagrammProps = None
        # self.labelsProps = None

        idx = 1000
        try:
            if len(self.diagrammStr) > 1:
                self.diagrammProps = ast.literal_eval(self.diagrammStr)
                for d in self.diagrammProps:
                    slices = d['slices']
                    if slices:
                        for slice in slices:
                            exp = slice['expression']
                            slice['expName'] = idx
                            self.attrsUsed.add(exp)
                            # self.dataDefinedProperties().setProperty(idx, QgsProperty.fromField(exp))
                            # self.setDataDefinedProperty(expName, QgsDataDefined(exp))
                            # if not self.dataDefinedProperties().hasProperty(idx):
                            #     self.dataDefinedProperties().setProperty(idx, QgsProperty.fromExpression('"{0}" + 0.0'.format(exp)))
                            #     self.setDataDefinedProperty(expName, QgsDataDefined('"{0}" + 0.0'.format(exp)))
                            idx = idx+1
                    if 'labels' in d:
                        labels = d['labels']
                        if labels:
                            for label in labels:
                                # expName = label['expName']
                                exp = label['expression']
                                label['expName'] = idx
                                self.attrsUsed.add(exp)
                                # self.dataDefinedProperties().setProperty(idx, QgsProperty.fromField(exp))
                                # self.setDataDefinedProperty(expName, QgsDataDefined(exp))
                                # if not self.dataDefinedProperties().hasProperty(idx):
                                #     self.dataDefinedProperties().setProperty(idx, QgsProperty.fromExpression('"{0}" + 0.0'.format(exp)))
                                #     self.setDataDefinedProperty(expName, QgsDataDefined('"{0}" + 0.0'.format(exp)))
                                idx = idx + 1

        except Exception as e:
            self.DEBUG and QgsMessageLog.logMessage('Evaluate diagram props: ' + str(e), 'BubbleSymbolLayer')

        self.DEBUG and QgsMessageLog.logMessage('{} rendered init in : {}'.format(self.__class__.__name__, str(datetime.now()-ts)), 'BubbleSymbolLayer')

        # try:
        #     if len(self.labelsStr) > 1:
        #         self.labelsProps = ast.literal_eval(self.labelsStr)
        #         for label in self.labelsProps:
        #             expName = str(idx) + '_labexpression'
        #             exp = label['expression']
        #             label['expName'] = expName
        #             self.setDataDefinedProperty(expName, QgsDataDefined('"{0}" + 0.0'.format(exp)))
        #             idx = idx+1
        # except Exception as e:
        #     QgsMessageLog.logMessage('Evaluate label props: ' + str(e), 'BubbleSymbolLayer')

        self.mXIndex = -1
        self.mYIndex = -1
        self.mDiagrammIndex = -1

        self.fields = None

    def layerType(self):
        return BubbleSymbolLayer.LAYERTYPE

    def bounds(self, point, context):
        res = super().bounds(point, context)
        return res

    def properties(self):
        props = { "showLineouts" : 'True' if self.showLineouts else 'False',
                 "showLabels" : 'True' if self.showLabels else 'False',
                 "showDiagramms" : 'True' if self.showDiagramms else 'False',
                 "labelSize" : str(self.labelSize),
                 "diagrammStr" : str(self.diagrammStr),
                 "templateStr": str(self.templateStr)}
                  # "labelDataSums": str(self.labelDataSums)}

        return props


    def stopRender(self, context):
        pass

    def drawPreview(self, painter, point, size):
        rect = QRectF(point, size)

        if self.showDiagramms:
            painter.setPen(Qt.black)
            painter.setBrush(QBrush(Qt.red))
            painter.drawPie(rect, 90 * 16, 180 * 16)
            painter.setBrush(QBrush(Qt.blue))
            painter.drawPie(rect, 270 * 16, 90 * 16)
            painter.setBrush(QBrush(Qt.green))
            painter.drawPie(rect, 360 * 16, 90 * 16)

        pt1 = QPointF(rect.center())
        pt2 = QPointF(pt1)
        pt3 = QPointF(rect.right(), pt1.y())

        if self.showLineouts:
            pen = QPen(Qt.black)
            pen.setWidth(1)
            pen.setCosmetic(True)
            painter.setPen(pen)
            
            pt3 = QPointF(rect.topRight())
            pt2 = QPointF((pt1.x()+pt3.x())/2, (pt1.y()+pt3.y())/2)
            pt3.setY(pt2.y())
            painter.drawLine(pt1, pt2)
            painter.drawLine(pt2, pt3)
            
            font = QFont("arial")
            font.setPointSizeF(qAbs(rect.top()-pt2.y()))
            painter.setFont(font)
            painter.drawText(pt2, u"1P")

    def addLabels(self, context, labelsProps):
        templateStr = u''
        if not labelsProps:
            return templateStr

        sum = 0.0
        for label in labelsProps:
            expName = label['expName']
            val = None
            if self.hasDataDefinedProperty(expName):
                (val, ok) = self.evaluateDataDefinedProperty(expName, context, 0.0)
                if type(val) is float:
                    sum = sum + float(val)

        for label in labelsProps:
            expName = label['expName']
            valStr = ''

            if self.hasDataDefinedProperty(expName):
                (val, ok) = self.evaluateDataDefinedProperty(expName, context, 0.0)
                if val is None or val == NULL:
                    break
                colorStr = label['color']
                showZero = label['showZero']
                isNewLine = label['isNewLine']

                # QgsMessageLog.logMessage(str(val), 'BubbleSymbolLayer')

                if type(val) is float:
                    formatString = "{:." + str(label['decimals']) + "f}"
                    if val != 0.0 or showZero:
                        if label['percent'] and sum != 0.0:
                            valStr = formatString.format(100.0 * float(val)/sum) + '%'
                        else:
                            valStr = formatString.format(float(val))
                else:
                    valStr = str(val)
            else:
                QgsMessageLog.logMessage('No DDF label ' + expName, 'BubbleSymbolLayer')

            if len(valStr):
                if isNewLine:
                    templateStr += '<div><span><font color="{0}">{1}</font></span></div>'.format(colorStr, valStr)
                else:
                    templateStr += '<span><font color="{0}">{1}</font></span>'.format(colorStr, valStr)

        templateStr = re.sub('^[\,\:\;\.\-/\\_ ]+|[\,\:\;\.\-/\\_ ]+$', '', templateStr)
        return templateStr

    def compileLabels(self, templateStr, sum, d, feature):
        self.DEBUG and QgsMessageLog.logMessage('compileLabels:', 'BubbleSymbolLayer') #DEBUG
        showZero = False
        decimals = d['decimals']
        formatString = "{:."+str(decimals)+"f}"

        days = feature["days"]
        if days:
            days = 1.0 / days

        slices = d['slices']
        multiplier = d['multiplier']
        dailyProduction = d['dailyProduction']
        for slice in slices:
            attr = slice['expression']
            colorStr = slice['labelColor']
            inPercent = slice['inPercent']
            strVal = '0'
            val = 0.0
            percentStr = ''
            if attr in templateStr:
                val = feature[attr]
                if val is not None and val != NULL:
                    if not inPercent:
                        val *= multiplier
                else:
                    val = 0
                if inPercent and sum != 0:
                    val = val / sum * 100
                    percentStr = '%'
                elif dailyProduction and days:
                    val *= days
                self.DEBUG and QgsMessageLog.logMessage('slice val={} :{}'.format(str(val),str(type(val))), 'BubbleSymbolLayer') #DEBUG
                strVal = formatString.format(val) + percentStr
            code = '"{0}"'.format(attr)
            if float(formatString.format(val)) != float(0) or showZero:
                templateStr = templateStr.replace(code, '<span><font color="{0}">{1}</font></span>'.format(colorStr,
                                                                                                           strVal))
            else:
                templateStr = templateStr.replace(code, '')

        templateStr = re.sub('^[\,\:\;\.\-/\\_ ]+|[\,\:\;\.\-/\\_ ]+$', '', templateStr)
        return templateStr
    
    def usedAttributes(self, context):
        res = super().usedAttributes(context)
        for f in self.attrsUsed:
            res.add(f)

        return res

    def renderPoint(self, point, context):
        feature = context.feature()
        p = context.renderContext().painter()

        if not feature: 
            '''
            If item not feature, then draw preview (symbol in legend or in style dock)
            '''
            labelSize = context.renderContext().convertToPainterUnits(self.size(), self.sizeUnit())
            self.drawPreview(p, QPointF(point.x() - labelSize / 2, point.y() - labelSize / 2), QSizeF(labelSize, labelSize))
            return

        ctx = context.renderContext()

        attrs = feature.attributes()

        labelTemplate = ''
        diagramms = []

        try:
            if self.diagrammProps and len(self.diagrammProps) > 0:
                '''
                 Get feature diagram size. New variant: from layer properties 
                '''
                size = float(feature.attribute(BubbleSymbolLayer.BUBBLE_SIZE))
                diagrammSize = ctx.convertToPainterUnits(size, QgsUnitTypes.RenderMillimeters)

                templateStr = self.templateStr
                self.DEBUG and QgsMessageLog.logMessage('#'*30, 'BubbleSymbolLayer') #DEBUG
                for d in self.diagrammProps:
                    self.DEBUG and QgsMessageLog.logMessage('*'*10, 'BubbleSymbolLayer') #DEBUG
                    slices = d['slices']
                    scaleType = int(d['scaleType'])
                    scaleMaxRadius = float(d['scaleMaxRadius'])
                    scaleMinRadius = float(d['scaleMinRadius'])
                    scale = float(d['scale'])
                    fixedSize = float(d['fixedSize'])
                    if slices and scale != 0.0:
                        koef = (scaleMaxRadius - scaleMinRadius) / scale
                        sum = 0.0
                        newSlices = []
                        for slice in slices:
                            expName = slice['expName']
                            val = feature.attribute(slice["expression"])
                            # if self.dataDefinedProperties().hasProperty(expName):
                            #     (val, ok) = self.evaluateDataDefinedProperty(expName, context, 0.0 )
                            if val and val != NULL:
                                self.DEBUG and QgsMessageLog.logMessage('val={},koef={},scale={} '.format(val, koef, scale), 'BubbleSymbolLayer') #DEBUG
                                sum = sum + val
                                bc = QgsSymbolLayerUtils.decodeColor(slice['backColor'])
                                lc = QgsSymbolLayerUtils.decodeColor(slice['lineColor'])
                                newSlice = DiagrammSlice(backColor=bc, lineColor=lc, percent=val)
                                newSlices.append(newSlice)
                            # else:
                            #     QgsMessageLog.logMessage('No DDF ' + str(expName), 'BubbleSymbolLayer')

                        if sum != 0.0:
                            ds = 0.0
                            if scaleType == 0:
                                ds = fixedSize
                            else:
                                ds = scaleMinRadius + sum * koef
                                self.DEBUG and QgsMessageLog.logMessage('ds={} '.format(ds), 'BubbleSymbolLayer') #DEBUG
                                if ds > scaleMaxRadius:
                                    ds = scaleMaxRadius
                                if ds < scaleMinRadius:
                                    ds = scaleMinRadius
                            for slice in newSlices:
                                slice.percent = slice.percent / sum

                            ds = ctx.convertToPainterUnits(ds, QgsUnitTypes.RenderMillimeters)
                            self.DEBUG and QgsMessageLog.logMessage('ds={} '.format(ds), 'BubbleSymbolLayer') #DEBUG
                            diagramm = DiagrammDesc(ds, newSlices, sum * koef )
                            diagramms.append(diagramm)

                    if 'labels' in d:
                        labels = d['labels']
                        self.DEBUG and QgsMessageLog.logMessage('labels: {}'.format(labels), 'BubbleSymbolLayer') #DEBUG
                        labelTemplate = labelTemplate + self.addLabels(context, labels)
                        templateStr = None
                    elif templateStr:
                        templateStr = self.compileLabels(templateStr, sum, d, feature)

                # QgsMessageLog.logMessage(templateStr, 'BubbleSymbolLayer')
                #
                # labelTemplate = feature.attribute(BubbleSymbolLayer.DIAGRAMM_LABELS)
                # if labelTemplate == NULL:
                #     labelTemplate = ''
                # labelTemplate = self.addLabels(context)
                if templateStr:
                    labelTemplate = templateStr


            elif self.mDiagrammIndex >= 0:
                '''
                 Get feature diagram size. Old variant: from Field with XML
                '''

                xmlString = attrs[self.mDiagrammIndex]
                if not xmlString:
                    QgsMessageLog.logMessage('No diagramm ' + ','.join([str(attr) for attr in attrs]),
                                             'BubbleSymbolLayer')
                    return

                root = ET.fromstring(xmlString)

                for diag in root.findall('diagramm'):
                    size = str(diag.attrib['size'])
                    diagrammSize = ctx.convertToPainterUnits(float_t(size), QgsUnitTypes.RenderMillimeters)

                    if diagrammSize > 0:
                        slices = []
                        for values in diag.findall('value'):
                            bc = QgsSymbolLayerUtils.decodeColor(values.attrib['backColor'])
                            lc = QgsSymbolLayerUtils.decodeColor(values.attrib["lineColor"])
                            prnc = float_t(values.text)
                            # fn = values.attrib["fieldName"]
                            # slice = DiagrammSlice(backColor=bc, lineColor=lc, percent=prnc, fieldName=fn)
                     
                            slice = DiagrammSlice(backColor=bc, lineColor=lc, percent=prnc)
                            slices.append(slice)

                        diagramm = DiagrammDesc(diagrammSize, slices)
                        diagramms.append(diagramm)

                for label in root.findall('label'):
                    labelTemplate = label.attrib['labelText']
            '''
            Draw diagram for current feature
            '''
            diagramms = sorted(diagramms, key=lambda diagramm: [diagramm.mDiagrammSize,diagramm.mRealSize], reverse=True)
            self.DEBUG and QgsMessageLog.logMessage("\n".join(map(str,diagramms)), 'BubbleSymbolLayer') #DEBUG
            if self.showDiagramms:
                for idx,desc in enumerate(diagramms):
                    #--- Fix for diagramms with identicaly size
                    if diagramms[idx-1].mDiagrammSize==desc.mDiagrammSize or (idx>0 and diagramms[idx-1].mDiagrammSize<desc.mDiagrammSize):
                        desc.mDiagrammSize=desc.mDiagrammSize*0.8
                        if desc.mDiagrammSize<=0:desc.mDiagrammSize=1
                    self.DEBUG and QgsMessageLog.logMessage("diagram {} size:{}".format(str(idx),str(desc.mDiagrammSize)), 'BubbleSymbolLayer') #DEBUG
                    rect = QRectF(point, QSizeF(desc.mDiagrammSize, desc.mDiagrammSize))
                    rect.translate(-desc.mDiagrammSize / 2, -desc.mDiagrammSize / 2)
                    startAngle = 90.0
                    count = len(desc.mSlices)
                    for slice in desc.mSlices:
                        color = QColor(slice.backColor)
                        p.setBrush(QBrush(color))

                        color = QColor(slice.lineColor)
                        p.setPen(color)

                        spanAngle = 360 * slice.percent
                        if count > 1:
                            p.drawPie(rect, startAngle * 16, spanAngle * 16)
                        else:
                            p.drawEllipse(rect)

                        startAngle = startAngle + spanAngle

            '''
            Draw diagram label for current feature
            '''
            labelSize = ctx.convertToPainterUnits(self.labelSize, QgsUnitTypes.RenderPixels)

            font = QFont()
            font.setPointSizeF(labelSize);
            p.setFont(font)

            if self.mXIndex >= 0 and self.mYIndex >= 0:
                xVal = 0.0
                yVal = 0.0
                if attrs[self.mXIndex]:
                    xVal = ctx.convertToPainterUnits(float(attrs[self.mXIndex]), QgsUnitTypes.RenderMillimeters)
                if attrs[self.mYIndex]:
                    yVal = ctx.convertToPainterUnits(float(attrs[self.mYIndex]), QgsUnitTypes.RenderMillimeters)
                widthVal = 10

                #if xVal != 0 or yVal != 0:
                pt1 = point + QPointF(xVal, yVal)
                
                st = QStaticText(labelTemplate);
                opt = st.textOption()
                opt.setWrapMode(QTextOption.NoWrap)
                st.setTextOption(opt)
                st.prepare(p.transform(), p.font())
                widthVal = st.size().width()
                
                pt2 = point + QPointF(xVal + widthVal, yVal)

                pen = QPen(Qt.black)
                pen.setWidth(2)
                p.setPen(pen)
                if point.x() < (pt1.x() + pt2.x()) / 2 :
                    if self.showLineouts:
                        p.drawLine(point, pt1)
                        p.drawLine(pt1, pt2)
                    if labelTemplate and labelTemplate != NULL and self.showLabels:
                        p.drawStaticText(pt1.x(), pt1.y(), st)
                else:
                    if self.showLineouts:
                        p.drawLine(point, pt2)
                        p.drawLine(pt2, pt1)
                    if labelTemplate and labelTemplate != NULL and self.showLabels:
                        p.drawStaticText(pt1.x(), pt1.y(), st)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            QgsMessageLog.logMessage('renderPoint: {} {} {} {}'.format(str(e),exc_type, fname, exc_tb.tb_lineno), 'BubbleSymbolLayer')


    def startRender(self, context):
        super().startRender(context)

        self.fields = context.fields()
        self.attrsUsed = []
        if self.fields:
            self.mXIndex = self.fields.lookupField("labloffx")    #LablOffX
            self.mYIndex = self.fields.lookupField("labloffy")    #LablOffY
            self.mDiagrammIndex = self.fields.lookupField(OLD_NEW_FIELDNAMES[0])
            if self.mDiagrammIndex < 0:
                self.mDiagrammIndex = self.fields.lookupField(OLD_NEW_FIELDNAMES[1])
        else:
            self.mXIndex = -1
            self.mYIndex = -1
            self.mDiagrammIndex= -1

        self.prepareExpressions(context)

    def clone(self):
        m = BubbleSymbolLayer(self.properties())
        self.copyDataDefinedProperties(m);
        self.copyPaintEffect(m);
        return m

    def create(props):
        QgsMessageLog.logMessage('Creating', 'BubbleSymbolLayer')
        return BubbleSymbolLayer(props)

    def toSld(self, doc, element, props):
        QgsMessageLog.logMessage('toSld', 'BubbleSymbolLayer')
        super().toSld(doc, element, props)

    def writeSldMarker(self, doc, element, props):
        QgsMessageLog.logMessage('writeSldMarker', 'BubbleSymbolLayer')
        super().writeSldMarker(doc, element, props)

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'qgis_pds_renderer_base.ui'))

class BabbleSymbolLayerWidget(QgsSymbolLayerWidget, FORM_CLASS):
    def __init__(self, parent=None, vectorLayer = None):
        super().__init__(parent, vectorLayer)

        self.setupUi(self)

        self.DEBUG = False
        self.layer = None
        self.expressionIndex = 0


    def setSymbolLayer(self, layer):
        if layer.layerType() != BubbleSymbolLayer.LAYERTYPE:
            return

        self.layer = layer
        self.showLineouts.setChecked(layer.showLineouts)
        self.showLabels.setChecked(layer.showLabels)
        self.showDiagramms.setChecked(layer.showDiagramms)
        self.mLabelSizeSpinBox.setValue(layer.labelSize)
        self.editTemplateStr.setText(layer.templateStr)
        self.editDiagrammStr.setPlainText(layer.diagrammStr)

    def symbolLayer(self):
        return self.layer
    
    def on_editTemplateStr_txt_changed(self,val):
        self.DEBUG and QgsMessageLog.logMessage('on_editTemplateStr_txt_changed', 'BubbleSymbolLayer')
        self.layer.templateStr=val
        self.changed.emit()
        pass

    def on_editDiagrammStr_txt_changed(self):
        self.DEBUG and QgsMessageLog.logMessage('on_editDiagrammStr_txt_changed', 'BubbleSymbolLayer')
        self.layer.diagrammStr=self.editDiagrammStr.toPlainText()
        self.changed.emit()

    def on_showLineouts_toggled(self, value):
        self.DEBUG and QgsMessageLog.logMessage('on_showLineouts_toggled', 'BubbleSymbolLayer')
        self.layer.showLineouts = value
        self.changed.emit()

    def on_showLabels_toggled(self, value):
        self.DEBUG and QgsMessageLog.logMessage('on_showLabels_toggled', 'BubbleSymbolLayer')
        self.layer.showLabels = value
        self.changed.emit()

    def on_showDiagramms_toggled(self, value):
        self.DEBUG and QgsMessageLog.logMessage('on_showDiagramms_toggled', 'BubbleSymbolLayer')
        self.layer.showDiagramms = value
        self.changed.emit()

    @pyqtSlot(float)
    def on_mLabelSizeSpinBox_valueChanged(self, value):
        self.DEBUG and QgsMessageLog.logMessage('on_mLabelSizeSpinBox_valueChanged', 'BubbleSymbolLayer')
        self.layer.labelSize = value
        self.changed.emit()


class BabbleSymbolLayerMetadata(QgsSymbolLayerAbstractMetadata):

    def __init__(self):
        super().__init__(BubbleSymbolLayer.LAYERTYPE, u"Круговые диаграммы PDS", QgsSymbol.Marker)

    def createSymbolLayer(self, props):
        return BubbleSymbolLayer(props)

    def createSymbolLayerWidget(self, vectorLayer):
        return BabbleSymbolLayerWidget(None, vectorLayer)




