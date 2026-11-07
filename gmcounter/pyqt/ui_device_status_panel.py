# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'device_status_panel.ui'
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
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLCDNumber,
    QLabel,
    QSizePolicy,
    QWidget,
)

from gmcounter.ui.widgets.status_led import StatusLed


class Ui_DeviceStatusPanel(object):
    def setupUi(self, DeviceStatusPanel):
        if not DeviceStatusPanel.objectName():
            DeviceStatusPanel.setObjectName("DeviceStatusPanel")
        DeviceStatusPanel.resize(260, 200)
        self.layoutDeviceStatusPanel = QGridLayout(DeviceStatusPanel)
        self.layoutDeviceStatusPanel.setSpacing(6)
        self.layoutDeviceStatusPanel.setObjectName("layoutDeviceStatusPanel")
        self.labelStatus = QLabel(DeviceStatusPanel)
        self.labelStatus.setObjectName("labelStatus")
        sizePolicy = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.labelStatus.sizePolicy().hasHeightForWidth())
        self.labelStatus.setSizePolicy(sizePolicy)

        self.layoutDeviceStatusPanel.addWidget(self.labelStatus, 0, 0, 1, 1)

        self.layoutStatus = QHBoxLayout()
        self.layoutStatus.setObjectName("layoutStatus")
        self.ledStatus = StatusLed(DeviceStatusPanel)
        self.ledStatus.setObjectName("ledStatus")

        self.layoutStatus.addWidget(self.ledStatus)

        self.valueStatus = QLabel(DeviceStatusPanel)
        self.valueStatus.setObjectName("valueStatus")
        sizePolicy1 = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.valueStatus.sizePolicy().hasHeightForWidth())
        self.valueStatus.setSizePolicy(sizePolicy1)

        self.layoutStatus.addWidget(self.valueStatus)

        self.layoutDeviceStatusPanel.addLayout(self.layoutStatus, 0, 1, 1, 1)

        self.labelVoltageReadback = QLabel(DeviceStatusPanel)
        self.labelVoltageReadback.setObjectName("labelVoltageReadback")
        sizePolicy.setHeightForWidth(
            self.labelVoltageReadback.sizePolicy().hasHeightForWidth()
        )
        self.labelVoltageReadback.setSizePolicy(sizePolicy)

        self.layoutDeviceStatusPanel.addWidget(self.labelVoltageReadback, 1, 0, 1, 1)

        self.lcdVoltage = QLCDNumber(DeviceStatusPanel)
        self.lcdVoltage.setObjectName("lcdVoltage")
        sizePolicy2 = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.lcdVoltage.sizePolicy().hasHeightForWidth())
        self.lcdVoltage.setSizePolicy(sizePolicy2)
        self.lcdVoltage.setMinimumSize(QSize(70, 36))
        self.lcdVoltage.setDigitCount(3)
        self.lcdVoltage.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)

        self.layoutDeviceStatusPanel.addWidget(self.lcdVoltage, 1, 1, 1, 1)

        self.labelDurationReadback = QLabel(DeviceStatusPanel)
        self.labelDurationReadback.setObjectName("labelDurationReadback")
        sizePolicy.setHeightForWidth(
            self.labelDurationReadback.sizePolicy().hasHeightForWidth()
        )
        self.labelDurationReadback.setSizePolicy(sizePolicy)

        self.layoutDeviceStatusPanel.addWidget(self.labelDurationReadback, 2, 0, 1, 1)

        self.lcdDuration = QLCDNumber(DeviceStatusPanel)
        self.lcdDuration.setObjectName("lcdDuration")
        sizePolicy2.setHeightForWidth(self.lcdDuration.sizePolicy().hasHeightForWidth())
        self.lcdDuration.setSizePolicy(sizePolicy2)
        self.lcdDuration.setMinimumSize(QSize(70, 36))
        self.lcdDuration.setDigitCount(3)
        self.lcdDuration.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)

        self.layoutDeviceStatusPanel.addWidget(self.lcdDuration, 2, 1, 1, 1)

        self.labelQueryReadback = QLabel(DeviceStatusPanel)
        self.labelQueryReadback.setObjectName("labelQueryReadback")
        sizePolicy.setHeightForWidth(
            self.labelQueryReadback.sizePolicy().hasHeightForWidth()
        )
        self.labelQueryReadback.setSizePolicy(sizePolicy)

        self.layoutDeviceStatusPanel.addWidget(self.labelQueryReadback, 3, 0, 1, 1)

        self.valueQueryMode = QLabel(DeviceStatusPanel)
        self.valueQueryMode.setObjectName("valueQueryMode")
        sizePolicy1.setHeightForWidth(
            self.valueQueryMode.sizePolicy().hasHeightForWidth()
        )
        self.valueQueryMode.setSizePolicy(sizePolicy1)

        self.layoutDeviceStatusPanel.addWidget(self.valueQueryMode, 3, 1, 1, 1)

        self.labelModeReadback = QLabel(DeviceStatusPanel)
        self.labelModeReadback.setObjectName("labelModeReadback")
        sizePolicy.setHeightForWidth(
            self.labelModeReadback.sizePolicy().hasHeightForWidth()
        )
        self.labelModeReadback.setSizePolicy(sizePolicy)

        self.layoutDeviceStatusPanel.addWidget(self.labelModeReadback, 4, 0, 1, 1)

        self.valueMode = QLabel(DeviceStatusPanel)
        self.valueMode.setObjectName("valueMode")
        sizePolicy1.setHeightForWidth(self.valueMode.sizePolicy().hasHeightForWidth())
        self.valueMode.setSizePolicy(sizePolicy1)

        self.layoutDeviceStatusPanel.addWidget(self.valueMode, 4, 1, 1, 1)

        self.labelFirmware = QLabel(DeviceStatusPanel)
        self.labelFirmware.setObjectName("labelFirmware")
        sizePolicy.setHeightForWidth(
            self.labelFirmware.sizePolicy().hasHeightForWidth()
        )
        self.labelFirmware.setSizePolicy(sizePolicy)

        self.layoutDeviceStatusPanel.addWidget(self.labelFirmware, 5, 0, 1, 1)

        self.valueFirmware = QLabel(DeviceStatusPanel)
        self.valueFirmware.setObjectName("valueFirmware")
        sizePolicy1.setHeightForWidth(
            self.valueFirmware.sizePolicy().hasHeightForWidth()
        )
        self.valueFirmware.setSizePolicy(sizePolicy1)

        self.layoutDeviceStatusPanel.addWidget(self.valueFirmware, 5, 1, 1, 1)

        self.labelOpenbis = QLabel(DeviceStatusPanel)
        self.labelOpenbis.setObjectName("labelOpenbis")
        sizePolicy.setHeightForWidth(self.labelOpenbis.sizePolicy().hasHeightForWidth())
        self.labelOpenbis.setSizePolicy(sizePolicy)

        self.layoutDeviceStatusPanel.addWidget(self.labelOpenbis, 6, 0, 1, 1)

        self.valueOpenbis = QLabel(DeviceStatusPanel)
        self.valueOpenbis.setObjectName("valueOpenbis")
        sizePolicy1.setHeightForWidth(
            self.valueOpenbis.sizePolicy().hasHeightForWidth()
        )
        self.valueOpenbis.setSizePolicy(sizePolicy1)

        self.layoutDeviceStatusPanel.addWidget(self.valueOpenbis, 6, 1, 1, 1)

        self.retranslateUi(DeviceStatusPanel)

        QMetaObject.connectSlotsByName(DeviceStatusPanel)

    # setupUi

    def retranslateUi(self, DeviceStatusPanel):
        DeviceStatusPanel.setTitle(
            QCoreApplication.translate("DeviceStatusPanel", "Ger\u00e4testatus", None)
        )
        self.labelStatus.setText(
            QCoreApplication.translate("DeviceStatusPanel", "Status", None)
        )
        self.valueStatus.setText(
            QCoreApplication.translate("DeviceStatusPanel", "Unbekannt", None)
        )
        self.labelVoltageReadback.setText(
            QCoreApplication.translate("DeviceStatusPanel", "GM-Spannung / V", None)
        )
        # if QT_CONFIG(tooltip)
        self.lcdVoltage.setToolTip(
            QCoreApplication.translate(
                "DeviceStatusPanel", "Aktuelle GM-Spannung", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.labelDurationReadback.setText(
            QCoreApplication.translate("DeviceStatusPanel", "Z\u00e4hldauer / s", None)
        )
        # if QT_CONFIG(tooltip)
        self.lcdDuration.setToolTip(
            QCoreApplication.translate(
                "DeviceStatusPanel",
                "Aktuell eingestellte Z\u00e4hldauer; 999 f\u00fcr unendlich",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.labelQueryReadback.setText(
            QCoreApplication.translate("DeviceStatusPanel", "Abfragemodus", None)
        )
        self.valueQueryMode.setText(
            QCoreApplication.translate("DeviceStatusPanel", "unbekannt", None)
        )
        # if QT_CONFIG(tooltip)
        self.valueQueryMode.setToolTip(
            QCoreApplication.translate(
                "DeviceStatusPanel",
                "Aktuell eingestellter Abfragemodus der Z\u00e4hlergebnisse",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.labelModeReadback.setText(
            QCoreApplication.translate("DeviceStatusPanel", "Z\u00e4hl-Modus", None)
        )
        self.valueMode.setText(
            QCoreApplication.translate("DeviceStatusPanel", "unbekannt", None)
        )
        # if QT_CONFIG(tooltip)
        self.valueMode.setToolTip(
            QCoreApplication.translate(
                "DeviceStatusPanel", "Aktuell eingestellter Z\u00e4hlmodus", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.labelFirmware.setText(
            QCoreApplication.translate("DeviceStatusPanel", "Firmware-Version", None)
        )
        self.valueFirmware.setText(
            QCoreApplication.translate("DeviceStatusPanel", "unbekannt", None)
        )
        # if QT_CONFIG(tooltip)
        self.valueFirmware.setToolTip(
            QCoreApplication.translate(
                "DeviceStatusPanel", "GM-Z\u00e4hler-Firmware", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.labelOpenbis.setText(
            QCoreApplication.translate("DeviceStatusPanel", "OpenBIS-Code", None)
        )
        self.valueOpenbis.setText(
            QCoreApplication.translate("DeviceStatusPanel", "unbekannt", None)
        )

    # retranslateUi
