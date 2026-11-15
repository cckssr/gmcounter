# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'measurement_panel.ui'
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
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QWidget,
)


class Ui_MeasurementPanel(object):
    def setupUi(self, MeasurementPanel):
        if not MeasurementPanel.objectName():
            MeasurementPanel.setObjectName("MeasurementPanel")
        MeasurementPanel.resize(194, 125)
        self.layoutMeasurementPanel = QGridLayout(MeasurementPanel)
        self.layoutMeasurementPanel.setSpacing(8)
        self.layoutMeasurementPanel.setObjectName("layoutMeasurementPanel")
        self.buttonStart = QPushButton(MeasurementPanel)
        self.buttonStart.setObjectName("buttonStart")
        self.buttonStart.setEnabled(True)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonStart.sizePolicy().hasHeightForWidth())
        self.buttonStart.setSizePolicy(sizePolicy)
        self.buttonStart.setMinimumSize(QSize(0, 28))
        # if QT_CONFIG(shortcut)
        self.buttonStart.setShortcut("F5")
        # endif // QT_CONFIG(shortcut)
        self.buttonStart.setAutoDefault(False)

        self.layoutMeasurementPanel.addWidget(self.buttonStart, 0, 0, 1, 1)

        self.buttonStop = QPushButton(MeasurementPanel)
        self.buttonStop.setObjectName("buttonStop")
        self.buttonStop.setEnabled(False)
        sizePolicy.setHeightForWidth(self.buttonStop.sizePolicy().hasHeightForWidth())
        self.buttonStop.setSizePolicy(sizePolicy)
        self.buttonStop.setMinimumSize(QSize(0, 28))
        # if QT_CONFIG(shortcut)
        self.buttonStop.setShortcut("F6")
        # endif // QT_CONFIG(shortcut)
        self.buttonStop.setAutoDefault(False)

        self.layoutMeasurementPanel.addWidget(self.buttonStop, 0, 1, 1, 1)

        self.buttonSave = QPushButton(MeasurementPanel)
        self.buttonSave.setObjectName("buttonSave")
        self.buttonSave.setEnabled(False)
        sizePolicy.setHeightForWidth(self.buttonSave.sizePolicy().hasHeightForWidth())
        self.buttonSave.setSizePolicy(sizePolicy)
        self.buttonSave.setMinimumSize(QSize(0, 28))
        self.buttonSave.setAutoDefault(False)

        self.layoutMeasurementPanel.addWidget(self.buttonSave, 1, 0, 1, 1)

        self.buttonReset = QPushButton(MeasurementPanel)
        self.buttonReset.setObjectName("buttonReset")
        self.buttonReset.setEnabled(False)
        sizePolicy.setHeightForWidth(self.buttonReset.sizePolicy().hasHeightForWidth())
        self.buttonReset.setSizePolicy(sizePolicy)
        self.buttonReset.setMinimumSize(QSize(0, 28))
        self.buttonReset.setAutoDefault(False)

        self.layoutMeasurementPanel.addWidget(self.buttonReset, 1, 1, 1, 1)

        self.layoutProgress = QHBoxLayout()
        self.layoutProgress.setObjectName("layoutProgress")
        self.progressMeasurement = QProgressBar(MeasurementPanel)
        self.progressMeasurement.setObjectName("progressMeasurement")
        sizePolicy1 = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(
            self.progressMeasurement.sizePolicy().hasHeightForWidth()
        )
        self.progressMeasurement.setSizePolicy(sizePolicy1)
        self.progressMeasurement.setMinimum(0)
        self.progressMeasurement.setMaximum(1)
        self.progressMeasurement.setValue(0)
        self.progressMeasurement.setTextVisible(False)

        self.layoutProgress.addWidget(self.progressMeasurement)

        self.valueElapsed = QLabel(MeasurementPanel)
        self.valueElapsed.setObjectName("valueElapsed")
        sizePolicy2 = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(
            self.valueElapsed.sizePolicy().hasHeightForWidth()
        )
        self.valueElapsed.setSizePolicy(sizePolicy2)
        self.valueElapsed.setMinimumSize(QSize(48, 0))

        self.layoutProgress.addWidget(self.valueElapsed)

        self.layoutMeasurementPanel.addLayout(self.layoutProgress, 2, 0, 1, 2)

        self.retranslateUi(MeasurementPanel)

        QMetaObject.connectSlotsByName(MeasurementPanel)

    # setupUi

    def retranslateUi(self, MeasurementPanel):
        MeasurementPanel.setTitle(
            QCoreApplication.translate("MeasurementPanel", "Messung", None)
        )
        # if QT_CONFIG(tooltip)
        self.buttonStart.setToolTip(
            QCoreApplication.translate("MeasurementPanel", "Messung starten (F5)", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.buttonStart.setText(
            QCoreApplication.translate("MeasurementPanel", "Start", None)
        )
        # if QT_CONFIG(tooltip)
        self.buttonStop.setToolTip(
            QCoreApplication.translate(
                "MeasurementPanel", "Aktuelle Messung stoppen (F6)", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.buttonStop.setText(
            QCoreApplication.translate("MeasurementPanel", "Stop", None)
        )
        # if QT_CONFIG(tooltip)
        self.buttonSave.setToolTip(
            QCoreApplication.translate(
                "MeasurementPanel", "Messung speichern (Dateidialog)", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.buttonSave.setText(
            QCoreApplication.translate("MeasurementPanel", "Speichern", None)
        )
        # if QT_CONFIG(tooltip)
        self.buttonReset.setToolTip(
            QCoreApplication.translate(
                "MeasurementPanel", "Messdaten verwerfen und zur\u00fccksetzen", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.buttonReset.setText(
            QCoreApplication.translate("MeasurementPanel", "Reset", None)
        )
        self.valueElapsed.setText(
            QCoreApplication.translate("MeasurementPanel", "0 s", None)
        )

    # retranslateUi
