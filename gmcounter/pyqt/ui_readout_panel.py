# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'readout_panel.ui'
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


class Ui_ReadoutPanel(object):
    def setupUi(self, ReadoutPanel):
        if not ReadoutPanel.objectName():
            ReadoutPanel.setObjectName("ReadoutPanel")
        ReadoutPanel.resize(260, 200)
        self.layoutReadoutPanel = QGridLayout(ReadoutPanel)
        self.layoutReadoutPanel.setSpacing(4)
        self.layoutReadoutPanel.setObjectName("layoutReadoutPanel")
        self.labelCount = QLabel(ReadoutPanel)
        self.labelCount.setObjectName("labelCount")
        sizePolicy = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.labelCount.sizePolicy().hasHeightForWidth())
        self.labelCount.setSizePolicy(sizePolicy)

        self.layoutReadoutPanel.addWidget(self.labelCount, 0, 0, 1, 1)

        self.lcdCount = QLCDNumber(ReadoutPanel)
        self.lcdCount.setObjectName("lcdCount")
        sizePolicy1 = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.lcdCount.sizePolicy().hasHeightForWidth())
        self.lcdCount.setSizePolicy(sizePolicy1)
        self.lcdCount.setMinimumSize(QSize(120, 52))
        self.lcdCount.setDigitCount(8)
        self.lcdCount.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)

        self.layoutReadoutPanel.addWidget(self.lcdCount, 1, 0, 1, 1)

        self.labelRate = QLabel(ReadoutPanel)
        self.labelRate.setObjectName("labelRate")
        sizePolicy.setHeightForWidth(self.labelRate.sizePolicy().hasHeightForWidth())
        self.labelRate.setSizePolicy(sizePolicy)

        self.layoutReadoutPanel.addWidget(self.labelRate, 2, 0, 1, 1)

        self.lcdRate = QLCDNumber(ReadoutPanel)
        self.lcdRate.setObjectName("lcdRate")
        sizePolicy1.setHeightForWidth(self.lcdRate.sizePolicy().hasHeightForWidth())
        self.lcdRate.setSizePolicy(sizePolicy1)
        self.lcdRate.setMinimumSize(QSize(120, 52))
        self.lcdRate.setDigitCount(8)
        self.lcdRate.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)

        self.layoutReadoutPanel.addWidget(self.lcdRate, 3, 0, 1, 1)

        self.labelLastCount = QLabel(ReadoutPanel)
        self.labelLastCount.setObjectName("labelLastCount")
        sizePolicy.setHeightForWidth(
            self.labelLastCount.sizePolicy().hasHeightForWidth()
        )
        self.labelLastCount.setSizePolicy(sizePolicy)

        self.layoutReadoutPanel.addWidget(self.labelLastCount, 4, 0, 1, 1)

        self.lcdLastCount = QLCDNumber(ReadoutPanel)
        self.lcdLastCount.setObjectName("lcdLastCount")
        sizePolicy1.setHeightForWidth(
            self.lcdLastCount.sizePolicy().hasHeightForWidth()
        )
        self.lcdLastCount.setSizePolicy(sizePolicy1)
        self.lcdLastCount.setMinimumSize(QSize(120, 52))
        self.lcdLastCount.setDigitCount(8)
        self.lcdLastCount.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)

        self.layoutReadoutPanel.addWidget(self.lcdLastCount, 5, 0, 1, 1)

        self.layoutHighSpeed = QHBoxLayout()
        self.layoutHighSpeed.setObjectName("layoutHighSpeed")
        self.labelHighSpeed = QLabel(ReadoutPanel)
        self.labelHighSpeed.setObjectName("labelHighSpeed")
        sizePolicy.setHeightForWidth(
            self.labelHighSpeed.sizePolicy().hasHeightForWidth()
        )
        self.labelHighSpeed.setSizePolicy(sizePolicy)

        self.layoutHighSpeed.addWidget(self.labelHighSpeed)

        self.ledHighSpeed = StatusLed(ReadoutPanel)
        self.ledHighSpeed.setObjectName("ledHighSpeed")

        self.layoutHighSpeed.addWidget(self.ledHighSpeed)

        self.valueHighSpeed = QLabel(ReadoutPanel)
        self.valueHighSpeed.setObjectName("valueHighSpeed")
        sizePolicy2 = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(
            self.valueHighSpeed.sizePolicy().hasHeightForWidth()
        )
        self.valueHighSpeed.setSizePolicy(sizePolicy2)

        self.layoutHighSpeed.addWidget(self.valueHighSpeed)

        self.layoutReadoutPanel.addLayout(self.layoutHighSpeed, 6, 0, 1, 1)

        self.retranslateUi(ReadoutPanel)

        QMetaObject.connectSlotsByName(ReadoutPanel)

    # setupUi

    def retranslateUi(self, ReadoutPanel):
        ReadoutPanel.setTitle(
            QCoreApplication.translate("ReadoutPanel", "Live-Werte", None)
        )
        self.labelCount.setText(
            QCoreApplication.translate(
                "ReadoutPanel", "Aktuelles Z\u00e4hlergebnis", None
            )
        )
        self.labelRate.setText(
            QCoreApplication.translate("ReadoutPanel", "Z\u00e4hlrate / Hz", None)
        )
        self.labelLastCount.setText(
            QCoreApplication.translate(
                "ReadoutPanel", "Voriges Z\u00e4hlergebnis", None
            )
        )
        self.labelHighSpeed.setText(
            QCoreApplication.translate("ReadoutPanel", "High-Speed-Modus", None)
        )
        # if QT_CONFIG(tooltip)
        self.ledHighSpeed.setToolTip(
            QCoreApplication.translate(
                "ReadoutPanel",
                "Leuchtet, solange nur das Histogramm aktualisiert wird (hohe Ereignisrate)",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.valueHighSpeed.setText(
            QCoreApplication.translate("ReadoutPanel", "inaktiv", None)
        )

    # retranslateUi
