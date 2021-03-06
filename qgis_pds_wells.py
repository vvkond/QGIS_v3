# -*- coding: utf-8 -*-

from qgis.core import *
from qgis.gui import *
from qgis.PyQt import QtGui
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from QgisPDS.db import Oracle
from QgisPDS.connections import create_connection
from QgisPDS.utils import to_unicode
from .tig_projection import *
import ast
import os
import time
# from processing.tools.vector import VectorWriter
from qgis.core import QgsVectorFileWriter, QgsWkbTypes
from .bblInit import STYLE_DIR, Fields, FieldsWellLayer,\
    FieldsForLabels,\
    set_QgsPalLayerSettings_datadefproperty, layer_to_labeled,\
    setLayerFieldsAliases
from .utils import plugin_path, load_styles_from_dir, load_style, edit_layer, memoryToShp

debuglevel = 4

def debug(msg, verbosity=1):
    if debuglevel >= verbosity:
        try:
            qDebug(msg)
        except:
            pass

class QgisPDSWells(QObject):

    def __init__(self, iface, project ,styleName=None ,styleUserDir=None):
        super(QgisPDSWells, self).__init__()

        self.plugin_dir = os.path.dirname(__file__)
        self.iface = iface
        self.project = project
        self.dateFormat = u'dd-MM-yyyy'

        self.proj4String = QgisProjectionConfig.get_default_layer_prj_epsg()
        self.db = None
        self.wellIdList = []
        
        self.styleName=styleName
        self.styleUserDir=styleUserDir
        

    def setWellList(self, wellList):
        self.wellIdList = wellList

    def createWellLayer(self):
        if not self.initDb():
            return

        self.uri = "Point?crs={}".format(self.proj4String)
        for field in FieldsWellLayer:
            self.uri += field.memoryfield
        for field in FieldsForLabels:
            self.uri += field.memoryfield

        layer = QgsVectorLayer(self.uri, "PDS Wells", "memory")
        if layer is None:
            QMessageBox.critical(None, self.tr(u'Error'), self.tr(
                u'Error create wells layer'), QMessageBox.Ok)

            return
        
        #---load user styles
        if self.styleUserDir is not None:
            load_styles_from_dir(layer=layer, styles_dir=os.path.join(plugin_path() ,STYLE_DIR, self.styleUserDir) ,switchActiveStyle=False)
        #---load default style
        if self.styleName is not None:
            load_style(layer=layer, style_path=os.path.join(plugin_path() ,STYLE_DIR ,self.styleName+".qml"))

        
        self.loadWells(layer, True, True, False, True, False)
        layer.commitChanges()
        self.db.disconnect()

        layerName = 'PDS Wells'
        layer = memoryToShp(layer, self.project['project'], layerName)

        # layer.startEditing()
        layer.setCustomProperty("qgis_pds_type", "pds_wells")
        layer.setCustomProperty("pds_project", str(self.project))

        palyr = QgsPalLayerSettings()
        # palyr.readFromLayer(layer)
        palyr.fieldName = Fields.WellId.name
        palyr=layer_to_labeled(palyr)  #---enable EasyLabel
        palyr = QgsVectorLayerSimpleLabeling(palyr)
        layer.setLabelsEnabled(True)
        layer.setLabeling(palyr)

        # layer.commitChanges()
        setLayerFieldsAliases(layer)

        QgsProject.instance().addMapLayer(layer)

        return layer

    def initDb(self):
        if self.project is None:
            QgsMessageLog.logMessage(self.tr(u'No current PDS project'), tag="QgisPDS.error")
            self.iface.messageBar().pushCritical(self.tr("Error"),
                self.tr(u'No current PDS project'))

            return False

        connection = create_connection(self.project)
        scheme = self.project['project']
        try:
            self.db = connection.get_db(scheme)
            self.tig_projections = TigProjections(db=self.db)
            proj = self.tig_projections.get_projection(self.tig_projections.default_projection_id)
            if proj is not None:
                self.proj4String = 'PROJ4:' + proj.qgis_string
                destSrc = QgsCoordinateReferenceSystem()
                destSrc.createFromProj4(proj.qgis_string)
                sourceCrs = QgsCoordinateReferenceSystem(QgisProjectionConfig.get_default_latlon_prj_epsg())
                #self.xform = QgsCoordinateTransform(sourceCrs, destSrc)
                self.xform=get_qgis_crs_transform(sourceCrs,destSrc,self.tig_projections.fix_id)
        except Exception as e:
            QgsMessageLog.logMessage(self.tr(u'Project projection read error {0}: {1}').format(scheme, str(e)), tag="QgisPDS.error")
            self.iface.messageBar().pushCritical(self.tr("Error")
                                                ,self.tr(u'Project projection read error {0}: {1}').format(scheme, str(e)))
            return False
        return True

    def get_sql(self, value):
        sql_file_path = os.path.join(self.plugin_dir, 'db', value)
        with open(sql_file_path, 'rb') as f:
            return f.read().decode('utf-8')

    def checkWell(self, well_name):
        sql = ("SELECT db_sldnid FROM tig_well_history WHERE rtrim(tig_latest_well_name) = '" + well_name + "' ")

        records = self.db.execute(sql)
        num = 0
        if records:
            for r in records:
                num += 1

        return num


    def loadWells(self, layer, isRefreshKoords, isRefreshData, isSelectedOnly, isAddMissing, isDeleteMissing, filterWellIds=None):
        if self.db is None and layer:
            # prjStr = layer.customProperty("pds_project")
            # self.project = ast.literal_eval(prjStr)
            if not self.initDb():
                return

        if isDeleteMissing:
            deletedWells = []
            with edit_layer(layer):
                for f in layer.getFeatures():
                    well_name = f.attribute(Fields.WellId.name)
                    well_id = f.attribute(Fields.Sldnid.name)
                    if (filterWellIds is not None) and (well_id not in filterWellIds):
                        deletedWells.append(well_name)
                        layer.deleteFeature(f.id())
                    elif self.checkWell(well_name) < 1:
                        deletedWells.append(well_name)
                        layer.deleteFeature(f.id())
            if len(deletedWells):
                s = self.tr('Deleted from layer') + ': ' + ','.join(str(s) for s in deletedWells)
                QMessageBox.warning(None, self.tr(u'Warning'), s, QMessageBox.Ok)

        dbWells = self._readWells()
        if dbWells is None:
            return

        projectName = self.project['project']

        allWells = len(self.wellIdList) < 1

        refreshed = False
        with edit_layer(layer):
            for row in dbWells:
                name= row[0]
                lng = row[20]
                lat = row[19]
                wellId = int(row[1])
                if (filterWellIds is not None) and (wellId not in filterWellIds):
                    continue
                elif lng and lat and (allWells or wellId in self.wellIdList):
                    pt = QgsPointXY(lng, lat)
                    
                    if self.xform:
                        pt = self.xform.transform(pt)

                    geom = QgsGeometry.fromPointXY(pt)

                    num = 0
                    well = None
                    if isSelectedOnly:
                        searchRes = layer.selectedFeatures()
                        for f in searchRes:
                            if f.attribute(Fields.WellId.name) == name:
                                well = f
                                if isRefreshKoords:
                                    layer.changeGeometry(f.id(), geom)
                                    well.setGeometry(geom)
                                num = num + 1
                                break
                    else:
                        args = (Fields.WellId.name, name)
                        expr = QgsExpression('\"{0}\"=\'{1}\''.format(*args))
                        searchRes = layer.getFeatures(QgsFeatureRequest(expr))
                        for f in searchRes:
                            refreshed = True
                            well = f
                            if isRefreshKoords:
                                layer.changeGeometry(f.id(), geom)
                                well.setGeometry(geom)
                            num = num + 1

                    if not well and isAddMissing:
                        well = QgsFeature(layer.fields())

                    if well:
                        well.setAttribute(Fields.WellId.name, name)
                        well.setAttribute(Fields.Latitude.name, lat)
                        well.setAttribute(Fields.Longitude.name, lng)

                        well.setAttribute(Fields.Sldnid.name, row[1])
                        well.setAttribute(Fields.Api.name, row[2])
                        well.setAttribute(Fields.Operator.name, row[3])
                        well.setAttribute(Fields.Country.name, row[4])
                        well.setAttribute(Fields.Depth.name, row[7])
                        try:
                            well.setAttribute(Fields.ElevationPoint.name, row[8])
                        except: #Format before shapes
                            well.setAttribute('measurement', row[8])
                        well.setAttribute(Fields.Elevation.name, row[9])
                        well.setAttribute(Fields.EleationvDatum.name, row[10])
                        try:
                            well.setAttribute(Fields.OnOffShor.name, row[11])
                        except: #Format before shapes
                            well.setAttribute('on_offshore', row[11])
                        well.setAttribute(Fields.TigLatestWellState.name, row[12])
                        well.setAttribute(Fields.TigWellSymbol.name, row[13])
                        well.setAttribute(Fields.SpudDate.name, str(row[14]))
                        try:
                            well.setAttribute(Fields.IsGlobal.name, row[15])
                        except: #Format before shapes
                            well.setAttribute('global_private', row[15])
                        well.setAttribute(Fields.Owner.name, row[16])
                        well.setAttribute(Fields.CreatedDT.name, QDateTime.fromTime_t(0).addSecs(int(row[17])))
                        well.setAttribute(Fields.Project.name, projectName)

                        if not num:
                            if not isSelectedOnly:
                                if lat != 0 or lng != 0:
                                    well.setGeometry(geom)
                                    layer.addFeatures([well])
                        elif isRefreshData:
                            layer.updateFeature(well)
        if refreshed:
            self.iface.messageBar().pushMessage(self.tr(u'Layer: {0} refreshed').format(layer.name), duration=10)

        layer.updateExtents()


    def _readWells(self):
        try:
            return self.db.execute(self.get_sql('Wells.sql'))
        except Exception as e:
            self.iface.messageBar().pushCritical(self.tr("Error"), str(e))
            return None


