# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'sample_panel.ui'
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
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QWidget,
)


class Ui_SamplePanel(object):
    def setupUi(self, SamplePanel):
        if not SamplePanel.objectName():
            SamplePanel.setObjectName("SamplePanel")
        SamplePanel.resize(260, 200)
        self.layoutSamplePanel = QGridLayout(SamplePanel)
        self.layoutSamplePanel.setSpacing(6)
        self.layoutSamplePanel.setObjectName("layoutSamplePanel")
        self.labelSample = QLabel(SamplePanel)
        self.labelSample.setObjectName("labelSample")
        sizePolicy = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.labelSample.sizePolicy().hasHeightForWidth())
        self.labelSample.setSizePolicy(sizePolicy)

        self.layoutSamplePanel.addWidget(self.labelSample, 0, 0, 1, 1)

        self.comboSample = QComboBox(SamplePanel)
        self.comboSample.setObjectName("comboSample")
        sizePolicy1 = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.comboSample.sizePolicy().hasHeightForWidth())
        self.comboSample.setSizePolicy(sizePolicy1)
        self.comboSample.setEditable(True)
        self.comboSample.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        self.layoutSamplePanel.addWidget(self.comboSample, 0, 1, 1, 1)

        self.labelGroup = QLabel(SamplePanel)
        self.labelGroup.setObjectName("labelGroup")
        sizePolicy.setHeightForWidth(self.labelGroup.sizePolicy().hasHeightForWidth())
        self.labelGroup.setSizePolicy(sizePolicy)

        self.layoutSamplePanel.addWidget(self.labelGroup, 1, 0, 1, 1)

        self.comboGroup = QComboBox(SamplePanel)
        self.comboGroup.addItem("")
        self.comboGroup.addItem("")
        self.comboGroup.addItem("")
        self.comboGroup.addItem("")
        self.comboGroup.addItem("")
        self.comboGroup.addItem("")
        self.comboGroup.addItem("")
        self.comboGroup.addItem("")
        self.comboGroup.addItem("")
        self.comboGroup.addItem("")
        self.comboGroup.addItem("")
        self.comboGroup.addItem("")
        self.comboGroup.addItem("")
        self.comboGroup.addItem("")
        self.comboGroup.addItem("")
        self.comboGroup.addItem("")
        self.comboGroup.addItem("")
        self.comboGroup.addItem("")
        self.comboGroup.addItem("")
        self.comboGroup.addItem("")
        self.comboGroup.addItem("")
        self.comboGroup.addItem("")
        self.comboGroup.addItem("")
        self.comboGroup.addItem("")
        self.comboGroup.setObjectName("comboGroup")
        sizePolicy1.setHeightForWidth(self.comboGroup.sizePolicy().hasHeightForWidth())
        self.comboGroup.setSizePolicy(sizePolicy1)
        self.comboGroup.setMaxCount(24)
        self.comboGroup.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        self.layoutSamplePanel.addWidget(self.comboGroup, 1, 1, 1, 1)

        self.labelDetector = QLabel(SamplePanel)
        self.labelDetector.setObjectName("labelDetector")
        sizePolicy.setHeightForWidth(
            self.labelDetector.sizePolicy().hasHeightForWidth()
        )
        self.labelDetector.setSizePolicy(sizePolicy)

        self.layoutSamplePanel.addWidget(self.labelDetector, 2, 0, 1, 1)

        self.comboDetector = QComboBox(SamplePanel)
        self.comboDetector.setObjectName("comboDetector")
        sizePolicy1.setHeightForWidth(
            self.comboDetector.sizePolicy().hasHeightForWidth()
        )
        self.comboDetector.setSizePolicy(sizePolicy1)
        self.comboDetector.setEditable(True)
        self.comboDetector.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        self.layoutSamplePanel.addWidget(self.comboDetector, 2, 1, 1, 1)

        self.labelDistance = QLabel(SamplePanel)
        self.labelDistance.setObjectName("labelDistance")
        sizePolicy.setHeightForWidth(
            self.labelDistance.sizePolicy().hasHeightForWidth()
        )
        self.labelDistance.setSizePolicy(sizePolicy)

        self.layoutSamplePanel.addWidget(self.labelDistance, 3, 0, 1, 1)

        self.spinDistance = QDoubleSpinBox(SamplePanel)
        self.spinDistance.setObjectName("spinDistance")
        sizePolicy1.setHeightForWidth(
            self.spinDistance.sizePolicy().hasHeightForWidth()
        )
        self.spinDistance.setSizePolicy(sizePolicy1)
        self.spinDistance.setDecimals(1)
        self.spinDistance.setMaximum(100.000000000000000)
        self.spinDistance.setSingleStep(0.500000000000000)

        self.layoutSamplePanel.addWidget(self.spinDistance, 3, 1, 1, 1)

        self.checkAutoSave = QCheckBox(SamplePanel)
        self.checkAutoSave.setObjectName("checkAutoSave")
        self.checkAutoSave.setChecked(False)

        self.layoutSamplePanel.addWidget(self.checkAutoSave, 4, 0, 1, 2)

        self.labelSuffix = QLabel(SamplePanel)
        self.labelSuffix.setObjectName("labelSuffix")
        sizePolicy.setHeightForWidth(self.labelSuffix.sizePolicy().hasHeightForWidth())
        self.labelSuffix.setSizePolicy(sizePolicy)

        self.layoutSamplePanel.addWidget(self.labelSuffix, 5, 0, 1, 1)

        self.editSuffix = QLineEdit(SamplePanel)
        self.editSuffix.setObjectName("editSuffix")
        sizePolicy1.setHeightForWidth(self.editSuffix.sizePolicy().hasHeightForWidth())
        self.editSuffix.setSizePolicy(sizePolicy1)
        self.editSuffix.setMaxLength(20)

        self.layoutSamplePanel.addWidget(self.editSuffix, 5, 1, 1, 1)

        self.retranslateUi(SamplePanel)

        self.comboSample.setCurrentIndex(-1)
        self.comboGroup.setCurrentIndex(-1)
        self.comboDetector.setCurrentIndex(-1)

        QMetaObject.connectSlotsByName(SamplePanel)

    # setupUi

    def retranslateUi(self, SamplePanel):
        SamplePanel.setTitle(
            QCoreApplication.translate("SamplePanel", "Probe && Speicherung", None)
        )
        self.labelSample.setText(
            QCoreApplication.translate("SamplePanel", "Radioaktive Probe*", None)
        )
        # if QT_CONFIG(tooltip)
        self.comboSample.setToolTip(
            QCoreApplication.translate(
                "SamplePanel",
                "Auswahl der verwendeten radioaktiven Probe (Pflichtfeld)",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.labelGroup.setText(
            QCoreApplication.translate("SamplePanel", "Gruppe*", None)
        )
        self.comboGroup.setItemText(
            0, QCoreApplication.translate("SamplePanel", "A", None)
        )
        self.comboGroup.setItemText(
            1, QCoreApplication.translate("SamplePanel", "B", None)
        )
        self.comboGroup.setItemText(
            2, QCoreApplication.translate("SamplePanel", "C", None)
        )
        self.comboGroup.setItemText(
            3, QCoreApplication.translate("SamplePanel", "D", None)
        )
        self.comboGroup.setItemText(
            4, QCoreApplication.translate("SamplePanel", "E", None)
        )
        self.comboGroup.setItemText(
            5, QCoreApplication.translate("SamplePanel", "F", None)
        )
        self.comboGroup.setItemText(
            6, QCoreApplication.translate("SamplePanel", "G", None)
        )
        self.comboGroup.setItemText(
            7, QCoreApplication.translate("SamplePanel", "H", None)
        )
        self.comboGroup.setItemText(
            8, QCoreApplication.translate("SamplePanel", "I", None)
        )
        self.comboGroup.setItemText(
            9, QCoreApplication.translate("SamplePanel", "J", None)
        )
        self.comboGroup.setItemText(
            10, QCoreApplication.translate("SamplePanel", "K", None)
        )
        self.comboGroup.setItemText(
            11, QCoreApplication.translate("SamplePanel", "L", None)
        )
        self.comboGroup.setItemText(
            12, QCoreApplication.translate("SamplePanel", "M", None)
        )
        self.comboGroup.setItemText(
            13, QCoreApplication.translate("SamplePanel", "N", None)
        )
        self.comboGroup.setItemText(
            14, QCoreApplication.translate("SamplePanel", "O", None)
        )
        self.comboGroup.setItemText(
            15, QCoreApplication.translate("SamplePanel", "P", None)
        )
        self.comboGroup.setItemText(
            16, QCoreApplication.translate("SamplePanel", "Q", None)
        )
        self.comboGroup.setItemText(
            17, QCoreApplication.translate("SamplePanel", "R", None)
        )
        self.comboGroup.setItemText(
            18, QCoreApplication.translate("SamplePanel", "S", None)
        )
        self.comboGroup.setItemText(
            19, QCoreApplication.translate("SamplePanel", "T", None)
        )
        self.comboGroup.setItemText(
            20, QCoreApplication.translate("SamplePanel", "U", None)
        )
        self.comboGroup.setItemText(
            21, QCoreApplication.translate("SamplePanel", "V", None)
        )
        self.comboGroup.setItemText(
            22, QCoreApplication.translate("SamplePanel", "W", None)
        )
        self.comboGroup.setItemText(
            23, QCoreApplication.translate("SamplePanel", "Z", None)
        )

        # if QT_CONFIG(tooltip)
        self.comboGroup.setToolTip(
            QCoreApplication.translate(
                "SamplePanel", "Auswahl der GP-Praktikumsgruppe (Pflichtfeld)", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.labelDetector.setText(
            QCoreApplication.translate("SamplePanel", "Detektor*", None)
        )
        # if QT_CONFIG(tooltip)
        self.comboDetector.setToolTip(
            QCoreApplication.translate(
                "SamplePanel",
                "Auswahl des verwendeten Detektors (Geiger-M\u00fcller-Z\u00e4hlrohr, Pflichtfeld)",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.labelDistance.setText(
            QCoreApplication.translate("SamplePanel", "Probenabstand", None)
        )
        self.spinDistance.setSuffix(
            QCoreApplication.translate("SamplePanel", " cm", None)
        )
        # if QT_CONFIG(tooltip)
        self.spinDistance.setToolTip(
            QCoreApplication.translate(
                "SamplePanel",
                "Abstand zwischen Detektoroberfl\u00e4che und radioaktiver Probe in cm",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.checkAutoSave.setText(
            QCoreApplication.translate("SamplePanel", "Automatische Speicherung", None)
        )
        # if QT_CONFIG(tooltip)
        self.checkAutoSave.setToolTip(
            QCoreApplication.translate(
                "SamplePanel",
                "Bei Aktivierung werden die Messungen automatisch als JJJJ_MM_TT-Probe-Suffix.csv im Ordner Dokumente/Geiger-Mueller/ gespeichert",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.labelSuffix.setText(
            QCoreApplication.translate("SamplePanel", "Eigenes Suffix", None)
        )
        # if QT_CONFIG(tooltip)
        self.editSuffix.setToolTip(
            QCoreApplication.translate(
                "SamplePanel",
                "Ein benutzerdefiniertes Suffix mit maximal 20 Zeichen",
                None,
            )
        )


# endif // QT_CONFIG(tooltip)
# retranslateUi
