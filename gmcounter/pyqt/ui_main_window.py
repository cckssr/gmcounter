# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
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
    QAction,
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
    QApplication,
    QDockWidget,
    QFrame,
    QMainWindow,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from gmcounter.ui.panels.device_panel import DevicePanel
from gmcounter.ui.panels.device_status_panel import DeviceStatusPanel
from gmcounter.ui.panels.event_log_panel import EventLogPanel
from gmcounter.ui.panels.measurement_panel import MeasurementPanel
from gmcounter.ui.panels.readout_panel import ReadoutPanel
from gmcounter.ui.panels.sample_panel import SamplePanel


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1280, 800)
        self.actionToggleControls = QAction(MainWindow)
        self.actionToggleControls.setObjectName("actionToggleControls")
        self.actionToggleControls.setCheckable(True)
        self.actionToggleControls.setChecked(True)
        self.actionToggleLive = QAction(MainWindow)
        self.actionToggleLive.setObjectName("actionToggleLive")
        self.actionToggleLive.setCheckable(True)
        self.actionToggleLive.setChecked(True)
        self.actionToggleLog = QAction(MainWindow)
        self.actionToggleLog.setObjectName("actionToggleLog")
        self.actionToggleLog.setCheckable(True)
        self.actionSwitchProfile = QAction(MainWindow)
        self.actionSwitchProfile.setObjectName("actionSwitchProfile")
        self.actionFullScreen = QAction(MainWindow)
        self.actionFullScreen.setObjectName("actionFullScreen")
        self.actionFullScreen.setCheckable(True)
        # if QT_CONFIG(shortcut)
        self.actionFullScreen.setShortcut("F11")
        # endif // QT_CONFIG(shortcut)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.centralLayout = QVBoxLayout(self.centralwidget)
        self.centralLayout.setObjectName("centralLayout")
        self.centralLayout.setContentsMargins(0, 0, 0, 0)
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")
        self.tabWidget.setDocumentMode(False)

        self.centralLayout.addWidget(self.tabWidget)

        MainWindow.setCentralWidget(self.centralwidget)
        self.toolBar = QToolBar(MainWindow)
        self.toolBar.setObjectName("toolBar")
        self.toolBar.setMovable(False)
        MainWindow.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolBar)
        self.dockControls = QDockWidget(MainWindow)
        self.dockControls.setObjectName("dockControls")
        self.dockControls.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self.dockControls.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.dockControlsContents = QWidget()
        self.dockControlsContents.setObjectName("dockControlsContents")
        self.dockControlsLayout = QVBoxLayout(self.dockControlsContents)
        self.dockControlsLayout.setObjectName("dockControlsLayout")
        self.dockControlsLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollControls = QScrollArea(self.dockControlsContents)
        self.scrollControls.setObjectName("scrollControls")
        self.scrollControls.setFrameShape(QFrame.Shape.NoFrame)
        self.scrollControls.setWidgetResizable(True)
        self.scrollControls.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.contentControls = QWidget()
        self.contentControls.setObjectName("contentControls")
        self.contentControlsLayout = QVBoxLayout(self.contentControls)
        self.contentControlsLayout.setSpacing(6)
        self.contentControlsLayout.setObjectName("contentControlsLayout")
        self.contentControlsLayout.setContentsMargins(4, 4, 4, 4)
        self.devicePanel = DevicePanel(self.contentControls)
        self.devicePanel.setObjectName("devicePanel")

        self.contentControlsLayout.addWidget(self.devicePanel)

        self.samplePanel = SamplePanel(self.contentControls)
        self.samplePanel.setObjectName("samplePanel")

        self.contentControlsLayout.addWidget(self.samplePanel)

        self.measurementPanel = MeasurementPanel(self.contentControls)
        self.measurementPanel.setObjectName("measurementPanel")

        self.contentControlsLayout.addWidget(self.measurementPanel)

        self.spacerControls = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )

        self.contentControlsLayout.addItem(self.spacerControls)

        self.scrollControls.setWidget(self.contentControls)

        self.dockControlsLayout.addWidget(self.scrollControls)

        self.dockControls.setWidget(self.dockControlsContents)
        MainWindow.addDockWidget(
            Qt.DockWidgetArea.LeftDockWidgetArea, self.dockControls
        )
        self.dockLive = QDockWidget(MainWindow)
        self.dockLive.setObjectName("dockLive")
        self.dockLive.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self.dockLive.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.dockLiveContents = QWidget()
        self.dockLiveContents.setObjectName("dockLiveContents")
        self.dockLiveLayout = QVBoxLayout(self.dockLiveContents)
        self.dockLiveLayout.setObjectName("dockLiveLayout")
        self.dockLiveLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollLive = QScrollArea(self.dockLiveContents)
        self.scrollLive.setObjectName("scrollLive")
        self.scrollLive.setFrameShape(QFrame.Shape.NoFrame)
        self.scrollLive.setWidgetResizable(True)
        self.scrollLive.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.contentLive = QWidget()
        self.contentLive.setObjectName("contentLive")
        self.contentLiveLayout = QVBoxLayout(self.contentLive)
        self.contentLiveLayout.setSpacing(6)
        self.contentLiveLayout.setObjectName("contentLiveLayout")
        self.contentLiveLayout.setContentsMargins(4, 4, 4, 4)
        self.readoutPanel = ReadoutPanel(self.contentLive)
        self.readoutPanel.setObjectName("readoutPanel")

        self.contentLiveLayout.addWidget(self.readoutPanel)

        self.deviceStatusPanel = DeviceStatusPanel(self.contentLive)
        self.deviceStatusPanel.setObjectName("deviceStatusPanel")

        self.contentLiveLayout.addWidget(self.deviceStatusPanel)

        self.spacerLive = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )

        self.contentLiveLayout.addItem(self.spacerLive)

        self.scrollLive.setWidget(self.contentLive)

        self.dockLiveLayout.addWidget(self.scrollLive)

        self.dockLive.setWidget(self.dockLiveContents)
        MainWindow.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dockLive)
        self.dockLog = QDockWidget(MainWindow)
        self.dockLog.setObjectName("dockLog")
        self.dockLog.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self.dockLog.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.TopDockWidgetArea
        )
        self.dockLog.setVisible(False)
        self.dockLogContents = QWidget()
        self.dockLogContents.setObjectName("dockLogContents")
        self.dockLogLayout = QVBoxLayout(self.dockLogContents)
        self.dockLogLayout.setObjectName("dockLogLayout")
        self.dockLogLayout.setContentsMargins(0, 0, 0, 0)
        self.eventLogPanel = EventLogPanel(self.dockLogContents)
        self.eventLogPanel.setObjectName("eventLogPanel")

        self.dockLogLayout.addWidget(self.eventLogPanel)

        self.dockLog.setWidget(self.dockLogContents)
        MainWindow.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.dockLog)
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setObjectName("statusBar")
        MainWindow.setStatusBar(self.statusBar)

        self.toolBar.addAction(self.actionToggleControls)
        self.toolBar.addAction(self.actionToggleLive)
        self.toolBar.addAction(self.actionToggleLog)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionSwitchProfile)
        self.toolBar.addAction(self.actionFullScreen)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)

    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(
            QCoreApplication.translate("MainWindow", "GM-Counter", None)
        )
        self.actionToggleControls.setText(
            QCoreApplication.translate("MainWindow", "Steuerung", None)
        )
        # if QT_CONFIG(tooltip)
        self.actionToggleControls.setToolTip(
            QCoreApplication.translate(
                "MainWindow",
                "Seitenleiste mit Ger\u00e4te-, Proben- und Messungssteuerung ein- oder ausblenden",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.actionToggleLive.setText(
            QCoreApplication.translate("MainWindow", "Anzeige", None)
        )
        # if QT_CONFIG(tooltip)
        self.actionToggleLive.setToolTip(
            QCoreApplication.translate(
                "MainWindow",
                "Seitenleiste mit Z\u00e4hlergebnissen und Ger\u00e4testatus ein- oder ausblenden",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.actionToggleLog.setText(
            QCoreApplication.translate("MainWindow", "Protokoll", None)
        )
        # if QT_CONFIG(tooltip)
        self.actionToggleLog.setToolTip(
            QCoreApplication.translate(
                "MainWindow", "Ereignisprotokoll ein- oder ausblenden", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.actionSwitchProfile.setText(
            QCoreApplication.translate("MainWindow", "Profil wechseln", None)
        )
        # if QT_CONFIG(tooltip)
        self.actionSwitchProfile.setToolTip(
            QCoreApplication.translate(
                "MainWindow", "Zwischen Experten- und Praktikumsprofil wechseln", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.actionFullScreen.setText(
            QCoreApplication.translate("MainWindow", "Vollbild", None)
        )
        # if QT_CONFIG(tooltip)
        self.actionFullScreen.setToolTip(
            QCoreApplication.translate(
                "MainWindow", "Zwischen Vollbild und Fenster wechseln (F11)", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.toolBar.setWindowTitle(
            QCoreApplication.translate("MainWindow", "Werkzeugleiste", None)
        )
        self.dockControls.setWindowTitle(
            QCoreApplication.translate("MainWindow", "Steuerung", None)
        )
        self.dockLive.setWindowTitle(
            QCoreApplication.translate("MainWindow", "Anzeige", None)
        )
        self.dockLog.setWindowTitle(
            QCoreApplication.translate("MainWindow", "Ereignisprotokoll", None)
        )

    # retranslateUi
