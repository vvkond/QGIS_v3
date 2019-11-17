# -*- coding: utf-8 -*-
import random
from qgis.core import QgsWkbTypes, QgsSymbol, QgsFeatureRenderer, QgsRendererAbstractMetadata, QgsRendererRegistry, QgsApplication
from qgis.gui import QgsRendererWidget, QgsColorButton
from qgis.PyQt.QtWidgets import *


class BubbleFeatureRenderer(QgsFeatureRenderer):
    def __init__(self, syms=None):
        super().__init__("BubbleFeatureRenderer")

        self.syms = syms if syms else [QgsSymbol.defaultSymbol(QgsWkbTypes.geometryType(QgsWkbTypes.Point))]

    def symbolForFeature(self, feature, context):
        return random.choice(self.syms)

    def startRender(self, context, fields):
        for s in self.syms:
            s.startRender(context)

    def stopRender(self, context):
        for s in self.syms:
            s.stopRender(context)

    def usedAttributes(self, context):
        return []

    def clone(self):
        return BubbleFeatureRenderer(self.syms)


class BubbleFeatureRendererWidget(QgsRendererWidget):
    def __init__(self, layer, style, renderer):
        super().__init__(layer, style)
        if renderer is None or renderer.type() != "BubbleFeatureRenderer":
            self.r = BubbleFeatureRenderer()
        else:
            self.r = renderer.clone()

        # setup UI
        self.btn1 = QgsColorButton()
        self.btn1.setColor(self.r.syms[0].color())
        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.btn1)
        self.setLayout(self.vbox)
        self.btn1.colorChanged.connect(self.colorChanged)

    def colorChanged(self, color):
        # color = QColorDialog.getColor(self.r.syms[0].color(), self)
        # if not color.isValid(): return

        self.r.syms[0].setColor(color)
        # self.btn1.setColor(self.r.syms[0].color())

    def renderer(self):
        return self.r


class BubbleFeatureRendererMetadata(QgsRendererAbstractMetadata):
    def __init__(self):
        super().__init__("BubbleFeatureRenderer", "renderer PUMA+")

    def createRenderer(self, element):
        return BubbleFeatureRenderer()

    def createRendererWidget(self, layer, style, renderer):
        return BubbleFeatureRendererWidget(layer, style, renderer)

