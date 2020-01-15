# -*- coding: utf-8 -*-

from qgis.core import *
from qgis.gui import QgsMessageBar
from qgis.PyQt.QtWidgets import *
from PyQt5 import QtGui, uic
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import numpy
from QgisPDS.connections import create_connection
from .utils import *
from .tig_projection import *
from .CornerPointGrid import *

class SimulationLink:
    def __init__(self, mnemonic, coordinate, simSldnam, simFldnam, simRunFldnam):
        self.mnemonic = mnemonic
        self.coordinate = coordinate
        self.simSldnam = simSldnam
        self.simFldnam = simFldnam
        self.simRunFldnam = simRunFldnam


PORO = 'Porosity'
XPERM = 'Permeability in x direction'
YPERM = 'Permeability in y direction'
ZPERM = 'Permeability in z direction'
NTG = 'Cell net to gross ratio'
GASSAT = 'Gas saturation for grid block'
WATSAT = 'Water saturation for grid block'
PBUB = 'Bubble point pressures'
MPBUB = 'Minimum bubble point pressures'
OGR = 'Initial oil/gas ratios'
MOGR = 'Minimum oil/gas ratio'
MNWSAT = 'Minimum water saturation'

CORNER_POINT = 2
FULL_CORNER_POINT = 4
SIM_INDT = -999

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'qgis_pds_modelDialog_base.ui'))

