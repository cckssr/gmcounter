# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'interval_tab.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (
    QCoreApplication,
    QDate,
    QDateTime,
    QLocale,
    QMetaObject,
    QObject,
    QPoint,
    QRect,
    QSize,
    QTime,
    QUrl,
    Qt,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QCursor,
    QFont,
    QFontDatabase,
    QGradient,
    QIcon,
    QImage,
    QKeySequence,
    QLinearGradient,
    QPainter,
    QPalette,
    QPixmap,
    QRadialGradient,
    QTransform,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QTableView,
    QWidget,
)

from gmcounter.ui.widgets.plot import GeneralPlot


class Ui_IntervalTab(object):
    def setupUi(self, IntervalTab):
        if not IntervalTab.objectName():
            IntervalTab.setObjectName("IntervalTab")
        IntervalTab.resize(900, 600)
        font = QFont()
        font.setPointSize(11)
        IntervalTab.setFont(font)
        self.gridInterval = QGridLayout(IntervalTab)
        self.gridInterval.setObjectName("gridInterval")
        self.gridInterval.setContentsMargins(10, 10, 10, 5)
        self.layoutIntervalControls = QHBoxLayout()
        self.layoutIntervalControls.setObjectName("layoutIntervalControls")
        self.labelWidth = QLabel(IntervalTab)
        self.labelWidth.setObjectName("labelWidth")

        self.layoutIntervalControls.addWidget(self.labelWidth)

        self.spinWidth = QDoubleSpinBox(IntervalTab)
        self.spinWidth.setObjectName("spinWidth")
        self.spinWidth.setMinimum(0.100000000000000)
        self.spinWidth.setMaximum(3600.000000000000000)
        self.spinWidth.setSingleStep(1.000000000000000)
        self.spinWidth.setValue(1.000000000000000)

        self.layoutIntervalControls.addWidget(self.spinWidth)

        self.labelRepeats = QLabel(IntervalTab)
        self.labelRepeats.setObjectName("labelRepeats")

        self.layoutIntervalControls.addWidget(self.labelRepeats)

        self.spinRepeats = QSpinBox(IntervalTab)
        self.spinRepeats.setObjectName("spinRepeats")
        self.spinRepeats.setMinimum(1)
        self.spinRepeats.setMaximum(10000)
        self.spinRepeats.setValue(10)

        self.layoutIntervalControls.addWidget(self.spinRepeats)

        self.spacerInterval = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        self.layoutIntervalControls.addItem(self.spacerInterval)

        self.valueStatus = QLabel(IntervalTab)
        self.valueStatus.setObjectName("valueStatus")
        self.valueStatus.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignTrailing
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.layoutIntervalControls.addWidget(self.valueStatus)

        self.gridInterval.addLayout(self.layoutIntervalControls, 0, 0, 1, 1)

        self.intervalPlot = GeneralPlot(IntervalTab)
        self.intervalPlot.setObjectName("intervalPlot")
        sizePolicy = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.intervalPlot.sizePolicy().hasHeightForWidth())
        self.intervalPlot.setSizePolicy(sizePolicy)

        self.gridInterval.addWidget(self.intervalPlot, 1, 0, 1, 1)

        self.tableIntervals = QTableView(IntervalTab)
        self.tableIntervals.setObjectName("tableIntervals")
        sizePolicy1 = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum
        )
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(
            self.tableIntervals.sizePolicy().hasHeightForWidth()
        )
        self.tableIntervals.setSizePolicy(sizePolicy1)
        self.tableIntervals.setMaximumSize(QSize(16777215, 200))
        self.tableIntervals.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.tableIntervals.setAlternatingRowColors(True)
        self.tableIntervals.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.gridInterval.addWidget(self.tableIntervals, 2, 0, 1, 1)

        self.gridInterval.setRowStretch(1, 1)

        self.retranslateUi(IntervalTab)

        QMetaObject.connectSlotsByName(IntervalTab)

    # setupUi

    def retranslateUi(self, IntervalTab):
        self.labelWidth.setText(
            QCoreApplication.translate("IntervalTab", "Intervallbreite", None)
        )
        self.spinWidth.setSuffix(QCoreApplication.translate("IntervalTab", " s", None))
        self.labelRepeats.setText(
            QCoreApplication.translate("IntervalTab", "Wiederholungen", None)
        )
        pass

    # retranslateUi
