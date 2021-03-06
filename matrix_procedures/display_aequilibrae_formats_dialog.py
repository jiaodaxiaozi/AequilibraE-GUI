"""
 -----------------------------------------------------------------------------------------------------------
 Package:    AequilibraE

 Name:       Loads AequilibraE datasets for visualization
 Purpose:    Allows visual inspection of data

 Original Author:  Pedro Camargo (c@margo.co)
 Contributors:
 Last edited by: Pedro Camargo

 Website:    www.AequilibraE.com
 Repository:  https://github.com/AequilibraE/AequilibraE

 Created:    2017-10-02
 Updated:
 Copyright:   (c) AequilibraE authors
 Licence:     See LICENSE.TXT
 -----------------------------------------------------------------------------------------------------------
 """
import logging
import numpy as np

from qgis.core import *
from qgis.PyQt import QtWidgets, uic, QtCore, QtGui
from qgis.PyQt.QtWidgets import QHBoxLayout, QTableView, QTableWidget, QPushButton, QVBoxLayout
from qgis.PyQt.QtWidgets import QComboBox, QCheckBox, QSpinBox, QLabel, QSpacerItem, QPushButton

from ..common_tools import DatabaseModel, NumpyModel, GetOutputFileName

from ..common_tools.auxiliary_functions import *
from aequilibrae.matrix import AequilibraeMatrix, AequilibraEData

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "forms/ui_data_viewer.ui"))

# Checks if we can display OMX
try:
    import openmatrix as omx

    has_omx = True
except ModuleNotFoundError as e:
    logger = logging.getLogger("aequilibrae")
    logger.error(e.name)
    has_omx = False


class DisplayAequilibraEFormatsDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, iface):
        QtWidgets.QDialog.__init__(self)
        self.iface = iface
        self.setupUi(self)

        self.error = None

        formats = ["Aequilibrae matrix(*.aem)", "Aequilibrae dataset(*.aed)"]
        if has_omx:
            formats.insert(1, "Open Matrix(*.omx)")
        self.error = None
        self.data_path, self.data_type = GetOutputFileName(
            self,
            "AequilibraE custom formats",
            formats,
            ".aem",
            standard_path(),
        )

        if self.data_type is None:
            self.error = "Path provided is not a valid dataset"
            self.exit_with_error()
        else:
            self.data_type = self.data_type.upper()

        if self.data_type in ["AED", "AEM"]:
            if self.data_type == "AED":
                self.data_to_show = AequilibraEData()
            elif self.data_type == "AEM":
                self.data_to_show = AequilibraeMatrix()

            try:
                self.data_to_show.load(self.data_path)
                self.list_cores = self.data_to_show.names
                self.list_indices = self.data_to_show.index_names
            except:
                self.error = "Could not load dataset"
                self.exit_with_error()

        elif self.data_type == "OMX":
            self.omx = omx.open_file(self.data_path, 'r')
            self.list_cores = self.omx.list_matrices()
            self.list_indices = self.omx.list_mappings()
            self.data_to_show = AequilibraeMatrix()

        # differentiates between AEM AND OMX
        if self.data_type == "AEM":
            self.data_to_show.computational_view([self.data_to_show.names[0]])
        elif self.data_type == "OMX":
            self.data_to_show.matrix_view = np.array(self.omx[self.list_cores[0]])
            self.data_to_show.index = np.array(list(self.omx.mapping(self.list_indices[0]).keys()))


        # Elements that will be used during the displaying
        self._layout = QVBoxLayout()
        self.table = QTableView()
        self._layout.addWidget(self.table)

        # Settings for displaying
        self.show_layout = QHBoxLayout()

        # Thousand separator
        self.thousand_separator = QCheckBox()
        self.thousand_separator.setChecked(True)
        self.thousand_separator.setText("Thousands separator")
        self.thousand_separator.toggled.connect(self.format_showing)
        self.show_layout.addWidget(self.thousand_separator)

        self.spacer = QSpacerItem(5, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.show_layout.addItem(self.spacer)

        # Decimals
        txt = QLabel()
        txt.setText("Decimal places")
        self.show_layout.addWidget(txt)
        self.decimals = QSpinBox()
        self.decimals.valueChanged.connect(self.format_showing)
        self.decimals.setMinimum(0)
        self.decimals.setValue(4)
        self.decimals.setMaximum(10)

        self.show_layout.addWidget(self.decimals)
        self._layout.addItem(self.show_layout)

        # differentiates between matrix and dataset
        if self.data_type in ["AEM", "OMX"]:
            # Matrices need cores and indices to be set as well
            self.mat_layout = QHBoxLayout()
            self.mat_list = QComboBox()

            for n in self.list_cores:
                self.mat_list.addItem(n)

            self.mat_list.currentIndexChanged.connect(self.change_matrix_cores)
            self.mat_layout.addWidget(self.mat_list)

            self.idx_list = QComboBox()
            for i in self.list_indices:
                self.idx_list.addItem(i)

            self.idx_list.currentIndexChanged.connect(self.change_matrix_cores)
            self.mat_layout.addWidget(self.idx_list)
            self._layout.addItem(self.mat_layout)
            self.change_matrix_cores()

        self.but_export = QPushButton()
        self.but_export.setText("Export")
        self.but_export.clicked.connect(self.export)

        self.but_close = QPushButton()
        self.but_close.clicked.connect(self.exit_procedure)
        self.but_close.setText("Close")

        self.but_layout = QHBoxLayout()
        self.but_layout.addWidget(self.but_export)
        self.but_layout.addWidget(self.but_close)

        self._layout.addItem(self.but_layout)

        # We chose to use QTableView. However, if we want to allow the user to edit the dataset
        # The we need to allow them to switch to the slower QTableWidget
        # Code below

        # self.table = QTableWidget(self.data_to_show.entries, self.data_to_show.num_fields)
        # self.table.setHorizontalHeaderLabels(self.data_to_show.fields)
        # self.table.setObjectName('data_viewer')
        #
        # self.table.setVerticalHeaderLabels([str(x) for x in self.data_to_show.index[:]])
        # self.table.clearContents()
        #
        # for i in range(self.data_to_show.entries):
        #     for j, f in enumerate(self.data_to_show.fields):
        #         item1 = QTableWidgetItem(str(self.data_to_show.data[f][i]))
        #         item1.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        #         self.table.setItem(i, j, item1)

        self.resize(700, 500)
        self.setLayout(self._layout)
        self.format_showing()

    def format_showing(self):
        decimals = self.decimals.value()
        separator = self.thousand_separator.isChecked()
        if isinstance(self.data_to_show, AequilibraeMatrix):
            m = NumpyModel(self.data_to_show, separator, decimals)
        else:
            m = DatabaseModel(self.data_to_show, separator, decimals)
        self.table.clearSpans()
        self.table.setModel(m)

    def change_matrix_cores(self):
        idx = self.idx_list.currentText()
        core = self.mat_list.currentText()
        if self.data_type == "AEM":
            self.data_to_show.computational_view([core])
            self.data_to_show.set_index(idx)
            self.format_showing()
        elif self.data_type == "OMX":
            self.data_to_show.matrix_view = np.array(self.omx[core])
            self.data_to_show.index = np.array(list(self.omx.mapping(idx).keys()))
            self.format_showing()

    def export(self):
        new_name, file_type = GetOutputFileName(
            self, self.data_type, ["Comma-separated file(*.csv)"], ".csv", self.data_path
        )
        if new_name is not None:
            self.data_to_show.export(new_name)

    def exit_with_error(self):
        qgis.utils.iface.messageBar().pushMessage("Error:", self.error, level=1)
        self.exit_procedure()

    def exit_procedure(self):
        self.close()
