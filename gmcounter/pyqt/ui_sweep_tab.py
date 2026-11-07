# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'sweep_tab.ui'
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
    QTableView,
    QWidget,
)

from gmcounter.ui.widgets.plot import GeneralPlot


class Ui_SweepTab(object):
    def setupUi(self, SweepTab):
        if not SweepTab.objectName():
            SweepTab.setObjectName("SweepTab")
        SweepTab.resize(900, 600)
        font = QFont()
        font.setPointSize(11)
        SweepTab.setFont(font)
        self.gridSweep = QGridLayout(SweepTab)
        self.gridSweep.setObjectName("gridSweep")
        self.gridSweep.setContentsMargins(10, 10, 10, 5)
        self.layoutSweepControls = QHBoxLayout()
        self.layoutSweepControls.setObjectName("layoutSweepControls")
        self.labelParam = QLabel(SweepTab)
        self.labelParam.setObjectName("labelParam")

        self.layoutSweepControls.addWidget(self.labelParam)

        self.spinParam = QDoubleSpinBox(SweepTab)
        self.spinParam.setObjectName("spinParam")
        self.spinParam.setDecimals(1)
        self.spinParam.setMaximum(99999.000000000000000)
        self.spinParam.setSingleStep(0.500000000000000)

        self.layoutSweepControls.addWidget(self.spinParam)

        self.labelHint = QLabel(SweepTab)
        self.labelHint.setObjectName("labelHint")

        self.layoutSweepControls.addWidget(self.labelHint)

        self.spacerSweep = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        self.layoutSweepControls.addItem(self.spacerSweep)

        self.valueStatus = QLabel(SweepTab)
        self.valueStatus.setObjectName("valueStatus")
        self.valueStatus.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignTrailing
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.layoutSweepControls.addWidget(self.valueStatus)

        self.gridSweep.addLayout(self.layoutSweepControls, 0, 0, 1, 1)

        self.sweepPlot = GeneralPlot(SweepTab)
        self.sweepPlot.setObjectName("sweepPlot")
        sizePolicy = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sweepPlot.sizePolicy().hasHeightForWidth())
        self.sweepPlot.setSizePolicy(sizePolicy)

        self.gridSweep.addWidget(self.sweepPlot, 1, 0, 1, 1)

        self.tableSummary = QTableView(SweepTab)
        self.tableSummary.setObjectName("tableSummary")
        sizePolicy1 = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum
        )
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(
            self.tableSummary.sizePolicy().hasHeightForWidth()
        )
        self.tableSummary.setSizePolicy(sizePolicy1)
        self.tableSummary.setMaximumSize(QSize(16777215, 200))
        self.tableSummary.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableSummary.setAlternatingRowColors(True)
        self.tableSummary.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.gridSweep.addWidget(self.tableSummary, 2, 0, 1, 1)

        self.gridSweep.setRowStretch(1, 1)

        self.retranslateUi(SweepTab)

        QMetaObject.connectSlotsByName(SweepTab)

    # setupUi

    def retranslateUi(self, SweepTab):
        self.labelParam.setText(
            QCoreApplication.translate("SweepTab", "Probenabstand", None)
        )
        self.spinParam.setSuffix(QCoreApplication.translate("SweepTab", " cm", None))
        # if QT_CONFIG(tooltip)
        self.spinParam.setToolTip(
            QCoreApplication.translate(
                "SweepTab", "Abstand der Probe vom Detektor in Zentimetern", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.labelHint.setText(
            QCoreApplication.translate(
                "SweepTab",
                "Spannung wird in der Ger\u00e4testeuerung eingestellt.",
                None,
            )
        )
        pass

    # retranslateUi
