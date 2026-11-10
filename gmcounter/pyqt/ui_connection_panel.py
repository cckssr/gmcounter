# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'connection_panel.ui'
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
    QApplication,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QWidget,
)

from gmcounter.ui.widgets.elided_label import ElidedLabel
from gmcounter.ui.widgets.status_led import StatusLed


class Ui_ConnectionPanel(object):
    def setupUi(self, ConnectionPanel):
        if not ConnectionPanel.objectName():
            ConnectionPanel.setObjectName("ConnectionPanel")
        ConnectionPanel.resize(260, 160)
        self.layoutConnectionPanel = QGridLayout(ConnectionPanel)
        self.layoutConnectionPanel.setSpacing(6)
        self.layoutConnectionPanel.setObjectName("layoutConnectionPanel")
        self.labelPort = QLabel(ConnectionPanel)
        self.labelPort.setObjectName("labelPort")

        self.layoutConnectionPanel.addWidget(self.labelPort, 0, 0, 1, 1)

        self.comboPort = QComboBox(ConnectionPanel)
        self.comboPort.setObjectName("comboPort")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboPort.sizePolicy().hasHeightForWidth())
        self.comboPort.setSizePolicy(sizePolicy)
        self.comboPort.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.comboPort.setMinimumContentsLength(8)

        self.layoutConnectionPanel.addWidget(self.comboPort, 0, 1, 1, 1)

        self.buttonRefreshPorts = QToolButton(ConnectionPanel)
        self.buttonRefreshPorts.setObjectName("buttonRefreshPorts")
        icon = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.ViewRefresh))
        self.buttonRefreshPorts.setIcon(icon)

        self.layoutConnectionPanel.addWidget(self.buttonRefreshPorts, 0, 2, 1, 1)

        self.labelDescription = QLabel(ConnectionPanel)
        self.labelDescription.setObjectName("labelDescription")

        self.layoutConnectionPanel.addWidget(self.labelDescription, 1, 0, 1, 1)

        self.valueDescription = ElidedLabel(ConnectionPanel)
        self.valueDescription.setObjectName("valueDescription")
        sizePolicy1 = QSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
        )
        sizePolicy1.setHorizontalStretch(1)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(
            self.valueDescription.sizePolicy().hasHeightForWidth()
        )
        self.valueDescription.setSizePolicy(sizePolicy1)

        self.layoutConnectionPanel.addWidget(self.valueDescription, 1, 1, 1, 2)

        self.labelBaud = QLabel(ConnectionPanel)
        self.labelBaud.setObjectName("labelBaud")

        self.layoutConnectionPanel.addWidget(self.labelBaud, 2, 0, 1, 1)

        self.comboBaud = QComboBox(ConnectionPanel)
        self.comboBaud.setObjectName("comboBaud")
        sizePolicy.setHeightForWidth(self.comboBaud.sizePolicy().hasHeightForWidth())
        self.comboBaud.setSizePolicy(sizePolicy)

        self.layoutConnectionPanel.addWidget(self.comboBaud, 2, 1, 1, 2)

        self.labelStatus = QLabel(ConnectionPanel)
        self.labelStatus.setObjectName("labelStatus")

        self.layoutConnectionPanel.addWidget(self.labelStatus, 3, 0, 1, 1)

        self.layoutStatus = QHBoxLayout()
        self.layoutStatus.setSpacing(6)
        self.layoutStatus.setObjectName("layoutStatus")
        self.ledStatus = StatusLed(ConnectionPanel)
        self.ledStatus.setObjectName("ledStatus")

        self.layoutStatus.addWidget(self.ledStatus)

        self.valueStatus = ElidedLabel(ConnectionPanel)
        self.valueStatus.setObjectName("valueStatus")
        sizePolicy1.setHeightForWidth(self.valueStatus.sizePolicy().hasHeightForWidth())
        self.valueStatus.setSizePolicy(sizePolicy1)

        self.layoutStatus.addWidget(self.valueStatus)

        self.layoutConnectionPanel.addLayout(self.layoutStatus, 3, 1, 1, 2)

        self.buttonConnect = QPushButton(ConnectionPanel)
        self.buttonConnect.setObjectName("buttonConnect")

        self.layoutConnectionPanel.addWidget(self.buttonConnect, 4, 0, 1, 3)

        self.layoutConnectionPanel.setColumnStretch(1, 1)

        self.retranslateUi(ConnectionPanel)

        QMetaObject.connectSlotsByName(ConnectionPanel)

    # setupUi

    def retranslateUi(self, ConnectionPanel):
        ConnectionPanel.setTitle(
            QCoreApplication.translate("ConnectionPanel", "Verbindung", None)
        )
        self.labelPort.setText(
            QCoreApplication.translate("ConnectionPanel", "Port", None)
        )
        # if QT_CONFIG(tooltip)
        self.comboPort.setToolTip(
            QCoreApplication.translate(
                "ConnectionPanel",
                "Serieller Port des GM-Z\u00e4hlers (Arduino). Wird der Z\u00e4hler nicht erkannt: abstecken, Liste aktualisieren, anstecken, erneut aktualisieren und den neuen Port w\u00e4hlen.",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.comboPort.setPlaceholderText(
            QCoreApplication.translate("ConnectionPanel", "Kein Port gefunden", None)
        )
        # if QT_CONFIG(tooltip)
        self.buttonRefreshPorts.setToolTip(
            QCoreApplication.translate(
                "ConnectionPanel", "Liste der seriellen Ports aktualisieren", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.buttonRefreshPorts.setText(
            QCoreApplication.translate("ConnectionPanel", "\u21bb", None)
        )
        self.labelDescription.setText(
            QCoreApplication.translate("ConnectionPanel", "Ger\u00e4t", None)
        )
        self.labelBaud.setText(
            QCoreApplication.translate("ConnectionPanel", "Baudrate", None)
        )
        # if QT_CONFIG(tooltip)
        self.comboBaud.setToolTip(
            QCoreApplication.translate(
                "ConnectionPanel",
                "Baudrate der seriellen Verbindung (Standard: 1000000)",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.labelStatus.setText(
            QCoreApplication.translate("ConnectionPanel", "Status", None)
        )
        # if QT_CONFIG(tooltip)
        self.buttonConnect.setToolTip(
            QCoreApplication.translate(
                "ConnectionPanel",
                "GM-Z\u00e4hler \u00fcber den gew\u00e4hlten Port verbinden oder trennen",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.buttonConnect.setText(
            QCoreApplication.translate("ConnectionPanel", "Verbinden", None)
        )

    # retranslateUi
