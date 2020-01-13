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
from QgisPDS.tig_projection import *

class SimulationLink:
    def __init__(self, mnemonic, coordinate, simSldnam, simFldnam, simRunFldnam):
        self.mnemonic = mnemonic
        self.coordinate = coordinate
        self.simSldnam = simSldnam
        self.simFldnam = simFldnam
        self.simRunFldnam = simRunFldnam


class CornerPointGrid:
    def __init__(self, model_no, nCellsX, nCellsY, nCellsZ):
        self.XCoordLine = None
        self.YCoordLine = None
        self.ZCoordLine = None
        self.nCellsX = nCellsX
        self.nCellsY = nCellsY
        self.nCellsZ = nCellsZ
        self.runSld = 0
        self.model_no = model_no
        self.layerName = 'unknown'

        self.activeCells = None

    def getCornerCoordinates(self, i, j, k, di, dj, dk):
        x1 = self.XCoordLine[2*(i+di-1)+2*(self.nCellsX+1)*(j+dj-1)]
        y1 = self.YCoordLine[2*(i+di-1)+2*(self.nCellsX+1)*(j+dj-1)]
        z1 = self.ZCoordLine[2*(i+di-1)+2*(self.nCellsX+1)*(j+dj-1)]
        x2 = self.XCoordLine[2*(i+di-1)+2*(self.nCellsX+1)*(j+dj-1)+1]
        y2 = self.YCoordLine[2*(i+di-1)+2*(self.nCellsX+1)*(j+dj-1)+1]
        z2 = self.ZCoordLine[2*(i+di-1)+2*(self.nCellsX+1)*(j+dj-1)+1]

        offset = 2 * (self.nCellsX + 1) * (self.nCellsY + 1) + 1
        z = self.ZCoordLine[offset + 2 * (i - 1) + 4 * self.nCellsX * (j - 1) +
                            8 * self.nCellsX * self.nCellsY * (k - 1) +
                            4 * self.nCellsX * self.nCellsY * dk +
                            2 * self.nCellsX * dj + di]
        a = (z-z1)/(z2-z1)
        x = x1+a*(x2-x1)
        y = y1+a*(y2-y1)
        return (x, y, z)

    def getCornerX(self, i, j, k, di, dj, dk):
        x,y,z = self.getCornerCoordinates(i,j,k,di,dj,dk)
        return x

    def getCornerY(self, i, j, k, di, dj, dk):
        x,y,z = self.getCornerCoordinates(i,j,k,di,dj,dk)
        return y


    def getCornerZ(self, i, j, k, di, dj, dk):
        x,y,z = self.getCornerCoordinates(i,j,k,di,dj,dk)
        return z

    def getLeftBackUpperCornerX(self, i, j, k):
        return self.getCornerX(i, j, k, 0, 0, 0)

    def getLeftBackUpperCornerY(self, i, j, k):
        return self.getCornerY(i, j, k, 0, 0, 0)

    def getLeftBackUpperCornerZ(self, i, j, k):
        return self.getCornerZ(i, j, k, 0, 0, 0)

    def getRightBackUpperCornerX(self, i, j, k):
        return self.getCornerX(i, j, k, 1, 0, 0)

    def getRightBackUpperCornerY(self, i, j, k):
        return self.getCornerY(i, j, k, 1, 0, 0)

    def getRightBackUpperCornerZ(self, i, j, k):
        return self.getCornerZ(i, j, k, 1, 0, 0)

    def getLeftFrontUpperCornerX(self, i, j, k):
        return self.getCornerX(i, j, k, 0, 1, 0)

    def getLeftFrontUpperCornerY(self, i, j, k):
        return self.getCornerY(i, j, k, 0, 1, 0)

    def getLeftFrontUpperCornerZ(self, i, j, k):
        return self.getCornerZ(i, j, k, 0, 1, 0)

    def getRightFrontUpperCornerX(self, i, j, k):
        return self.getCornerX(i, j, k, 1, 1, 0)

    def getRightFrontUpperCornerY(self, i, j, k):
        return self.getCornerY(i, j, k, 1, 1, 0)

    def getRightFrontUpperCornerZ(self, i, j, k):
        return self.getCornerZ(i, j, k, 1, 1, 0)

    def getLeftBackLowerCornerX(self, i, j, k):
        return self.getCornerX(i, j, k, 0, 0, 1)

    def getLeftBackLowerCornerY(self, i, j, k):
        return self.getCornerY(i, j, k, 0, 0, 1)

    def getLeftBackLowerCornerZ(self, i, j, k):
        return self.getCornerZ(i, j, k, 0, 0, 1)

    def getRightBackLowerCornerX(self, i, j, k):
        return self.getCornerX(i, j, k, 1, 0, 1)

    def getRightBackLowerCornerY(self, i, j, k):
        return self.getCornerY(i, j, k, 1, 0, 1)

    def getRightBackLowerCornerZ(self, i, j, k):
        return self.getCornerZ(i, j, k, 1, 0, 1)

    def getLeftFrontLowerCornerX(self, i, j, k):
        return self.getCornerX(i, j, k, 0, 1, 1)

    def getLeftFrontLowerCornerY(self, i, j, k):
        return self.getCornerY(i, j, k, 0, 1, 1)

    def getLeftFrontLowerCornerZ(self, i, j, k):
        return self.getCornerZ(i, j, k, 0, 1, 1)

    def getRightFrontLowerCornerX(self, i, j, k):
        return self.getCornerX(i, j, k, 1, 1, 1)

    def getRightFrontLowerCornerY(self, i, j, k):
        return self.getCornerY(i, j, k, 1, 1, 1)

    def getRightFrontLowerCornerZ(self, i, j, k):
        return self.getCornerZ(i, j, k, 1, 1, 1)

    def getPolygon(self, i, j, layer):
        x1 = self.getLeftBackUpperCornerX(i, j, layer)
        y1 = self.getLeftBackUpperCornerY(i, j, layer)

        x2 = self.getRightBackUpperCornerX(i, j, layer)
        y2 = self.getRightBackUpperCornerY(i, j, layer)

        x3 = self.getRightFrontUpperCornerX(i, j, layer)
        y3 = self.getRightFrontUpperCornerY(i, j, layer)

        x4 = self.getLeftFrontUpperCornerX(i, j, layer)
        y4 = self.getLeftFrontUpperCornerY(i, j, layer)

        return (x1,y1, x2,y2, x3,y3, x4,y4)


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

        self.fillModelList()

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

        model_no = self.modelListWidget.currentItem().data(Qt.UserRole)

        key = self.propertyListWidget.currentItem().text()
        sl = self.simLinks[key]

        grid = self.readGrid(model_no, self.modelListWidget.currentItem().text())
        if not grid:
            QMessageBox.critical(None, self.tr(u'Ошибка'), self.tr('Ошибка загрузки модели'), QMessageBox.Ok)
            return

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

    def gridToLayer(self, grid, layer):
        if not grid:
            return

        uri = "Polygon?crs={}".format(self.proj4String)
        uri += '&field={}:{}'.format('layer', "int")
        mapLayer = QgsVectorLayer(uri, grid.layerName, "memory")

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
                mapLayer.addFeatures([cPoint])

        mapLayer.commitChanges()

        shpLayer = memoryToShp(mapLayer, self.project['project'], grid.layerName)
        QgsProject.instance().addMapLayer(shpLayer)