# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QgisPDS_v3
                                 A PUMA+ plugin
 PDS link
                             -------------------
        begin                : 2016-11-05
        copyright            : (C) 2019 by SoyuzGeoService
        email                : viktor@gmail.com, skylex72rus@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load QgisPDS class from file QgisPDS.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from qgis.PyQt.QtCore import QSettings
    from qgis.core import QgsMessageLog
    import os,sys

    settings_svg_path=QSettings().value( 'svg/searchPathsForSVG')
    if settings_svg_path is None or type(settings_svg_path) is str : settings_svg_path = []

    svg_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),u'svg')
    utils_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),u'libs\\pds_opt_py')
    utils_platform_depended=str(os.path.join(
                                os.path.dirname(os.path.abspath(__file__))
                                ,r"libs\x86_64" if sys.maxsize > 2**32 else r"libs\i386" 
                            ))
    bin_platform_depended=str(os.path.join(
                                os.path.dirname(os.path.abspath(__file__))
                                ,r"bin\x86_64" if sys.maxsize > 2**32 else r"bin\i386" 
                            ))
    sys.path.insert(0, utils_platform_depended)
    sys.path.insert(0, utils_path)
    sys.path.insert(0, bin_platform_depended)
    
    if svg_path not in settings_svg_path and svg_path is not None:
        settings_svg_path.append(svg_path)
        QSettings().setValue('svg/searchPathsForSVG', ', '.join(settings_svg_path))

    from .qgis_pds import QgisPDS
    return QgisPDS(iface)
