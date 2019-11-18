# -*- coding: utf-8 -*-
import random
from qgis.core import *
from qgis.gui import QgsRendererWidget, QgsColorButton
from qgis.PyQt.QtWidgets import *


class BubbleFeatureRenderer(QgsFeatureRenderer):
    def __init__(self, syms=None):
        super().__init__("BubbleFeatureRenderer")

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
        return BubbleFeatureRenderer(self.mSymbol.clone())

    def save(self, doc, context):
        QgsMessageLog.logMessage('save', 'BubbleFeatureRenderer')

        rendererElem = doc.createElement('renderer-v2')

        rendererElem.setAttribute('forceraster', '0')
        rendererElem.setAttribute('type', 'BubbleFeatureRenderer')

        return rendererElem


class BubbleFeatureRendererWidget(QgsRendererWidget):
    def __init__(self, layer, style, renderer):
        super().__init__(layer, style)
        if renderer is None or renderer.type() != "BubbleFeatureRenderer":
            self.r = BubbleFeatureRenderer()
        else:
            self.r = renderer.clone()

        # setup UI
        self.btn1 = QgsColorButton()
        self.btn1.setColor(self.r.mSymbol.color())
        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.btn1)
        self.setLayout(self.vbox)
        self.btn1.colorChanged.connect(self.colorChanged)

    def colorChanged(self, color):
        self.r.mSymbol.setColor(color)


    def renderer(self):
        return self.r


class BubbleFeatureRendererMetadata(QgsRendererAbstractMetadata):
    def __init__(self):
        super().__init__("BubbleFeatureRenderer", "PUMA+ Bubble renderer")

    def createRenderer(self, domElement, context):
        return BubbleFeatureRenderer()

    def createRendererWidget(self, layer, style, oldRenderer):
        return BubbleFeatureRendererWidget(layer, style, oldRenderer)


# QgsApplication.rendererRegistry().addRenderer(BubbleFeatureRendererMetadata())