class QgisPDSModel3DDialog(QDialog, FORM_CLASS):
    """Constructor."""
    def __init__(self, _iface, _project, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.simLinks = {
            PORO: SimulationLink(PORO, False, "tig_sim_geom_data",
             "tig_cell_porosity",
             "tig_geom_data_vrsn_no"),

            XPERM: SimulationLink(XPERM, False, "tig_sim_geom_data",
             "tig_x_permeability",
             "tig_geom_data_vrsn_no"),

            YPERM: SimulationLink(YPERM, False, "tig_sim_geom_data",
             "tig_y_permeability",
             "tig_geom_data_vrsn_no"),

            ZPERM: SimulationLink(ZPERM, False, "tig_sim_geom_data",
             "tig_z_permeability",
             "tig_geom_data_vrsn_no"),

            # SimulationLink(PBUB, False, "tig_sim_black_oil_equil",
            #  "tig_bubble_pnt_pres",
            #  "tig_black_oil_equil_nos"),
            #
            # SimulationLink(MPBUB, False, "tig_sim_black_oil_equil",
            #  "tig_min_bubble_pnt_pres",
            #  "tig_black_oil_equil_nos"),
            #
            # SimulationLink(MNWSAT, False, "tig_sim_satn_data",
            #  "tig_min_h2o_satns",
            #  "tig_satn_data_vrsn_no"),

            # SimulationLink(MXWSAT, False, "tig_sim_satn_data",
            #  "tig_max_h2o_satns",
            #  "tig_satn_data_vrsn_no"),

            # SimulationLink(OGR, False, "tig_sim_black_oil_equil",
            #  "tig_init_vap_og_ratio",
            #  "tig_black_oil_equil_nos"),
            #
            # SimulationLink(MOGR, False, "tig_sim_black_oil_equil",
            #  "tig_min_vap_og_ratio",
            #  "tig_black_oil_equil_nos"),

            NTG: SimulationLink(NTG, False, "tig_sim_geom_data",
             "tig_net_to_gross_ratio",
             "tig_geom_data_vrsn_no"),

            GASSAT: SimulationLink(GASSAT, False, "tig_sim_geom_data",
             "tig_geom_vap_saturation",
             "tig_geom_data_vrsn_no"),

            WATSAT: SimulationLink(WATSAT, False, "tig_sim_geom_data",
             "tig_geom_aqu_saturation",
             "tig_geom_data_vrsn_no"),

            # SimulationLink(TOPDEP, True, "tig_sim_model",
            #  "tig_cell_z_map_coord",
            #  ""),
            #
            # SimulationLink(CTRDEP, True, "tig_sim_model",
            #  "tig_cell_z_map_coord",
            #  ""),
            #
            # SimulationLink(BOTDEP, True, "tig_sim_model",
            #  "tig_cell_z_map_coord",
            #  ""),
            #
            # SimulationLink(TTVDSS, True, "tig_sim_model",
            #  "tig_cell_z_map_coord",
            #  ""),
            #
            # SimulationLink(BTVDSS, True, "tig_sim_model",
            #  "tig_cell_z_map_coord",
            #  ""),
            #
            # SimulationLink(GRT, False, "tig_sim_model",
            #  "tig_cell_delta_z",
            #  "")
        }

        self.plugin_dir = os.path.dirname(__file__)
        self.project = _project
        self.iface = _iface
        self.initialized = False
        self.db = None
        if not self.initDb():
            return

        self.curModelNo = -1
        self.curPropKey = ''
        self.curModelNo,self.curPropKey, layerNo = self.readSettings()

        self.fillModelList()
        self.layerSpinBox.setValue(layerNo)


    def initDb(self):
        if self.project is None:
            self.iface.messageBar().pushCritical(self.tr("Error"),
                self.tr(u'Не выбран проект PDS'))

            return False

        connection = create_connection(self.project)
        scheme = self.project['project']
        self.proj4String = QgisProjectionConfig.get_default_layer_prj_epsg()
        try:
            self.db = connection.get_db(scheme)

            self.tig_projections = TigProjections(db=self.db)
            proj = self.tig_projections.get_projection(self.tig_projections.default_projection_id)
            if proj is not None:
                self.proj4String = 'PROJ4:' + proj.qgis_string
                destSrc = QgsCoordinateReferenceSystem()
                destSrc.createFromProj4(proj.qgis_string)
                sourceCrs = None
                self.xform = get_qgis_crs_transform(sourceCrs, destSrc, self.tig_projections.fix_id)
        except Exception as e:
            self.iface.messageBar().pushCritical(self.tr("Error"),
                                                self.tr(u'Project projection read error {0}: {1}').format(
                                                    scheme, str(e)))
            return False
        return True

    def fillModelList(self):
        self.modelListWidget.clear()

        sql = 'select tig_simultn_model_no, tig_description from TIG_SIM_MODEL'
        records = self.db.execute(sql)
        if records:
            for input_row in records:
                item = QListWidgetItem(input_row[1])
                item.setData(Qt.UserRole, input_row[0])
                self.modelListWidget.addItem(item)
                if input_row[0] == self.curModelNo:
                    self.modelListWidget.setCurrentItem(item)

    def fillParamList(self, model_no):
        self.propertyListWidget.clear()

        for key in self.simLinks:
            sl = self.simLinks[key]
            sql = 'select count(*) from ' + sl.simSldnam + ' where tig_simultn_model_no='+str(model_no)
            records = self.db.execute(sql)
            if records:
                for input_row in records:
                    if input_row[0] > 0:
                        item = QListWidgetItem(sl.mnemonic)
                        self.propertyListWidget.addItem(item)
                        if key == self.curPropKey:
                            self.propertyListWidget.setCurrentItem(item)
                    break

    def on_modelListWidget_currentItemChanged(self, current, previous):
        model_no = current.data(Qt.UserRole)

        nx, ny, nz = self.readGridInfo(model_no)
        self.layerSpinBox.setMaximum(nz)
        self.layerLabel.setText(self.tr('Слой') + ' (1:{0})'.format(nz))

        self.fillParamList(model_no)

    def on_buttonBox_accepted(self):
        if not self.propertyListWidget.currentItem() or not self.modelListWidget.currentItem():
            QMessageBox.critical(None, self.tr(u'Ошибка'), self.tr('Не выбрана модель или параметр'), QMessageBox.Ok)
            return

        self.saveSettings()

        model_no = self.modelListWidget.currentItem().data(Qt.UserRole)

        key = self.propertyListWidget.currentItem().text()
        sl = self.simLinks[key]

        grid = self.readGrid(model_no, self.modelListWidget.currentItem().text())
        if not grid:
            QMessageBox.critical(None, self.tr(u'Ошибка'), self.tr('Ошибка загрузки модели'), QMessageBox.Ok)
            return

        self.readPropertyCube(grid, sl)
        self.gridToLayer(grid, self.layerSpinBox.value()-1)

    def readGridInfo(self, modelId):
        sql = 'select tig_simultn_model_no, tig_model_def_sldnid, tig_radial_geometry, tig_geometry_type, ' \
              'tig_cells_in_x_or_r_dir, tig_cells_in_y_or_0_dir, tig_cells_in_z_dir ' \
              'from TIG_SIM_MODEL where tig_simultn_model_no = ' + str(modelId)
        records = self.db.execute(sql)
        if records:
            for input_row in records:
                nCellsX = input_row[4]
                nCellsY = input_row[5]
                nCellsZ = input_row[6]
                return (nCellsX, nCellsY, nCellsZ)

        return (0, 0, 0)

    def readGrid(self, modelId, modelName):
        sql = 'select tig_simultn_model_no, tig_model_def_sldnid, tig_radial_geometry, tig_geometry_type, ' \
              'tig_cells_in_x_or_r_dir, tig_cells_in_y_or_0_dir, tig_cells_in_z_dir ' \
              'from TIG_SIM_MODEL where tig_simultn_model_no = ' + str(modelId)
        records = self.db.execute(sql)
        if records:
            for input_row in records:
                gridSld = input_row[1]
                geometryType = input_row[2]
                nCellsX = input_row[4]
                nCellsY = input_row[5]
                nCellsZ = input_row[6]

                coordLinesCount = 2 * (nCellsX + 1) * (nCellsY + 1)
                cornerPointsCount = 8 * nCellsX * nCellsY * nCellsZ

                sql = 'select tig_cell_x_map_coord, tig_cell_y_map_coord, tig_cell_z_map_coord from tig_sim_grid_defn ' \
                      'where db_sldnid = ' + str(gridSld)

                grid_records = self.db.execute(sql)
                for row in grid_records:
                    grid = CornerPointGrid(modelId, nCellsX, nCellsY, nCellsZ)
                    grid.layerName = modelName

                    grid.XCoordLine = numpy.fromstring(self.db.blobToString(row[0]), '>f').astype('d')
                    grid.YCoordLine = numpy.fromstring(self.db.blobToString(row[1]), '>f').astype('d')
                    grid.ZCoordLine = numpy.fromstring(self.db.blobToString(row[2]), '>f').astype('d')
                    if ((geometryType != CORNER_POINT and geometryType != FULL_CORNER_POINT)
                            or len(grid.XCoordLine) != coordLinesCount
                            or len(grid.YCoordLine) != coordLinesCount
                            or len(grid.ZCoordLine) != coordLinesCount + cornerPointsCount):
                        break

                    return grid

        return None

    def readPropertyCube(self, grid, simLink):
        sql = 'select ' + simLink.simFldnam + ' from ' + simLink.simSldnam + ' where tig_simultn_model_no='+str(grid.model_no)
        records = self.db.execute(sql)
        if records:
            for row in records:
                grid.cube = numpy.fromstring(self.db.blobToString(row[0]), '>f').astype('d')
                grid.cubeMin = numpy.amin(grid.cube)
                grid.cubeMax = numpy.amax(grid.cube)
                break

    def gridToLayer(self, grid, layer):
        if not grid:
            return

        uri = "Polygon?crs={}".format(self.proj4String)
        uri += '&field={}:{}'.format('layer', "int")
        uri += '&field={}:{}'.format('value', "double")
        mapLayer = QgsVectorLayer(uri, grid.layerName, "memory")

        istart = grid.nCellsX * grid.nCellsY * layer
        useCube = grid.cube is not None and len(grid.cube) > istart

        mapLayer.startEditing()
        for i in range(1, grid.nCellsX):
            for j in range(1, grid.nCellsY):
                x1,y1, x2,y2, x3,y3, x4,y4 = grid.getPolygon(i, j, layer);
                pt1 = QgsPointXY(x1, y1)
                pt2 = QgsPointXY(x2, y2)
                pt3 = QgsPointXY(x3, y3)
                pt4 = QgsPointXY(x4, y4)
                if self.xform:
                    pt1 = self.xform.transform(pt1)
                    pt2 = self.xform.transform(pt2)
                    pt3 = self.xform.transform(pt3)
                    pt4 = self.xform.transform(pt4)
                cPoint = QgsFeature(mapLayer.fields())
                cPoint.setGeometry(QgsGeometry.fromPolygonXY([[pt1, pt2, pt3, pt4]]))
                cPoint.setAttribute('layer', layer)
                try:
                    if useCube:
                        val = grid.cube[istart + (j-1)*grid.nCellsX + i - 1]
                        cPoint.setAttribute('value', float(val))
                    else:
                        cPoint.setAttribute('value', SIM_INDT)
                except:
                    pass
                mapLayer.addFeatures([cPoint])

        mapLayer.commitChanges()

        shpLayer = memoryToShp(mapLayer, self.project['project'], grid.layerName+'_layer_'+str(layer+1))

        if useCube:
            myStyle = QgsStyle().defaultStyle()
            ramp = myStyle.colorRamp('Spectral')

            intervals =QgsGraduatedSymbolRenderer.calcEqualIntervalBreaks(grid.cubeMin, grid.cubeMax, 10, False, 0, False)
            count = len(intervals)
            num = 0.0
            myRangeList = []
            minVal = grid.cubeMin
            for maxVal in intervals:
                mySymbol1 = QgsSymbol.defaultSymbol(shpLayer.geometryType())
                clr = ramp.color(num / count)
                mySymbol1.setColor(clr)

                myRange1 = QgsRendererRange(minVal, maxVal, mySymbol1, '{0:.2f}-{1:.2f}'.format(minVal, maxVal))
                myRangeList.append(myRange1)
                num+=1.0
                minVal = maxVal

            myRenderer = QgsGraduatedSymbolRenderer('', myRangeList)
            myRenderer.setMode(QgsGraduatedSymbolRenderer.EqualInterval)
            myRenderer.setClassAttribute('value')
            shpLayer.setRenderer(myRenderer)

        QgsProject.instance().addMapLayer(shpLayer)

    def saveSettings(self):
        settings = QSettings()

        if self.modelListWidget.currentItem():
            model_no = self.modelListWidget.currentItem().data(Qt.UserRole)
            settings.setValue('PDS/QgisPDSModel3DDialog/model', model_no)

        if self.propertyListWidget.currentItem():
            key = self.propertyListWidget.currentItem().text()
            settings.setValue('PDS/QgisPDSModel3DDialog/property', key)

        settings.setValue('PDS/QgisPDSModel3DDialog/layer', self.layerSpinBox.value())

    def readSettings(self):
        settings = QSettings()

        model_no = settings.value('PDS/QgisPDSModel3DDialog/model', -1)
        key = settings.value('PDS/QgisPDSModel3DDialog/property', "")
        layer = settings.value('PDS/QgisPDSModel3DDialog/layer', 1)

        return (model_no, key, layer)
