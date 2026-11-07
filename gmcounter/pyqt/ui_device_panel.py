# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'device_panel.ui'
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
    QAbstractSpinBox,
    QApplication,
    QButtonGroup,
    QComboBox,
    QDial,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QSpinBox,
    QWidget,
)


class Ui_DevicePanel(object):
    def setupUi(self, DevicePanel):
        if not DevicePanel.objectName():
            DevicePanel.setObjectName("DevicePanel")
        DevicePanel.resize(260, 200)
        self.layoutDevicePanel = QGridLayout(DevicePanel)
        self.layoutDevicePanel.setSpacing(6)
        self.layoutDevicePanel.setObjectName("layoutDevicePanel")
        self.labelCountMode = QLabel(DevicePanel)
        self.labelCountMode.setObjectName("labelCountMode")
        sizePolicy = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.labelCountMode.sizePolicy().hasHeightForWidth()
        )
        self.labelCountMode.setSizePolicy(sizePolicy)

        self.layoutDevicePanel.addWidget(self.labelCountMode, 0, 0, 1, 1)

        self.layoutCountMode = QHBoxLayout()
        self.layoutCountMode.setObjectName("layoutCountMode")
        self.radioModeSingle = QRadioButton(DevicePanel)
        self.buttonGroupCountMode = QButtonGroup(DevicePanel)
        self.buttonGroupCountMode.setObjectName("buttonGroupCountMode")
        self.buttonGroupCountMode.addButton(self.radioModeSingle)
        self.radioModeSingle.setObjectName("radioModeSingle")
        self.radioModeSingle.setChecked(True)

        self.layoutCountMode.addWidget(self.radioModeSingle)

        self.radioModeRepeat = QRadioButton(DevicePanel)
        self.buttonGroupCountMode.addButton(self.radioModeRepeat)
        self.radioModeRepeat.setObjectName("radioModeRepeat")

        self.layoutCountMode.addWidget(self.radioModeRepeat)

        self.layoutDevicePanel.addLayout(self.layoutCountMode, 0, 1, 1, 1)

        self.labelQueryMode = QLabel(DevicePanel)
        self.labelQueryMode.setObjectName("labelQueryMode")
        sizePolicy.setHeightForWidth(
            self.labelQueryMode.sizePolicy().hasHeightForWidth()
        )
        self.labelQueryMode.setSizePolicy(sizePolicy)

        self.layoutDevicePanel.addWidget(self.labelQueryMode, 1, 0, 1, 1)

        self.layoutQueryMode = QHBoxLayout()
        self.layoutQueryMode.setObjectName("layoutQueryMode")
        self.radioQueryManual = QRadioButton(DevicePanel)
        self.buttonGroupQueryMode = QButtonGroup(DevicePanel)
        self.buttonGroupQueryMode.setObjectName("buttonGroupQueryMode")
        self.buttonGroupQueryMode.addButton(self.radioQueryManual)
        self.radioQueryManual.setObjectName("radioQueryManual")
        self.radioQueryManual.setChecked(True)

        self.layoutQueryMode.addWidget(self.radioQueryManual)

        self.radioQueryAuto = QRadioButton(DevicePanel)
        self.buttonGroupQueryMode.addButton(self.radioQueryAuto)
        self.radioQueryAuto.setObjectName("radioQueryAuto")

        self.layoutQueryMode.addWidget(self.radioQueryAuto)

        self.layoutDevicePanel.addLayout(self.layoutQueryMode, 1, 1, 1, 1)

        self.labelDuration = QLabel(DevicePanel)
        self.labelDuration.setObjectName("labelDuration")
        sizePolicy.setHeightForWidth(
            self.labelDuration.sizePolicy().hasHeightForWidth()
        )
        self.labelDuration.setSizePolicy(sizePolicy)

        self.layoutDevicePanel.addWidget(self.labelDuration, 2, 0, 1, 1)

        self.comboDuration = QComboBox(DevicePanel)
        self.comboDuration.addItem("")
        self.comboDuration.addItem("")
        self.comboDuration.addItem("")
        self.comboDuration.addItem("")
        self.comboDuration.addItem("")
        self.comboDuration.addItem("")
        self.comboDuration.setObjectName("comboDuration")
        sizePolicy1 = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(
            self.comboDuration.sizePolicy().hasHeightForWidth()
        )
        self.comboDuration.setSizePolicy(sizePolicy1)
        self.comboDuration.setEditable(True)
        self.comboDuration.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        self.layoutDevicePanel.addWidget(self.comboDuration, 2, 1, 1, 1)

        self.labelVoltage = QLabel(DevicePanel)
        self.labelVoltage.setObjectName("labelVoltage")
        sizePolicy.setHeightForWidth(self.labelVoltage.sizePolicy().hasHeightForWidth())
        self.labelVoltage.setSizePolicy(sizePolicy)

        self.layoutDevicePanel.addWidget(self.labelVoltage, 3, 0, 1, 1)

        self.spinVoltage = QSpinBox(DevicePanel)
        self.spinVoltage.setObjectName("spinVoltage")
        sizePolicy1.setHeightForWidth(self.spinVoltage.sizePolicy().hasHeightForWidth())
        self.spinVoltage.setSizePolicy(sizePolicy1)
        self.spinVoltage.setMinimumSize(QSize(0, 28))
        self.spinVoltage.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.spinVoltage.setMinimum(300)
        self.spinVoltage.setMaximum(700)
        self.spinVoltage.setSingleStep(10)
        self.spinVoltage.setValue(500)

        self.layoutDevicePanel.addWidget(self.spinVoltage, 3, 1, 1, 1)

        self.dialVoltage = QDial(DevicePanel)
        self.dialVoltage.setObjectName("dialVoltage")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.dialVoltage.sizePolicy().hasHeightForWidth())
        self.dialVoltage.setSizePolicy(sizePolicy2)
        self.dialVoltage.setMinimumSize(QSize(90, 90))
        self.dialVoltage.setMaximumSize(QSize(90, 90))
        self.dialVoltage.setMinimum(300)
        self.dialVoltage.setMaximum(700)
        self.dialVoltage.setSingleStep(5)
        self.dialVoltage.setPageStep(10)
        self.dialVoltage.setValue(500)
        self.dialVoltage.setWrapping(False)
        self.dialVoltage.setNotchesVisible(True)

        self.layoutDevicePanel.addWidget(self.dialVoltage, 4, 0, 1, 2, Qt.AlignHCenter)

        self.buttonApply = QPushButton(DevicePanel)
        self.buttonApply.setObjectName("buttonApply")
        self.buttonApply.setMinimumSize(QSize(0, 28))
        self.buttonApply.setAutoDefault(False)

        self.layoutDevicePanel.addWidget(self.buttonApply, 5, 0, 1, 2)

        self.retranslateUi(DevicePanel)

        self.comboDuration.setCurrentIndex(0)

        QMetaObject.connectSlotsByName(DevicePanel)

    # setupUi

    def retranslateUi(self, DevicePanel):
        DevicePanel.setTitle(
            QCoreApplication.translate("DevicePanel", "Ger\u00e4testeuerung", None)
        )
        self.labelCountMode.setText(
            QCoreApplication.translate("DevicePanel", "Z\u00e4hlmodus", None)
        )
        self.radioModeSingle.setText(
            QCoreApplication.translate("DevicePanel", "Einzel", None)
        )
        # if QT_CONFIG(tooltip)
        self.radioModeSingle.setToolTip(
            QCoreApplication.translate(
                "DevicePanel", "Stoppt die Messung nach Ablauf der Z\u00e4hldauer", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.radioModeRepeat.setText(
            QCoreApplication.translate("DevicePanel", "Wiederholung", None)
        )
        # if QT_CONFIG(tooltip)
        self.radioModeRepeat.setToolTip(
            QCoreApplication.translate(
                "DevicePanel",
                "Wiederholt die Messung automatisch nach Ablauf der Z\u00e4hldauer",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.labelQueryMode.setText(
            QCoreApplication.translate("DevicePanel", "Abfragemodus", None)
        )
        self.radioQueryManual.setText(
            QCoreApplication.translate("DevicePanel", "Manuell", None)
        )
        # if QT_CONFIG(tooltip)
        self.radioQueryManual.setToolTip(
            QCoreApplication.translate(
                "DevicePanel",
                "Z\u00e4hlergebnisse werden nur auf Anfrage gelesen",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.radioQueryAuto.setText(
            QCoreApplication.translate("DevicePanel", "Automatik", None)
        )
        # if QT_CONFIG(tooltip)
        self.radioQueryAuto.setToolTip(
            QCoreApplication.translate(
                "DevicePanel",
                "Das Ger\u00e4t sendet die Z\u00e4hlergebnisse fortlaufend",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.labelDuration.setText(
            QCoreApplication.translate("DevicePanel", "Z\u00e4hldauer", None)
        )
        self.comboDuration.setItemText(
            0, QCoreApplication.translate("DevicePanel", "unendlich", None)
        )
        self.comboDuration.setItemText(
            1, QCoreApplication.translate("DevicePanel", "1 Sekunde", None)
        )
        self.comboDuration.setItemText(
            2, QCoreApplication.translate("DevicePanel", "10 Sekunden", None)
        )
        self.comboDuration.setItemText(
            3, QCoreApplication.translate("DevicePanel", "60 Sekunden", None)
        )
        self.comboDuration.setItemText(
            4, QCoreApplication.translate("DevicePanel", "100 Sekunden", None)
        )
        self.comboDuration.setItemText(
            5, QCoreApplication.translate("DevicePanel", "300 Sekunden", None)
        )

        # if QT_CONFIG(tooltip)
        self.comboDuration.setToolTip(
            QCoreApplication.translate(
                "DevicePanel",
                "Wie lange der Z\u00e4hler misst; eine eigene Dauer in Sekunden kann eingetippt werden",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.labelVoltage.setText(
            QCoreApplication.translate("DevicePanel", "GM-Spannung", None)
        )
        self.spinVoltage.setSuffix(
            QCoreApplication.translate("DevicePanel", " V", None)
        )
        # if QT_CONFIG(tooltip)
        self.spinVoltage.setToolTip(
            QCoreApplication.translate(
                "DevicePanel", "Betriebsspannung des Z\u00e4hlrohrs", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        # if QT_CONFIG(tooltip)
        self.dialVoltage.setToolTip(
            QCoreApplication.translate(
                "DevicePanel", "Betriebsspannung des Z\u00e4hlrohrs", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.buttonApply.setText(
            QCoreApplication.translate(
                "DevicePanel", "Einstellungen \u00fcbernehmen", None
            )
        )
        # if QT_CONFIG(tooltip)
        self.buttonApply.setToolTip(
            QCoreApplication.translate(
                "DevicePanel",
                "Spannung, Modus und Abfragemodus an das Ger\u00e4t senden",
                None,
            )
        )


# endif // QT_CONFIG(tooltip)
# retranslateUi
