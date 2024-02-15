# -*- coding: utf-8 -*-
"""
/***************************************************************************
 MyPlugin
                                 A QGIS plugin
 p
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-02-12
        git sha              : $Format:%H$
        copyright            : (C) 2024 by p
        email                : p
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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsProject, QgsWkbTypes
from qgis.core import QgsVectorLayer

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .my_plugin_dialog import MyPluginDialog
import os.path


class MyPlugin:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'MyPlugin_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&My Plugin')
        
        # Must be set in selectLayer() and selectAttribute()
        self.gravity_components = {
            "target_layer": None,
            "target_attribute": None
        }

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('MyPlugin', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action


    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/my_plugin/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'MyPlugin'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&My Plugin'),
                action)
            self.iface.removeToolBarIcon(action)


    def run(self):
        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = MyPluginDialog()

        self.dlg.horizontalSlider_alpha.valueChanged.connect(self.sliderAlphaChanged)
        self.dlg.horizontalSlider_beta.valueChanged.connect(self.sliderBetaChanged)

        # Connect comboBox variant selection event to handler functions
        self.dlg.comboBox_feature_layer.activated.connect(self.selectLayer) # When layer selected
        self.dlg.comboBox_significance_attr.activated.connect(self.selectAttribute) # When attribute selected

        # show the dialog
        self.dlg.show()

        # Run the dialog event loop
        result = self.dlg.exec_()

        # Logic starts here
        layer_list = [layer for layer in QgsProject.instance().mapLayers().values()]

        self.dlg.comboBox_feature_layer.clear()
        for layer in layer_list:
            self.dlg.comboBox_feature_layer.addItem(layer.name(), layer)

        # See if OK was pressed
        if result:
            print("OK PRESSED")
            # Disconnect from handler function. Need to insure no duplicates created on 2nd+ run#########
            self.dlg.comboBox_feature_layer.activated.disconnect(self.selectLayer)
            self.dlg.comboBox_significance_attr.activated.disconnect(self.selectAttribute)
            
            target_layer = self.gravity_components["target_layer"]
            target_attribute = self.gravity_components["target_attribute"]
            power_of_significance = self.dlg.textEdit_significance_power.toPlainText()
            power_of_distance = self.dlg.textEdit_distance_power.toPlainText()
            
            # Validate Layer
            
            # Validate Attribute
            
            # Validate both numbers

            print("LAYER:", str(target_layer))
            print("ATTR:", str(target_attribute))
            print("SIGNIFICANCE:", str(power_of_significance))
            print("DISTANCE:", str(power_of_distance))
            
            # Get all components
            gravity_component_generator = self.generateGravityComponents(target_layer, target_attribute)
            alpha = power_of_significance
            beta = power_of_distance

            # Iterate through generator and calculate gravity (volume of trade)
            for m_i, m_j, distance_ij in gravity_component_generator:
                gravity_value = self.calculateGravityValue(m_i, m_j, distance_ij, alpha, beta)
                print("Gravity Value:", gravity_value)


    def selectLayer(self):
        layer = self.getCurrentLayer()
        print("Selected Layer:", layer)
        
        # If isn't Vector Layer
        if isinstance(layer, QgsVectorLayer) is False:
            self.dlg.comboBox_significance_attr.setEnabled(False)
            print("⚠️Выберите векторный слой.")
            return
        
        # Get layer attributes names
        fields = layer.fields()

        # Populate significance attribute comboBox
        self.dlg.comboBox_significance_attr.clear()
        for field in fields:
            self.dlg.comboBox_significance_attr.addItem(field.name(), field)

        # Enable comboBox with attributes
        self.dlg.comboBox_significance_attr.setEnabled(True)
        
        self.gravity_components["target_layer"] = layer
        
        
    def selectAttribute(self):
        attribute = self.getCurrentAttribute()
        self.gravity_components["target_attribute"] = attribute
        
        
    def getCurrentLayer(self):
        selected_layer_index = self.dlg.comboBox_feature_layer.currentIndex()
        return self.dlg.comboBox_feature_layer.itemData(selected_layer_index)


    def getCurrentAttribute(self):            
        selected_attribute_index = self.dlg.comboBox_significance_attr.currentIndex()
        return self.dlg.comboBox_significance_attr.itemData(selected_attribute_index)
        
        
    def calculateGravityValue(self, m_i, m_j, distance_ij, alpha, beta):
        return (m_i**alpha * m_j**alpha) / (distance_ij**beta)


    def generateGravityComponents(self, layer, attribute_name):
        total_features = layer.featureCount()

        # Iterate through all features in the layer
        for i in range(total_features):
            feature_i = layer.getFeature(i)
            for j in range(i + 1, total_features):
                feature_j = layer.getFeature(j)

                significance_measure_i = feature_i[attribute_name]
                significance_measure_j = feature_j[attribute_name]

                distance_ij = calculateDistance(feature_i, feature_j)

                yield significance_measure_i, significance_measure_j, distance_ij


        def calculateDistance():
            pass

    
    def sliderAlphaChanged(self, value):
        self.dlg.textEdit_significance_power.setText(str(value))
    
    
    def sliderBetaChanged(self, value):
        self.dlg.textEdit_distance_power.setText(str(value))
        
        
#                                                                           ____  __  _______ __    ___    _   __
#                                                                          / __ \/ / / / ___// /   /   |  / | / /
#                                                                         / /_/ / / / /\__ \/ /   / /| | /  |/ / 
#                                                                        / _, _/ /_/ /___/ / /___/ ___ |/ /|  /  
#                                                                       /_/ |_|\____//____/_____/_/  |_/_/ |_/   
                                         
