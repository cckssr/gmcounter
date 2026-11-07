# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'timing_tab.ui'
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
    QAbstractSpinBox,
    QApplication,
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSpacerItem,
    QSpinBox,
    QTabWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from gmcounter.ui.widgets.plot import GeneralPlot, HistogramWidget


class Ui_TimingTab(object):
    def setupUi(self, TimingTab):
        if not TimingTab.objectName():
            TimingTab.setObjectName("TimingTab")
        TimingTab.resize(900, 600)
        font = QFont()
        font.setPointSize(11)
        TimingTab.setFont(font)
        self.layoutTiming = QVBoxLayout(TimingTab)
        self.layoutTiming.setObjectName("layoutTiming")
        self.layoutTiming.setContentsMargins(0, 0, 0, 0)
        self.tabViews = QTabWidget(TimingTab)
        self.tabViews.setObjectName("tabViews")
        sizePolicy = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabViews.sizePolicy().hasHeightForWidth())
        self.tabViews.setSizePolicy(sizePolicy)
        self.pageTime = QWidget()
        self.pageTime.setObjectName("pageTime")
        self.gridTime = QGridLayout(self.pageTime)
        self.gridTime.setObjectName("gridTime")
        self.gridTime.setContentsMargins(10, 10, 10, 5)
        self.layoutPlotControls = QHBoxLayout()
        self.layoutPlotControls.setObjectName("layoutPlotControls")
        self.layoutPlotControls.setContentsMargins(-1, 0, -1, -1)
        self.spacerPlotControls = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        self.layoutPlotControls.addItem(self.spacerPlotControls)

        self.labelPlotPoints = QLabel(self.pageTime)
        self.labelPlotPoints.setObjectName("labelPlotPoints")

        self.layoutPlotControls.addWidget(self.labelPlotPoints)

        self.spinPlotPoints = QSpinBox(self.pageTime)
        self.spinPlotPoints.setObjectName("spinPlotPoints")
        self.spinPlotPoints.setMinimum(10)
        self.spinPlotPoints.setMaximum(100000)
        self.spinPlotPoints.setSingleStep(10)
        self.spinPlotPoints.setStepType(
            QAbstractSpinBox.StepType.AdaptiveDecimalStepType
        )
        self.spinPlotPoints.setValue(2000)

        self.layoutPlotControls.addWidget(self.spinPlotPoints)

        self.checkAutoScroll = QCheckBox(self.pageTime)
        self.checkAutoScroll.setObjectName("checkAutoScroll")
        self.checkAutoScroll.setChecked(True)

        self.layoutPlotControls.addWidget(self.checkAutoScroll)

        self.buttonAutoRange = QPushButton(self.pageTime)
        self.buttonAutoRange.setObjectName("buttonAutoRange")

        self.layoutPlotControls.addWidget(self.buttonAutoRange)

        self.gridTime.addLayout(self.layoutPlotControls, 0, 0, 1, 1)

        self.timePlot = GeneralPlot(self.pageTime)
        self.timePlot.setObjectName("timePlot")
        sizePolicy.setHeightForWidth(self.timePlot.sizePolicy().hasHeightForWidth())
        self.timePlot.setSizePolicy(sizePolicy)

        self.gridTime.addWidget(self.timePlot, 1, 0, 1, 1)

        self.gridTime.setRowStretch(1, 1)
        self.tabViews.addTab(self.pageTime, "")
        self.pageHistogram = QWidget()
        self.pageHistogram.setObjectName("pageHistogram")
        self.gridHistogram = QGridLayout(self.pageHistogram)
        self.gridHistogram.setObjectName("gridHistogram")
        self.gridHistogram.setContentsMargins(10, 10, 10, 5)
        self.layoutStats = QGridLayout()
        self.layoutStats.setObjectName("layoutStats")
        self.labelStatCount = QLabel(self.pageHistogram)
        self.labelStatCount.setObjectName("labelStatCount")

        self.layoutStats.addWidget(self.labelStatCount, 0, 0, 1, 1)

        self.valueStatCount = QLabel(self.pageHistogram)
        self.valueStatCount.setObjectName("valueStatCount")
        self.valueStatCount.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.valueStatCount.setFrameShape(QFrame.Shape.StyledPanel)
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(
            self.valueStatCount.sizePolicy().hasHeightForWidth()
        )
        self.valueStatCount.setSizePolicy(sizePolicy1)
        self.valueStatCount.setMinimumSize(QSize(70, 0))

        self.layoutStats.addWidget(self.valueStatCount, 1, 0, 1, 1)

        self.labelStatMin = QLabel(self.pageHistogram)
        self.labelStatMin.setObjectName("labelStatMin")

        self.layoutStats.addWidget(self.labelStatMin, 0, 1, 1, 1)

        self.valueStatMin = QLabel(self.pageHistogram)
        self.valueStatMin.setObjectName("valueStatMin")
        self.valueStatMin.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.valueStatMin.setFrameShape(QFrame.Shape.StyledPanel)
        sizePolicy1.setHeightForWidth(
            self.valueStatMin.sizePolicy().hasHeightForWidth()
        )
        self.valueStatMin.setSizePolicy(sizePolicy1)
        self.valueStatMin.setMinimumSize(QSize(70, 0))

        self.layoutStats.addWidget(self.valueStatMin, 1, 1, 1, 1)

        self.labelStatMax = QLabel(self.pageHistogram)
        self.labelStatMax.setObjectName("labelStatMax")

        self.layoutStats.addWidget(self.labelStatMax, 0, 2, 1, 1)

        self.valueStatMax = QLabel(self.pageHistogram)
        self.valueStatMax.setObjectName("valueStatMax")
        self.valueStatMax.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.valueStatMax.setFrameShape(QFrame.Shape.StyledPanel)
        sizePolicy1.setHeightForWidth(
            self.valueStatMax.sizePolicy().hasHeightForWidth()
        )
        self.valueStatMax.setSizePolicy(sizePolicy1)
        self.valueStatMax.setMinimumSize(QSize(70, 0))

        self.layoutStats.addWidget(self.valueStatMax, 1, 2, 1, 1)

        self.labelStatMean = QLabel(self.pageHistogram)
        self.labelStatMean.setObjectName("labelStatMean")

        self.layoutStats.addWidget(self.labelStatMean, 0, 3, 1, 1)

        self.valueStatMean = QLabel(self.pageHistogram)
        self.valueStatMean.setObjectName("valueStatMean")
        self.valueStatMean.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.valueStatMean.setFrameShape(QFrame.Shape.StyledPanel)
        sizePolicy1.setHeightForWidth(
            self.valueStatMean.sizePolicy().hasHeightForWidth()
        )
        self.valueStatMean.setSizePolicy(sizePolicy1)
        self.valueStatMean.setMinimumSize(QSize(70, 0))

        self.layoutStats.addWidget(self.valueStatMean, 1, 3, 1, 1)

        self.labelStatStd = QLabel(self.pageHistogram)
        self.labelStatStd.setObjectName("labelStatStd")

        self.layoutStats.addWidget(self.labelStatStd, 0, 4, 1, 1)

        self.valueStatStd = QLabel(self.pageHistogram)
        self.valueStatStd.setObjectName("valueStatStd")
        self.valueStatStd.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.valueStatStd.setFrameShape(QFrame.Shape.StyledPanel)
        sizePolicy1.setHeightForWidth(
            self.valueStatStd.sizePolicy().hasHeightForWidth()
        )
        self.valueStatStd.setSizePolicy(sizePolicy1)
        self.valueStatStd.setMinimumSize(QSize(70, 0))

        self.layoutStats.addWidget(self.valueStatStd, 1, 4, 1, 1)

        self.spacerStats = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        self.layoutStats.addItem(self.spacerStats, 0, 5, 2, 1)

        self.gridHistogram.addLayout(self.layoutStats, 0, 0, 1, 1)

        self.layoutBinning = QHBoxLayout()
        self.layoutBinning.setObjectName("layoutBinning")
        self.layoutBinning.setContentsMargins(-1, -1, -1, 0)
        self.labelBinSize = QLabel(self.pageHistogram)
        self.labelBinSize.setObjectName("labelBinSize")

        self.layoutBinning.addWidget(self.labelBinSize)

        self.sliderBinSize = QSlider(self.pageHistogram)
        self.sliderBinSize.setObjectName("sliderBinSize")
        self.sliderBinSize.setMinimum(100)
        self.sliderBinSize.setMaximum(100000)
        self.sliderBinSize.setSingleStep(50)
        self.sliderBinSize.setOrientation(Qt.Orientation.Horizontal)
        self.sliderBinSize.setTickPosition(QSlider.TickPosition.NoTicks)

        self.layoutBinning.addWidget(self.sliderBinSize)

        self.spinBinSize = QSpinBox(self.pageHistogram)
        self.spinBinSize.setObjectName("spinBinSize")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.spinBinSize.sizePolicy().hasHeightForWidth())
        self.spinBinSize.setSizePolicy(sizePolicy2)
        self.spinBinSize.setMinimumSize(QSize(80, 0))
        self.spinBinSize.setFrame(False)
        self.spinBinSize.setReadOnly(True)
        self.spinBinSize.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spinBinSize.setMinimum(100)
        self.spinBinSize.setMaximum(100000)
        self.spinBinSize.setSingleStep(50)
        self.spinBinSize.setValue(100000)

        self.layoutBinning.addWidget(self.spinBinSize)

        self.labelCutoff = QLabel(self.pageHistogram)
        self.labelCutoff.setObjectName("labelCutoff")

        self.layoutBinning.addWidget(self.labelCutoff)

        self.sliderCutoff = QSlider(self.pageHistogram)
        self.sliderCutoff.setObjectName("sliderCutoff")
        self.sliderCutoff.setMinimum(1000)
        self.sliderCutoff.setMaximum(100000)
        self.sliderCutoff.setSingleStep(100)
        self.sliderCutoff.setValue(5000)
        self.sliderCutoff.setOrientation(Qt.Orientation.Horizontal)
        self.sliderCutoff.setTickPosition(QSlider.TickPosition.NoTicks)

        self.layoutBinning.addWidget(self.sliderCutoff)

        self.spinCutoff = QSpinBox(self.pageHistogram)
        self.spinCutoff.setObjectName("spinCutoff")
        sizePolicy2.setHeightForWidth(self.spinCutoff.sizePolicy().hasHeightForWidth())
        self.spinCutoff.setSizePolicy(sizePolicy2)
        self.spinCutoff.setMinimumSize(QSize(80, 0))
        self.spinCutoff.setFrame(False)
        self.spinCutoff.setReadOnly(True)
        self.spinCutoff.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spinCutoff.setMinimum(100)
        self.spinCutoff.setMaximum(100000)
        self.spinCutoff.setSingleStep(50)
        self.spinCutoff.setValue(100000)

        self.layoutBinning.addWidget(self.spinCutoff)

        self.gridHistogram.addLayout(self.layoutBinning, 1, 0, 1, 1)

        self.histogramPlot = HistogramWidget(self.pageHistogram)
        self.histogramPlot.setObjectName("histogramPlot")
        sizePolicy.setHeightForWidth(
            self.histogramPlot.sizePolicy().hasHeightForWidth()
        )
        self.histogramPlot.setSizePolicy(sizePolicy)

        self.gridHistogram.addWidget(self.histogramPlot, 2, 0, 1, 1)

        self.gridHistogram.setRowStretch(2, 1)
        self.tabViews.addTab(self.pageHistogram, "")
        self.pageList = QWidget()
        self.pageList.setObjectName("pageList")
        self.gridList = QGridLayout(self.pageList)
        self.gridList.setObjectName("gridList")
        self.gridList.setContentsMargins(10, 10, 10, 5)
        self.tableEvents = QTableView(self.pageList)
        self.tableEvents.setObjectName("tableEvents")
        self.tableEvents.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.gridList.addWidget(self.tableEvents, 0, 0, 1, 1)

        self.tabViews.addTab(self.pageList, "")

        self.layoutTiming.addWidget(self.tabViews)

        self.retranslateUi(TimingTab)

        self.tabViews.setCurrentIndex(0)

        QMetaObject.connectSlotsByName(TimingTab)

    # setupUi

    def retranslateUi(self, TimingTab):
        self.labelPlotPoints.setText(
            QCoreApplication.translate("TimingTab", "Max. Plotpunkte", None)
        )
        self.checkAutoScroll.setText(
            QCoreApplication.translate("TimingTab", "Auto-Scroll", None)
        )
        self.buttonAutoRange.setText(
            QCoreApplication.translate("TimingTab", "Achsen anpassen", None)
        )
        self.tabViews.setTabText(
            self.tabViews.indexOf(self.pageTime),
            QCoreApplication.translate("TimingTab", "Zeitverlauf", None),
        )
        self.labelStatCount.setText(
            QCoreApplication.translate("TimingTab", "Anzahl", None)
        )
        self.labelStatMin.setText(
            QCoreApplication.translate("TimingTab", "Min / \u00b5s", None)
        )
        self.labelStatMax.setText(
            QCoreApplication.translate("TimingTab", "Max / \u00b5s", None)
        )
        self.labelStatMean.setText(
            QCoreApplication.translate("TimingTab", "Mittelwert / \u00b5s", None)
        )
        self.labelStatStd.setText(
            QCoreApplication.translate("TimingTab", "Standardabw. / \u00b5s", None)
        )
        self.labelBinSize.setText(
            QCoreApplication.translate(
                "TimingTab", "Bin-Gr\u00f6\u00dfe / \u00b5s", None
            )
        )
        self.spinBinSize.setSuffix(
            QCoreApplication.translate("TimingTab", " \u00b5s", None)
        )
        self.labelCutoff.setText(
            QCoreApplication.translate("TimingTab", "Cut-Off / \u00b5s", None)
        )
        # if QT_CONFIG(tooltip)
        self.sliderCutoff.setToolTip(
            QCoreApplication.translate(
                "TimingTab",
                "Obere Grenze ab welcher Daten nicht mehr im Diagramm angezeigt werden sollen",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.spinCutoff.setSuffix(
            QCoreApplication.translate("TimingTab", " \u00b5s", None)
        )
        self.tabViews.setTabText(
            self.tabViews.indexOf(self.pageHistogram),
            QCoreApplication.translate("TimingTab", "Histogramm", None),
        )
        self.tabViews.setTabText(
            self.tabViews.indexOf(self.pageList),
            QCoreApplication.translate("TimingTab", "Liste", None),
        )
        pass

    # retranslateUi
