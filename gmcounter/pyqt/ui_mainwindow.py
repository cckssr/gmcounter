# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainwindow.ui'
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
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDial,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLCDNumber,
    QLabel,
    QLayout,
    QLineEdit,
    QMainWindow,
    QMenuBar,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QStatusBar,
    QTabWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1280, 929)
        font = QFont()
        font.setPointSize(10)
        MainWindow.setFont(font)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_5 = QGridLayout(self.centralwidget)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.gridLayout_5.setContentsMargins(10, -1, -1, 10)
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout_2.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.verticalLayout_2.setContentsMargins(0, -1, -1, 0)
        self.settings = QGroupBox(self.centralwidget)
        self.settings.setObjectName("settings")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.settings.sizePolicy().hasHeightForWidth())
        self.settings.setSizePolicy(sizePolicy)
        self.settings.setMaximumSize(QSize(1000, 16777215))
        font1 = QFont()
        font1.setPointSize(11)
        self.settings.setFont(font1)
        self.settings.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.formLayout = QFormLayout(self.settings)
        self.formLayout.setObjectName("formLayout")
        self.formLayout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.formLayout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )
        self.formLayout.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignTrailing
            | Qt.AlignmentFlag.AlignVCenter
        )
        self.formLayout.setFormAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignTop
        )
        self.formLayout.setContentsMargins(-1, 12, -1, -1)
        self.mode_label = QLabel(self.settings)
        self.mode_label.setObjectName("mode_label")
        sizePolicy1 = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
        )
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.mode_label.sizePolicy().hasHeightForWidth())
        self.mode_label.setSizePolicy(sizePolicy1)
        self.mode_label.setFont(font1)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.mode_label)

        self.sMode = QHBoxLayout()
        self.sMode.setObjectName("sMode")
        self.sMode.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.sMode.setContentsMargins(-1, -1, 0, -1)
        self.sModeSingle = QRadioButton(self.settings)
        self.groupMode = QButtonGroup(MainWindow)
        self.groupMode.setObjectName("groupMode")
        self.groupMode.addButton(self.sModeSingle)
        self.sModeSingle.setObjectName("sModeSingle")
        sizePolicy.setHeightForWidth(self.sModeSingle.sizePolicy().hasHeightForWidth())
        self.sModeSingle.setSizePolicy(sizePolicy)
        self.sModeSingle.setFont(font1)
        self.sModeSingle.setChecked(True)

        self.sMode.addWidget(self.sModeSingle)

        self.sModeMulti = QRadioButton(self.settings)
        self.groupMode.addButton(self.sModeMulti)
        self.sModeMulti.setObjectName("sModeMulti")
        sizePolicy2 = QSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum
        )
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.sModeMulti.sizePolicy().hasHeightForWidth())
        self.sModeMulti.setSizePolicy(sizePolicy2)
        self.sModeMulti.setFont(font1)

        self.sMode.addWidget(self.sModeMulti)

        self.formLayout.setLayout(0, QFormLayout.ItemRole.FieldRole, self.sMode)

        self.label_10 = QLabel(self.settings)
        self.label_10.setObjectName("label_10")
        sizePolicy1.setHeightForWidth(self.label_10.sizePolicy().hasHeightForWidth())
        self.label_10.setSizePolicy(sizePolicy1)
        self.label_10.setMinimumSize(QSize(0, 20))
        self.label_10.setFont(font1)
        self.label_10.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_10)

        self.sQueryMode = QHBoxLayout()
        self.sQueryMode.setObjectName("sQueryMode")
        self.sQueryMode.setSizeConstraint(QLayout.SizeConstraint.SetMaximumSize)
        self.sQModeMan = QRadioButton(self.settings)
        self.groupQMode = QButtonGroup(MainWindow)
        self.groupQMode.setObjectName("groupQMode")
        self.groupQMode.addButton(self.sQModeMan)
        self.sQModeMan.setObjectName("sQModeMan")
        self.sQModeMan.setEnabled(False)
        sizePolicy.setHeightForWidth(self.sQModeMan.sizePolicy().hasHeightForWidth())
        self.sQModeMan.setSizePolicy(sizePolicy)
        self.sQModeMan.setFont(font1)
        self.sQModeMan.setChecked(False)

        self.sQueryMode.addWidget(self.sQModeMan)

        self.sQModeAuto = QRadioButton(self.settings)
        self.groupQMode.addButton(self.sQModeAuto)
        self.sQModeAuto.setObjectName("sQModeAuto")
        self.sQModeAuto.setEnabled(False)
        sizePolicy3 = QSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum
        )
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.sQModeAuto.sizePolicy().hasHeightForWidth())
        self.sQModeAuto.setSizePolicy(sizePolicy3)
        self.sQModeAuto.setFont(font1)
        self.sQModeAuto.setChecked(True)

        self.sQueryMode.addWidget(self.sQModeAuto)

        self.formLayout.setLayout(1, QFormLayout.ItemRole.FieldRole, self.sQueryMode)

        self.duration_label = QLabel(self.settings)
        self.duration_label.setObjectName("duration_label")
        sizePolicy4 = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(
            self.duration_label.sizePolicy().hasHeightForWidth()
        )
        self.duration_label.setSizePolicy(sizePolicy4)
        self.duration_label.setFont(font1)

        self.formLayout.setWidget(
            2, QFormLayout.ItemRole.LabelRole, self.duration_label
        )

        self.sDuration = QComboBox(self.settings)
        self.sDuration.addItem("")
        self.sDuration.addItem("")
        self.sDuration.addItem("")
        self.sDuration.addItem("")
        self.sDuration.addItem("")
        self.sDuration.addItem("")
        self.sDuration.setObjectName("sDuration")
        sizePolicy5 = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum
        )
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.sDuration.sizePolicy().hasHeightForWidth())
        self.sDuration.setSizePolicy(sizePolicy5)
        self.sDuration.setFont(font1)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.sDuration)

        self.volt_label = QLabel(self.settings)
        self.volt_label.setObjectName("volt_label")
        sizePolicy6 = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding
        )
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.volt_label.sizePolicy().hasHeightForWidth())
        self.volt_label.setSizePolicy(sizePolicy6)
        self.volt_label.setMinimumSize(QSize(0, 100))
        self.volt_label.setMaximumSize(QSize(16777215, 100))
        self.volt_label.setFont(font1)

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.volt_label)

        self.sVolt = QHBoxLayout()
        self.sVolt.setObjectName("sVolt")
        self.sVolt.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.sVolt.setContentsMargins(-1, -1, 0, -1)
        self.sVoltage = QSpinBox(self.settings)
        self.sVoltage.setObjectName("sVoltage")
        sizePolicy7 = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        sizePolicy7.setHorizontalStretch(0)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(self.sVoltage.sizePolicy().hasHeightForWidth())
        self.sVoltage.setSizePolicy(sizePolicy7)
        self.sVoltage.setMinimumSize(QSize(0, 40))
        self.sVoltage.setFont(font1)
        self.sVoltage.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.sVoltage.setMinimum(300)
        self.sVoltage.setMaximum(700)
        self.sVoltage.setSingleStep(10)
        self.sVoltage.setValue(500)

        self.sVolt.addWidget(self.sVoltage)

        self.voltDial = QDial(self.settings)
        self.voltDial.setObjectName("voltDial")
        sizePolicy8 = QSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum
        )
        sizePolicy8.setHorizontalStretch(0)
        sizePolicy8.setVerticalStretch(0)
        sizePolicy8.setHeightForWidth(self.voltDial.sizePolicy().hasHeightForWidth())
        self.voltDial.setSizePolicy(sizePolicy8)
        self.voltDial.setMinimumSize(QSize(100, 100))
        self.voltDial.setMaximumSize(QSize(100, 100))
        self.voltDial.setFont(font1)
        self.voltDial.setStyleSheet("QDial {color: rgb(255, 38, 0);}")
        self.voltDial.setMinimum(300)
        self.voltDial.setMaximum(700)
        self.voltDial.setSingleStep(5)
        self.voltDial.setValue(500)
        self.voltDial.setWrapping(False)
        self.voltDial.setNotchesVisible(True)

        self.sVolt.addWidget(self.voltDial)

        self.formLayout.setLayout(3, QFormLayout.ItemRole.FieldRole, self.sVolt)

        self.buttonSetting = QPushButton(self.settings)
        self.buttonSetting.setObjectName("buttonSetting")
        self.buttonSetting.setEnabled(True)
        self.buttonSetting.setFont(font1)
        self.buttonSetting.setAutoDefault(False)

        self.formLayout.setWidget(
            4, QFormLayout.ItemRole.SpanningRole, self.buttonSetting
        )

        self.label_10.raise_()
        self.mode_label.raise_()
        self.duration_label.raise_()
        self.sDuration.raise_()
        self.volt_label.raise_()
        self.buttonSetting.raise_()

        self.verticalLayout_2.addWidget(self.settings)

        self.verticalSpacer = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.groupBox = QGroupBox(self.centralwidget)
        self.groupBox.setObjectName("groupBox")
        sizePolicy9 = QSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred
        )
        sizePolicy9.setHorizontalStretch(0)
        sizePolicy9.setVerticalStretch(0)
        sizePolicy9.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy9)
        self.groupBox.setMinimumSize(QSize(0, 50))
        self.groupBox.setFont(font1)
        self.groupBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.groupBox.setFlat(False)
        self.groupBox.setCheckable(False)
        self.verticalLayout = QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName("formLayout_2")
        self.formLayout_2.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )
        self.formLayout_2.setContentsMargins(-1, -1, 0, 0)
        self.label_6 = QLabel(self.groupBox)
        self.label_6.setObjectName("label_6")
        self.label_6.setFont(font1)

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_6)

        self.radSample = QComboBox(self.groupBox)
        self.radSample.setObjectName("radSample")
        sizePolicy10 = QSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed
        )
        sizePolicy10.setHorizontalStretch(0)
        sizePolicy10.setVerticalStretch(0)
        sizePolicy10.setHeightForWidth(self.radSample.sizePolicy().hasHeightForWidth())
        self.radSample.setSizePolicy(sizePolicy10)
        self.radSample.setFont(font1)
        self.radSample.setEditable(True)
        self.radSample.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.FieldRole, self.radSample)

        self.label_7 = QLabel(self.groupBox)
        self.label_7.setObjectName("label_7")
        self.label_7.setFont(font1)

        self.formLayout_2.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_7)

        self.groupLetter = QComboBox(self.groupBox)
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.setObjectName("groupLetter")
        sizePolicy10.setHeightForWidth(
            self.groupLetter.sizePolicy().hasHeightForWidth()
        )
        self.groupLetter.setSizePolicy(sizePolicy10)
        self.groupLetter.setFont(font1)
        self.groupLetter.setMaxCount(24)
        self.groupLetter.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        self.formLayout_2.setWidget(3, QFormLayout.ItemRole.FieldRole, self.groupLetter)

        self.label_5 = QLabel(self.groupBox)
        self.label_5.setObjectName("label_5")
        self.label_5.setFont(font1)

        self.formLayout_2.setWidget(4, QFormLayout.ItemRole.LabelRole, self.label_5)

        self.suffix = QLineEdit(self.groupBox)
        self.suffix.setObjectName("suffix")
        sizePolicy10.setHeightForWidth(self.suffix.sizePolicy().hasHeightForWidth())
        self.suffix.setSizePolicy(sizePolicy10)
        self.suffix.setFont(font1)
        self.suffix.setText("")
        self.suffix.setMaxLength(20)

        self.formLayout_2.setWidget(4, QFormLayout.ItemRole.FieldRole, self.suffix)

        self.label_20 = QLabel(self.groupBox)
        self.label_20.setObjectName("label_20")
        self.label_20.setFont(font1)

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_20)

        self.detectorCode = QComboBox(self.groupBox)
        self.detectorCode.setObjectName("detectorCode")
        sizePolicy10.setHeightForWidth(
            self.detectorCode.sizePolicy().hasHeightForWidth()
        )
        self.detectorCode.setSizePolicy(sizePolicy10)
        self.detectorCode.setFont(font1)
        self.detectorCode.setEditable(True)
        self.detectorCode.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        self.formLayout_2.setWidget(
            1, QFormLayout.ItemRole.FieldRole, self.detectorCode
        )

        self.lblDistance = QLabel(self.groupBox)
        self.lblDistance.setObjectName("lblDistance")
        self.lblDistance.setFont(font1)

        self.formLayout_2.setWidget(2, QFormLayout.ItemRole.LabelRole, self.lblDistance)

        self.distanceGlobalDistance = QDoubleSpinBox(self.groupBox)
        self.distanceGlobalDistance.setObjectName("distanceGlobalDistance")
        self.distanceGlobalDistance.setDecimals(1)

        self.formLayout_2.setWidget(
            2, QFormLayout.ItemRole.FieldRole, self.distanceGlobalDistance
        )

        self.verticalLayout.addLayout(self.formLayout_2)

        self.buttonSave = QPushButton(self.groupBox)
        self.buttonSave.setObjectName("buttonSave")
        self.buttonSave.setEnabled(False)
        sizePolicy11 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy11.setHorizontalStretch(0)
        sizePolicy11.setVerticalStretch(0)
        sizePolicy11.setHeightForWidth(self.buttonSave.sizePolicy().hasHeightForWidth())
        self.buttonSave.setSizePolicy(sizePolicy11)
        self.buttonSave.setMinimumSize(QSize(100, 30))
        self.buttonSave.setMaximumSize(QSize(1000, 40))
        self.buttonSave.setFont(font1)

        self.verticalLayout.addWidget(self.buttonSave)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(-1, -1, 0, 0)
        self.autoSave = QCheckBox(self.groupBox)
        self.autoSave.setObjectName("autoSave")
        sizePolicy12 = QSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum
        )
        sizePolicy12.setHorizontalStretch(0)
        sizePolicy12.setVerticalStretch(0)
        sizePolicy12.setHeightForWidth(self.autoSave.sizePolicy().hasHeightForWidth())
        self.autoSave.setSizePolicy(sizePolicy12)
        self.autoSave.setMaximumSize(QSize(850, 16777215))
        self.autoSave.setFont(font1)
        self.autoSave.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.autoSave.setChecked(False)
        self.autoSave.setTristate(False)

        self.horizontalLayout_5.addWidget(self.autoSave)

        self.verticalLayout.addLayout(self.horizontalLayout_5)

        self.verticalLayout_2.addWidget(self.groupBox)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setContentsMargins(2, 2, 2, 2)
        self.buttonStart = QPushButton(self.centralwidget)
        self.buttonStart.setObjectName("buttonStart")
        self.buttonStart.setEnabled(False)
        self.buttonStart.setMinimumSize(QSize(75, 30))
        self.buttonStart.setMaximumSize(QSize(500, 40))
        self.buttonStart.setFont(font1)

        self.horizontalLayout.addWidget(self.buttonStart)

        self.buttonStop = QPushButton(self.centralwidget)
        self.buttonStop.setObjectName("buttonStop")
        self.buttonStop.setEnabled(False)
        self.buttonStop.setMinimumSize(QSize(75, 30))
        self.buttonStop.setMaximumSize(QSize(500, 40))
        self.buttonStop.setFont(font1)

        self.horizontalLayout.addWidget(self.buttonStop)

        self.line_3 = QFrame(self.centralwidget)
        self.line_3.setObjectName("line_3")
        self.line_3.setFont(font1)
        self.line_3.setFrameShape(QFrame.Shape.VLine)
        self.line_3.setFrameShadow(QFrame.Shadow.Sunken)

        self.horizontalLayout.addWidget(self.line_3)

        self.buttonReset = QPushButton(self.centralwidget)
        self.buttonReset.setObjectName("buttonReset")
        self.buttonReset.setEnabled(False)
        self.buttonReset.setFont(font1)

        self.horizontalLayout.addWidget(self.buttonReset)

        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.gridLayout_5.addLayout(self.verticalLayout_2, 0, 0, 1, 1)

        self.line = QFrame(self.centralwidget)
        self.line.setObjectName("line")
        self.line.setFont(font1)
        self.line.setFrameShadow(QFrame.Shadow.Plain)
        self.line.setFrameShape(QFrame.Shape.VLine)

        self.gridLayout_5.addWidget(self.line, 0, 1, 1, 1)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(-1, -1, 0, -1)
        self.gridGroupBox = QGroupBox(self.centralwidget)
        self.gridGroupBox.setObjectName("gridGroupBox")
        sizePolicy13 = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        sizePolicy13.setHorizontalStretch(0)
        sizePolicy13.setVerticalStretch(0)
        sizePolicy13.setHeightForWidth(
            self.gridGroupBox.sizePolicy().hasHeightForWidth()
        )
        self.gridGroupBox.setSizePolicy(sizePolicy13)
        self.gridGroupBox.setFont(font1)
        self.gridGroupBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gridGroupBox.setFlat(False)
        self.gridLayout_2 = QGridLayout(self.gridGroupBox)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout_2.setHorizontalSpacing(-1)
        self.gridLayout_2.setContentsMargins(-1, 12, -1, -1)
        self.line_2 = QFrame(self.gridGroupBox)
        self.line_2.setObjectName("line_2")
        self.line_2.setFont(font1)
        self.line_2.setFrameShadow(QFrame.Shadow.Plain)
        self.line_2.setFrameShape(QFrame.Shape.HLine)

        self.gridLayout_2.addWidget(self.line_2, 3, 0, 1, 1)

        self.tabWidget = QTabWidget(self.gridGroupBox)
        self.tabWidget.setObjectName("tabWidget")
        sizePolicy14 = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        sizePolicy14.setHorizontalStretch(0)
        sizePolicy14.setVerticalStretch(10)
        sizePolicy14.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy14)
        self.tabWidget.setFont(font1)
        self.tabWidget.setAutoFillBackground(False)
        self.time = QWidget()
        self.time.setObjectName("time")
        self.gridLayout_6 = QGridLayout(self.time)
        self.gridLayout_6.setObjectName("gridLayout_6")
        self.gridLayout_6.setContentsMargins(10, 10, 10, 5)
        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(-1, 0, -1, -1)
        self.horizontalSpacer = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        self.horizontalLayout_8.addItem(self.horizontalSpacer)

        self.label_19 = QLabel(self.time)
        self.label_19.setObjectName("label_19")
        self.label_19.setFont(font1)

        self.horizontalLayout_8.addWidget(self.label_19)

        self.sPlotpoints = QSpinBox(self.time)
        self.sPlotpoints.setObjectName("sPlotpoints")
        self.sPlotpoints.setFont(font1)
        self.sPlotpoints.setMinimum(10)
        self.sPlotpoints.setMaximum(100000)
        self.sPlotpoints.setSingleStep(10)
        self.sPlotpoints.setStepType(QAbstractSpinBox.StepType.AdaptiveDecimalStepType)
        self.sPlotpoints.setValue(2000)

        self.horizontalLayout_8.addWidget(self.sPlotpoints)

        self.autoScroll = QCheckBox(self.time)
        self.autoScroll.setObjectName("autoScroll")
        self.autoScroll.setFont(font1)
        self.autoScroll.setChecked(True)

        self.horizontalLayout_8.addWidget(self.autoScroll)

        self.buttonAutoRange = QPushButton(self.time)
        self.buttonAutoRange.setObjectName("buttonAutoRange")
        self.buttonAutoRange.setFont(font1)

        self.horizontalLayout_8.addWidget(self.buttonAutoRange)

        self.gridLayout_6.addLayout(self.horizontalLayout_8, 0, 0, 1, 1)

        self.timePlot = QWidget(self.time)
        self.timePlot.setObjectName("timePlot")
        sizePolicy15 = QSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding
        )
        sizePolicy15.setHorizontalStretch(0)
        sizePolicy15.setVerticalStretch(0)
        sizePolicy15.setHeightForWidth(self.timePlot.sizePolicy().hasHeightForWidth())
        self.timePlot.setSizePolicy(sizePolicy15)
        self.timePlot.setFont(font1)

        self.gridLayout_6.addWidget(self.timePlot, 1, 0, 1, 1)

        self.tabWidget.addTab(self.time, "")
        self.histogramm = QWidget()
        self.histogramm.setObjectName("histogramm")
        sizePolicy16 = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        sizePolicy16.setHorizontalStretch(0)
        sizePolicy16.setVerticalStretch(0)
        sizePolicy16.setHeightForWidth(self.histogramm.sizePolicy().hasHeightForWidth())
        self.histogramm.setSizePolicy(sizePolicy16)
        self.gridLayout_4 = QGridLayout(self.histogramm)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.gridLayout_4.setContentsMargins(10, 10, 10, 5)
        self.histWidget = QWidget(self.histogramm)
        self.histWidget.setObjectName("histWidget")

        self.gridLayout_4.addWidget(self.histWidget, 1, 0, 1, 1)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.label_13 = QLabel(self.histogramm)
        self.label_13.setObjectName("label_13")

        self.horizontalLayout_6.addWidget(self.label_13)

        self.cStatPoints = QLineEdit(self.histogramm)
        self.cStatPoints.setObjectName("cStatPoints")
        self.cStatPoints.setEnabled(True)
        self.cStatPoints.setText("")
        self.cStatPoints.setReadOnly(True)

        self.horizontalLayout_6.addWidget(self.cStatPoints)

        self.label_14 = QLabel(self.histogramm)
        self.label_14.setObjectName("label_14")

        self.horizontalLayout_6.addWidget(self.label_14)

        self.cStatMin = QLineEdit(self.histogramm)
        self.cStatMin.setObjectName("cStatMin")
        self.cStatMin.setEnabled(True)
        self.cStatMin.setText("")
        self.cStatMin.setReadOnly(True)

        self.horizontalLayout_6.addWidget(self.cStatMin)

        self.label_15 = QLabel(self.histogramm)
        self.label_15.setObjectName("label_15")

        self.horizontalLayout_6.addWidget(self.label_15)

        self.cStatMax = QLineEdit(self.histogramm)
        self.cStatMax.setObjectName("cStatMax")
        self.cStatMax.setEnabled(True)
        self.cStatMax.setText("")
        self.cStatMax.setReadOnly(True)

        self.horizontalLayout_6.addWidget(self.cStatMax)

        self.label_16 = QLabel(self.histogramm)
        self.label_16.setObjectName("label_16")

        self.horizontalLayout_6.addWidget(self.label_16)

        self.cStatAvg = QLineEdit(self.histogramm)
        self.cStatAvg.setObjectName("cStatAvg")
        self.cStatAvg.setEnabled(True)
        self.cStatAvg.setText("")
        self.cStatAvg.setReadOnly(True)

        self.horizontalLayout_6.addWidget(self.cStatAvg)

        self.label_17 = QLabel(self.histogramm)
        self.label_17.setObjectName("label_17")

        self.horizontalLayout_6.addWidget(self.label_17)

        self.cStatSD = QLineEdit(self.histogramm)
        self.cStatSD.setObjectName("cStatSD")
        self.cStatSD.setEnabled(True)
        self.cStatSD.setText("")
        self.cStatSD.setReadOnly(True)

        self.horizontalLayout_6.addWidget(self.cStatSD)

        self.gridLayout_4.addLayout(self.horizontalLayout_6, 0, 0, 1, 1)

        self.gridLayout_4.setRowStretch(1, 1)
        self.tabWidget.addTab(self.histogramm, "")
        self.list = QWidget()
        self.list.setObjectName("list")
        sizePolicy16.setHeightForWidth(self.list.sizePolicy().hasHeightForWidth())
        self.list.setSizePolicy(sizePolicy16)
        self.gridLayout = QGridLayout(self.list)
        self.gridLayout.setObjectName("gridLayout")
        self.gridLayout.setContentsMargins(10, 10, 10, 5)
        self.tableView = QTableView(self.list)
        self.tableView.setObjectName("tableView")
        self.tableView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.gridLayout.addWidget(self.tableView, 0, 0, 1, 1)

        self.tabWidget.addTab(self.list, "")
        self.distance = QWidget()
        self.distance.setObjectName("distance")
        sizePolicy16.setHeightForWidth(self.distance.sizePolicy().hasHeightForWidth())
        self.distance.setSizePolicy(sizePolicy16)
        self.gridLayout_distance = QGridLayout(self.distance)
        self.gridLayout_distance.setObjectName("gridLayout_distance")
        self.gridLayout_distance.setContentsMargins(10, 10, 10, 5)
        self.horizontalLayout_distance = QHBoxLayout()
        self.horizontalLayout_distance.setObjectName("horizontalLayout_distance")
        self.label_distanceInput = QLabel(self.distance)
        self.label_distanceInput.setObjectName("label_distanceInput")
        self.label_distanceInput.setFont(font1)

        self.horizontalLayout_distance.addWidget(self.label_distanceInput)

        self.distanceInput = QDoubleSpinBox(self.distance)
        self.distanceInput.setObjectName("distanceInput")
        self.distanceInput.setFont(font1)
        self.distanceInput.setDecimals(1)
        self.distanceInput.setMaximum(99999.000000000000000)
        self.distanceInput.setSingleStep(0.500000000000000)

        self.horizontalLayout_distance.addWidget(self.distanceInput)

        self.horizontalSpacer_distance = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        self.horizontalLayout_distance.addItem(self.horizontalSpacer_distance)

        self.distanceStatus = QLabel(self.distance)
        self.distanceStatus.setObjectName("distanceStatus")
        self.distanceStatus.setFont(font1)
        self.distanceStatus.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignTrailing
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.horizontalLayout_distance.addWidget(self.distanceStatus)

        self.gridLayout_distance.addLayout(self.horizontalLayout_distance, 0, 0, 1, 1)

        self.distancePlot = QWidget(self.distance)
        self.distancePlot.setObjectName("distancePlot")
        sizePolicy15.setHeightForWidth(
            self.distancePlot.sizePolicy().hasHeightForWidth()
        )
        self.distancePlot.setSizePolicy(sizePolicy15)

        self.gridLayout_distance.addWidget(self.distancePlot, 1, 0, 1, 1)

        self.distanceTable = QTableView(self.distance)
        self.distanceTable.setObjectName("distanceTable")
        sizePolicy5.setHeightForWidth(
            self.distanceTable.sizePolicy().hasHeightForWidth()
        )
        self.distanceTable.setSizePolicy(sizePolicy5)
        self.distanceTable.setMaximumSize(QSize(16777215, 200))
        self.distanceTable.setFont(font1)
        self.distanceTable.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.distanceTable.setAlternatingRowColors(True)
        self.distanceTable.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.gridLayout_distance.addWidget(self.distanceTable, 2, 0, 1, 1)

        self.gridLayout_distance.setRowStretch(1, 1)
        self.tabWidget.addTab(self.distance, "")
        self.voltage = QWidget()
        self.voltage.setObjectName("voltage")
        sizePolicy16.setHeightForWidth(self.voltage.sizePolicy().hasHeightForWidth())
        self.voltage.setSizePolicy(sizePolicy16)
        self.gridLayout_voltage = QGridLayout(self.voltage)
        self.gridLayout_voltage.setObjectName("gridLayout_voltage")
        self.gridLayout_voltage.setContentsMargins(10, 10, 10, 5)
        self.horizontalLayout_voltage = QHBoxLayout()
        self.horizontalLayout_voltage.setObjectName("horizontalLayout_voltage")
        self.label_voltageHint = QLabel(self.voltage)
        self.label_voltageHint.setObjectName("label_voltageHint")
        self.label_voltageHint.setFont(font1)

        self.horizontalLayout_voltage.addWidget(self.label_voltageHint)

        self.horizontalSpacer_voltage = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        self.horizontalLayout_voltage.addItem(self.horizontalSpacer_voltage)

        self.voltageStatus = QLabel(self.voltage)
        self.voltageStatus.setObjectName("voltageStatus")
        self.voltageStatus.setFont(font1)
        self.voltageStatus.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignTrailing
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.horizontalLayout_voltage.addWidget(self.voltageStatus)

        self.gridLayout_voltage.addLayout(self.horizontalLayout_voltage, 0, 0, 1, 1)

        self.voltagePlot = QWidget(self.voltage)
        self.voltagePlot.setObjectName("voltagePlot")
        sizePolicy15.setHeightForWidth(
            self.voltagePlot.sizePolicy().hasHeightForWidth()
        )
        self.voltagePlot.setSizePolicy(sizePolicy15)

        self.gridLayout_voltage.addWidget(self.voltagePlot, 1, 0, 1, 1)

        self.voltageTable = QTableView(self.voltage)
        self.voltageTable.setObjectName("voltageTable")
        sizePolicy5.setHeightForWidth(
            self.voltageTable.sizePolicy().hasHeightForWidth()
        )
        self.voltageTable.setSizePolicy(sizePolicy5)
        self.voltageTable.setMaximumSize(QSize(16777215, 200))
        self.voltageTable.setFont(font1)
        self.voltageTable.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.voltageTable.setAlternatingRowColors(True)
        self.voltageTable.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.gridLayout_voltage.addWidget(self.voltageTable, 2, 0, 1, 1)

        self.gridLayout_voltage.setRowStretch(1, 1)
        self.tabWidget.addTab(self.voltage, "")
        self.interval = QWidget()
        self.interval.setObjectName("interval")
        sizePolicy16.setHeightForWidth(self.interval.sizePolicy().hasHeightForWidth())
        self.interval.setSizePolicy(sizePolicy16)
        self.gridLayout_interval = QGridLayout(self.interval)
        self.gridLayout_interval.setObjectName("gridLayout_interval")
        self.gridLayout_interval.setContentsMargins(10, 10, 10, 5)
        self.horizontalLayout_interval = QHBoxLayout()
        self.horizontalLayout_interval.setObjectName("horizontalLayout_interval")
        self.label_intervalWidth = QLabel(self.interval)
        self.label_intervalWidth.setObjectName("label_intervalWidth")
        self.label_intervalWidth.setFont(font1)

        self.horizontalLayout_interval.addWidget(self.label_intervalWidth)

        self.intervalWidthInput = QDoubleSpinBox(self.interval)
        self.intervalWidthInput.setObjectName("intervalWidthInput")
        self.intervalWidthInput.setFont(font1)
        self.intervalWidthInput.setMinimum(0.100000000000000)
        self.intervalWidthInput.setMaximum(3600.000000000000000)
        self.intervalWidthInput.setSingleStep(1.000000000000000)
        self.intervalWidthInput.setValue(1.000000000000000)

        self.horizontalLayout_interval.addWidget(self.intervalWidthInput)

        self.label_intervalRepeats = QLabel(self.interval)
        self.label_intervalRepeats.setObjectName("label_intervalRepeats")
        self.label_intervalRepeats.setFont(font1)

        self.horizontalLayout_interval.addWidget(self.label_intervalRepeats)

        self.intervalRepeatInput = QSpinBox(self.interval)
        self.intervalRepeatInput.setObjectName("intervalRepeatInput")
        self.intervalRepeatInput.setFont(font1)
        self.intervalRepeatInput.setMinimum(1)
        self.intervalRepeatInput.setMaximum(10000)
        self.intervalRepeatInput.setValue(10)

        self.horizontalLayout_interval.addWidget(self.intervalRepeatInput)

        self.horizontalSpacer_interval = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        self.horizontalLayout_interval.addItem(self.horizontalSpacer_interval)

        self.intervalStatus = QLabel(self.interval)
        self.intervalStatus.setObjectName("intervalStatus")
        self.intervalStatus.setFont(font1)
        self.intervalStatus.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignTrailing
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.horizontalLayout_interval.addWidget(self.intervalStatus)

        self.gridLayout_interval.addLayout(self.horizontalLayout_interval, 0, 0, 1, 1)

        self.intervalPlot = QWidget(self.interval)
        self.intervalPlot.setObjectName("intervalPlot")
        sizePolicy15.setHeightForWidth(
            self.intervalPlot.sizePolicy().hasHeightForWidth()
        )
        self.intervalPlot.setSizePolicy(sizePolicy15)

        self.gridLayout_interval.addWidget(self.intervalPlot, 1, 0, 1, 1)

        self.intervalTable = QTableView(self.interval)
        self.intervalTable.setObjectName("intervalTable")
        sizePolicy5.setHeightForWidth(
            self.intervalTable.sizePolicy().hasHeightForWidth()
        )
        self.intervalTable.setSizePolicy(sizePolicy5)
        self.intervalTable.setMaximumSize(QSize(16777215, 200))
        self.intervalTable.setFont(font1)
        self.intervalTable.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.intervalTable.setAlternatingRowColors(True)
        self.intervalTable.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.gridLayout_interval.addWidget(self.intervalTable, 2, 0, 1, 1)

        self.gridLayout_interval.setRowStretch(1, 1)
        self.tabWidget.addTab(self.interval, "")

        self.gridLayout_2.addWidget(self.tabWidget, 4, 0, 1, 1)

        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.label_4 = QLabel(self.gridGroupBox)
        self.label_4.setObjectName("label_4")
        sizePolicy17 = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum
        )
        sizePolicy17.setHorizontalStretch(0)
        sizePolicy17.setVerticalStretch(0)
        sizePolicy17.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy17)
        self.label_4.setMaximumSize(QSize(16777215, 100))
        self.label_4.setFont(font1)
        self.label_4.setAlignment(
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter
        )

        self.gridLayout_3.addWidget(self.label_4, 2, 3, 1, 1)

        self.formLayout_4 = QFormLayout()
        self.formLayout_4.setObjectName("formLayout_4")
        self.formLayout_4.setHorizontalSpacing(10)
        self.label_8 = QLabel(self.gridGroupBox)
        self.label_8.setObjectName("label_8")
        self.label_8.setMinimumSize(QSize(130, 0))
        self.label_8.setFont(font1)
        self.label_8.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignTrailing
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.formLayout_4.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_8)

        self.cVoltage = QLCDNumber(self.gridGroupBox)
        self.cVoltage.setObjectName("cVoltage")
        sizePolicy8.setHeightForWidth(self.cVoltage.sizePolicy().hasHeightForWidth())
        self.cVoltage.setSizePolicy(sizePolicy8)
        self.cVoltage.setMinimumSize(QSize(0, 25))
        self.cVoltage.setMaximumSize(QSize(120, 50))
        self.cVoltage.setFont(font1)
        self.cVoltage.setDigitCount(3)

        self.formLayout_4.setWidget(0, QFormLayout.ItemRole.FieldRole, self.cVoltage)

        self.label_9 = QLabel(self.gridGroupBox)
        self.label_9.setObjectName("label_9")
        self.label_9.setMinimumSize(QSize(130, 0))
        self.label_9.setFont(font1)
        self.label_9.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignTrailing
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.formLayout_4.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_9)

        self.cDuration = QLCDNumber(self.gridGroupBox)
        self.cDuration.setObjectName("cDuration")
        sizePolicy8.setHeightForWidth(self.cDuration.sizePolicy().hasHeightForWidth())
        self.cDuration.setSizePolicy(sizePolicy8)
        self.cDuration.setMinimumSize(QSize(100, 25))
        self.cDuration.setMaximumSize(QSize(120, 50))
        self.cDuration.setFont(font1)
        self.cDuration.setDigitCount(3)

        self.formLayout_4.setWidget(1, QFormLayout.ItemRole.FieldRole, self.cDuration)

        self.query_label = QLabel(self.gridGroupBox)
        self.query_label.setObjectName("query_label")
        sizePolicy17.setHeightForWidth(
            self.query_label.sizePolicy().hasHeightForWidth()
        )
        self.query_label.setSizePolicy(sizePolicy17)
        self.query_label.setMinimumSize(QSize(130, 0))
        self.query_label.setFont(font1)
        self.query_label.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignTrailing
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.formLayout_4.setWidget(2, QFormLayout.ItemRole.LabelRole, self.query_label)

        self.cQueryMode = QLabel(self.gridGroupBox)
        self.cQueryMode.setObjectName("cQueryMode")
        sizePolicy12.setHeightForWidth(self.cQueryMode.sizePolicy().hasHeightForWidth())
        self.cQueryMode.setSizePolicy(sizePolicy12)
        self.cQueryMode.setMinimumSize(QSize(0, 15))
        self.cQueryMode.setMaximumSize(QSize(120, 50))
        self.cQueryMode.setFont(font1)

        self.formLayout_4.setWidget(2, QFormLayout.ItemRole.FieldRole, self.cQueryMode)

        self.label_12 = QLabel(self.gridGroupBox)
        self.label_12.setObjectName("label_12")
        sizePolicy17.setHeightForWidth(self.label_12.sizePolicy().hasHeightForWidth())
        self.label_12.setSizePolicy(sizePolicy17)
        self.label_12.setMinimumSize(QSize(130, 20))
        self.label_12.setFont(font1)
        self.label_12.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignTrailing
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.formLayout_4.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_12)

        self.cMode = QLabel(self.gridGroupBox)
        self.cMode.setObjectName("cMode")
        sizePolicy12.setHeightForWidth(self.cMode.sizePolicy().hasHeightForWidth())
        self.cMode.setSizePolicy(sizePolicy12)
        self.cMode.setMinimumSize(QSize(0, 15))
        self.cMode.setMaximumSize(QSize(120, 50))
        self.cMode.setFont(font1)

        self.formLayout_4.setWidget(3, QFormLayout.ItemRole.FieldRole, self.cMode)

        self.gridLayout_3.addLayout(self.formLayout_4, 1, 0, 3, 1)

        self.lastCount = QLCDNumber(self.gridGroupBox)
        self.lastCount.setObjectName("lastCount")
        sizePolicy12.setHeightForWidth(self.lastCount.sizePolicy().hasHeightForWidth())
        self.lastCount.setSizePolicy(sizePolicy12)
        self.lastCount.setMinimumSize(QSize(200, 50))
        self.lastCount.setMaximumSize(QSize(1000, 70))
        self.lastCount.setFont(font1)
        self.lastCount.setFrameShape(QFrame.Shape.Box)
        self.lastCount.setFrameShadow(QFrame.Shadow.Raised)

        self.gridLayout_3.addWidget(self.lastCount, 3, 3, 1, 1)

        self.label_18 = QLabel(self.gridGroupBox)
        self.label_18.setObjectName("label_18")
        sizePolicy9.setHeightForWidth(self.label_18.sizePolicy().hasHeightForWidth())
        self.label_18.setSizePolicy(sizePolicy9)
        self.label_18.setFont(font1)
        self.label_18.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_3.addWidget(self.label_18, 0, 0, 1, 1)

        self.line_4 = QFrame(self.gridGroupBox)
        self.line_4.setObjectName("line_4")
        self.line_4.setFont(font1)
        self.line_4.setFrameShape(QFrame.Shape.VLine)
        self.line_4.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout_3.addWidget(self.line_4, 0, 1, 4, 1)

        self.currentCount = QLCDNumber(self.gridGroupBox)
        self.currentCount.setObjectName("currentCount")
        sizePolicy12.setHeightForWidth(
            self.currentCount.sizePolicy().hasHeightForWidth()
        )
        self.currentCount.setSizePolicy(sizePolicy12)
        self.currentCount.setMinimumSize(QSize(200, 50))
        self.currentCount.setMaximumSize(QSize(1000, 70))
        self.currentCount.setFont(font1)
        self.currentCount.setFrameShape(QFrame.Shape.Box)
        self.currentCount.setFrameShadow(QFrame.Shadow.Raised)

        self.gridLayout_3.addWidget(self.currentCount, 3, 4, 1, 1)

        self.label_3 = QLabel(self.gridGroupBox)
        self.label_3.setObjectName("label_3")
        sizePolicy17.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy17)
        self.label_3.setMaximumSize(QSize(16777215, 100))
        self.label_3.setFont(font1)
        self.label_3.setAlignment(
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter
        )

        self.gridLayout_3.addWidget(self.label_3, 2, 4, 1, 1)

        self.label_21 = QLabel(self.gridGroupBox)
        self.label_21.setObjectName("label_21")
        sizePolicy17.setHeightForWidth(self.label_21.sizePolicy().hasHeightForWidth())
        self.label_21.setSizePolicy(sizePolicy17)
        self.label_21.setMaximumSize(QSize(16777215, 100))
        self.label_21.setFont(font1)
        self.label_21.setAlignment(
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter
        )

        self.gridLayout_3.addWidget(self.label_21, 2, 2, 1, 1)

        self.currentRate = QLCDNumber(self.gridGroupBox)
        self.currentRate.setObjectName("currentRate")
        sizePolicy12.setHeightForWidth(
            self.currentRate.sizePolicy().hasHeightForWidth()
        )
        self.currentRate.setSizePolicy(sizePolicy12)
        self.currentRate.setMinimumSize(QSize(200, 50))
        self.currentRate.setMaximumSize(QSize(1000, 70))
        self.currentRate.setFont(font1)
        self.currentRate.setFrameShape(QFrame.Shape.Box)
        self.currentRate.setFrameShadow(QFrame.Shadow.Raised)
        self.currentRate.setDigitCount(6)

        self.gridLayout_3.addWidget(self.currentRate, 3, 2, 1, 1)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(-1, -1, -1, 0)
        self.progressBar = QProgressBar(self.gridGroupBox)
        self.progressBar.setObjectName("progressBar")
        sizePolicy18 = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        sizePolicy18.setHorizontalStretch(0)
        sizePolicy18.setVerticalStretch(0)
        sizePolicy18.setHeightForWidth(
            self.progressBar.sizePolicy().hasHeightForWidth()
        )
        self.progressBar.setSizePolicy(sizePolicy18)
        self.progressBar.setFont(font1)
        self.progressBar.setValue(0)

        self.horizontalLayout_4.addWidget(self.progressBar)

        self.progressTimer = QLabel(self.gridGroupBox)
        self.progressTimer.setObjectName("progressTimer")
        sizePolicy17.setHeightForWidth(
            self.progressTimer.sizePolicy().hasHeightForWidth()
        )
        self.progressTimer.setSizePolicy(sizePolicy17)
        self.progressTimer.setMinimumSize(QSize(50, 0))
        self.progressTimer.setFont(font1)

        self.horizontalLayout_4.addWidget(self.progressTimer)

        self.gridLayout_3.addLayout(self.horizontalLayout_4, 1, 2, 1, 3)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(-1, 0, -1, -1)
        self.label = QLabel(self.gridGroupBox)
        self.label.setObjectName("label")
        sizePolicy12.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy12)
        self.label.setMinimumSize(QSize(80, 20))
        self.label.setFont(font1)
        self.label.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignTrailing
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.horizontalLayout_3.addWidget(self.label)

        self.cVersion = QLabel(self.gridGroupBox)
        self.cVersion.setObjectName("cVersion")
        sizePolicy12.setHeightForWidth(self.cVersion.sizePolicy().hasHeightForWidth())
        self.cVersion.setSizePolicy(sizePolicy12)
        self.cVersion.setMinimumSize(QSize(0, 15))
        self.cVersion.setMaximumSize(QSize(120, 50))
        self.cVersion.setFont(font1)

        self.horizontalLayout_3.addWidget(self.cVersion)

        self.label_11 = QLabel(self.gridGroupBox)
        self.label_11.setObjectName("label_11")
        sizePolicy9.setHeightForWidth(self.label_11.sizePolicy().hasHeightForWidth())
        self.label_11.setSizePolicy(sizePolicy9)
        self.label_11.setMinimumSize(QSize(80, 0))
        self.label_11.setFont(font1)
        self.label_11.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignTrailing
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.horizontalLayout_3.addWidget(self.label_11)

        self.cOpenbis = QLabel(self.gridGroupBox)
        self.cOpenbis.setObjectName("cOpenbis")
        sizePolicy9.setHeightForWidth(self.cOpenbis.sizePolicy().hasHeightForWidth())
        self.cOpenbis.setSizePolicy(sizePolicy9)
        self.cOpenbis.setMinimumSize(QSize(0, 15))
        self.cOpenbis.setMaximumSize(QSize(120, 50))
        self.cOpenbis.setFont(font1)

        self.horizontalLayout_3.addWidget(self.cOpenbis)

        self.horizontalSpacer_2 = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        self.horizontalLayout_3.addItem(self.horizontalSpacer_2)

        self.label_2 = QLabel(self.gridGroupBox)
        self.label_2.setObjectName("label_2")
        sizePolicy17.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy17)
        self.label_2.setFont(font1)
        self.label_2.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignTrailing
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.horizontalLayout_3.addWidget(self.label_2)

        self.statusLED = QLabel(self.gridGroupBox)
        self.statusLED.setObjectName("statusLED")
        sizePolicy19 = QSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum
        )
        sizePolicy19.setHorizontalStretch(0)
        sizePolicy19.setVerticalStretch(0)
        sizePolicy19.setHeightForWidth(self.statusLED.sizePolicy().hasHeightForWidth())
        self.statusLED.setSizePolicy(sizePolicy19)
        self.statusLED.setMinimumSize(QSize(20, 20))
        self.statusLED.setMaximumSize(QSize(20, 20))
        self.statusLED.setFont(font1)
        self.statusLED.setStyleSheet(
            "background-color: rgb(255, 11, 3); border: 0px; padding: 4px; border-radius: 10px"
        )
        self.statusLED.setFrameShape(QFrame.Shape.Box)
        self.statusLED.setText("")

        self.horizontalLayout_3.addWidget(self.statusLED)

        self.statusText = QLabel(self.gridGroupBox)
        self.statusText.setObjectName("statusText")
        sizePolicy17.setHeightForWidth(self.statusText.sizePolicy().hasHeightForWidth())
        self.statusText.setSizePolicy(sizePolicy17)
        self.statusText.setMinimumSize(QSize(100, 0))
        self.statusText.setFont(font1)

        self.horizontalLayout_3.addWidget(self.statusText)

        self.horizontalLayout_2.addLayout(self.horizontalLayout_3)

        self.gridLayout_3.addLayout(self.horizontalLayout_2, 0, 2, 1, 3)

        self.gridLayout_3.setColumnStretch(2, 1)
        self.gridLayout_3.setColumnStretch(3, 1)
        self.gridLayout_3.setColumnStretch(4, 1)

        self.gridLayout_2.addLayout(self.gridLayout_3, 0, 0, 1, 1)

        self.gridLayout_2.setRowStretch(0, 1)

        self.verticalLayout_3.addWidget(self.gridGroupBox)

        self.gridLayout_5.addLayout(self.verticalLayout_3, 0, 2, 1, 1)

        self.gridLayout_5.setColumnStretch(2, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 1280, 39))
        MainWindow.setMenuBar(self.menubar)
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setObjectName("statusBar")
        MainWindow.setStatusBar(self.statusBar)

        self.retranslateUi(MainWindow)
        self.voltDial.valueChanged.connect(self.sVoltage.setValue)
        self.sVoltage.valueChanged.connect(self.voltDial.setValue)
        self.autoScroll.toggled.connect(self.sPlotpoints.setVisible)
        self.autoScroll.toggled.connect(self.label_19.setVisible)
        self.autoSave.toggled.connect(self.label_5.setVisible)
        self.autoSave.toggled.connect(self.suffix.setVisible)

        self.buttonSetting.setDefault(False)
        self.radSample.setCurrentIndex(-1)
        self.groupLetter.setCurrentIndex(-1)
        self.detectorCode.setCurrentIndex(-1)
        self.tabWidget.setCurrentIndex(3)

        QMetaObject.connectSlotsByName(MainWindow)

    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(
            QCoreApplication.translate("MainWindow", "GM-Counter", None)
        )
        self.settings.setTitle(
            QCoreApplication.translate("MainWindow", "Einstellungen", None)
        )
        self.mode_label.setText(
            QCoreApplication.translate("MainWindow", "Z\u00e4hl-Modus", None)
        )
        # if QT_CONFIG(tooltip)
        self.sModeSingle.setToolTip(
            QCoreApplication.translate(
                "MainWindow",
                "<html><head/><body><p>Stoppt die Messung nach Ablauf Z\u00e4hldauer</p></body></html>",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.sModeSingle.setText(
            QCoreApplication.translate("MainWindow", "Einzel", None)
        )
        # if QT_CONFIG(tooltip)
        self.sModeMulti.setToolTip(
            QCoreApplication.translate(
                "MainWindow",
                "<html><head/><body><p>Wiederholt die Messung automatisch nach Ablauf Z\u00e4hldauer</p></body></html>",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.sModeMulti.setText(
            QCoreApplication.translate("MainWindow", "Wiederholung", None)
        )
        self.label_10.setText(
            QCoreApplication.translate("MainWindow", "Abfragemodus", None)
        )
        self.sQModeMan.setText(
            QCoreApplication.translate("MainWindow", "Manuell", None)
        )
        self.sQModeAuto.setText(
            QCoreApplication.translate("MainWindow", "Automatik", None)
        )
        self.duration_label.setText(
            QCoreApplication.translate("MainWindow", "Z\u00e4hldauer", None)
        )
        self.sDuration.setItemText(
            0, QCoreApplication.translate("MainWindow", "unendlich", "f0")
        )
        self.sDuration.setItemText(
            1, QCoreApplication.translate("MainWindow", "1 Sekunde", "f1")
        )
        self.sDuration.setItemText(
            2, QCoreApplication.translate("MainWindow", "10 Sekunden", "f2")
        )
        self.sDuration.setItemText(
            3, QCoreApplication.translate("MainWindow", "60 Sekunden", "f3")
        )
        self.sDuration.setItemText(
            4, QCoreApplication.translate("MainWindow", "100 Sekunden", "f4")
        )
        self.sDuration.setItemText(
            5, QCoreApplication.translate("MainWindow", "300 Sekunden", "f5")
        )

        # if QT_CONFIG(tooltip)
        self.sDuration.setToolTip(
            QCoreApplication.translate(
                "MainWindow", "Wie lange der Z\u00e4hler misst", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        # if QT_CONFIG(tooltip)
        self.volt_label.setToolTip(
            QCoreApplication.translate(
                "MainWindow", "Spannung des Geiger-M\u00fcller Z\u00e4hlrohrs", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.volt_label.setText(
            QCoreApplication.translate("MainWindow", "GM-Spannung", None)
        )
        self.sVoltage.setSuffix(QCoreApplication.translate("MainWindow", " V", None))
        self.buttonSetting.setText(
            QCoreApplication.translate("MainWindow", "Einstellungen \u00e4ndern", None)
        )
        self.groupBox.setTitle(
            QCoreApplication.translate("MainWindow", "Speicherung", None)
        )
        self.label_6.setText(
            QCoreApplication.translate("MainWindow", "Radioaktive Probe*", None)
        )
        # if QT_CONFIG(tooltip)
        self.radSample.setToolTip(
            QCoreApplication.translate(
                "MainWindow",
                '<html><head/><body><p>Auswahl der verwendeten radioaktiven Probe <span style=" color:#ff001a;">(Pflichtfeld)</span></p></body></html>',
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.radSample.setCurrentText("")
        self.label_7.setText(QCoreApplication.translate("MainWindow", "Gruppe*", None))
        self.groupLetter.setItemText(
            0, QCoreApplication.translate("MainWindow", "A", None)
        )
        self.groupLetter.setItemText(
            1, QCoreApplication.translate("MainWindow", "B", None)
        )
        self.groupLetter.setItemText(
            2, QCoreApplication.translate("MainWindow", "C", None)
        )
        self.groupLetter.setItemText(
            3, QCoreApplication.translate("MainWindow", "D", None)
        )
        self.groupLetter.setItemText(
            4, QCoreApplication.translate("MainWindow", "E", None)
        )
        self.groupLetter.setItemText(
            5, QCoreApplication.translate("MainWindow", "F", None)
        )
        self.groupLetter.setItemText(
            6, QCoreApplication.translate("MainWindow", "G", None)
        )
        self.groupLetter.setItemText(
            7, QCoreApplication.translate("MainWindow", "H", None)
        )
        self.groupLetter.setItemText(
            8, QCoreApplication.translate("MainWindow", "I", None)
        )
        self.groupLetter.setItemText(
            9, QCoreApplication.translate("MainWindow", "J", None)
        )
        self.groupLetter.setItemText(
            10, QCoreApplication.translate("MainWindow", "K", None)
        )
        self.groupLetter.setItemText(
            11, QCoreApplication.translate("MainWindow", "L", None)
        )
        self.groupLetter.setItemText(
            12, QCoreApplication.translate("MainWindow", "M", None)
        )
        self.groupLetter.setItemText(
            13, QCoreApplication.translate("MainWindow", "N", None)
        )
        self.groupLetter.setItemText(
            14, QCoreApplication.translate("MainWindow", "O", None)
        )
        self.groupLetter.setItemText(
            15, QCoreApplication.translate("MainWindow", "P", None)
        )
        self.groupLetter.setItemText(
            16, QCoreApplication.translate("MainWindow", "Q", None)
        )
        self.groupLetter.setItemText(
            17, QCoreApplication.translate("MainWindow", "R", None)
        )
        self.groupLetter.setItemText(
            18, QCoreApplication.translate("MainWindow", "S", None)
        )
        self.groupLetter.setItemText(
            19, QCoreApplication.translate("MainWindow", "T", None)
        )
        self.groupLetter.setItemText(
            20, QCoreApplication.translate("MainWindow", "U", None)
        )
        self.groupLetter.setItemText(
            21, QCoreApplication.translate("MainWindow", "V", None)
        )
        self.groupLetter.setItemText(
            22, QCoreApplication.translate("MainWindow", "W", None)
        )
        self.groupLetter.setItemText(
            23, QCoreApplication.translate("MainWindow", "Z", None)
        )

        # if QT_CONFIG(tooltip)
        self.groupLetter.setToolTip(
            QCoreApplication.translate(
                "MainWindow",
                '<html><head/><body><p>Auswahl der GP Praktikumsgruppe <span style=" color:#ff001a;">(Pflichtfeld)</span></p></body></html>',
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.label_5.setText(
            QCoreApplication.translate("MainWindow", "Eigenes Suffix", None)
        )
        # if QT_CONFIG(tooltip)
        self.suffix.setToolTip(
            QCoreApplication.translate(
                "MainWindow",
                "Ein benutzerdefiniertes Suffix mit maximal 20 Zeichen",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.label_20.setText(
            QCoreApplication.translate("MainWindow", "Detektor*", None)
        )
        # if QT_CONFIG(tooltip)
        self.detectorCode.setToolTip(
            QCoreApplication.translate(
                "MainWindow",
                '<html><head/><body><p>Auswahl des verwendeten Detektors (Geiger-M\u00fcller-Z\u00e4hlrohr) <span style=" color:#ff001a;">(Pflichtfeld)</span></p></body></html>',
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.detectorCode.setCurrentText("")
        self.lblDistance.setText(
            QCoreApplication.translate("MainWindow", "Probenabstand", None)
        )
        # if QT_CONFIG(tooltip)
        self.distanceGlobalDistance.setToolTip(
            QCoreApplication.translate(
                "MainWindow",
                "Abstand zwischen Detektoroberfl\u00e4che und radioaktiver Probe in cm",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.distanceGlobalDistance.setSuffix(
            QCoreApplication.translate("MainWindow", " cm", None)
        )
        # if QT_CONFIG(tooltip)
        self.buttonSave.setToolTip(
            QCoreApplication.translate(
                "MainWindow", "Messung speichern (Dateidialog)", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.buttonSave.setText(
            QCoreApplication.translate("MainWindow", "Speichern", None)
        )
        # if QT_CONFIG(tooltip)
        self.autoSave.setToolTip(
            QCoreApplication.translate(
                "MainWindow",
                '<html><head/><body><p>Bei Aktivierung werden die Messungen automatisch im Format:</p><p>YYYY_MM_DD-<span style=" font-style:italic;">Radioaktive Probe</span>-<span style=" font-style:italic;">Suffix</span>.csv</p><p>im Ordner Dokumente/Geiger-Mueller/ gespeichert.</p></body></html>',
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.autoSave.setText(
            QCoreApplication.translate("MainWindow", "Automatische Speicherung. ", None)
        )
        # if QT_CONFIG(tooltip)
        self.buttonStart.setToolTip(
            QCoreApplication.translate("MainWindow", "Start der Messung", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.buttonStart.setText(
            QCoreApplication.translate("MainWindow", "Start", None)
        )
        # if QT_CONFIG(tooltip)
        self.buttonStop.setToolTip(
            QCoreApplication.translate("MainWindow", "Aktuelle Messung stoppen", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.buttonStop.setText(QCoreApplication.translate("MainWindow", "Stop", None))
        self.buttonReset.setText(
            QCoreApplication.translate("MainWindow", "Reset", None)
        )
        self.gridGroupBox.setTitle(
            QCoreApplication.translate("MainWindow", "Live-Metriken", None)
        )
        self.label_19.setText(
            QCoreApplication.translate("MainWindow", "Max. Plot Punkte", None)
        )
        self.autoScroll.setText(
            QCoreApplication.translate("MainWindow", "Auto Scroll", None)
        )
        self.buttonAutoRange.setText(
            QCoreApplication.translate("MainWindow", "x/y Limits anpassen", None)
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.time),
            QCoreApplication.translate("MainWindow", "Zeitverlauf", None),
        )
        self.label_13.setText(QCoreApplication.translate("MainWindow", "Anzahl:", None))
        self.label_14.setText(
            QCoreApplication.translate("MainWindow", "Min / \u00b5s:", None)
        )
        self.label_15.setText(
            QCoreApplication.translate("MainWindow", "Max / \u00b5s:", None)
        )
        self.label_16.setText(
            QCoreApplication.translate("MainWindow", "Mittelwert / \u00b5s:", None)
        )
        self.label_17.setText(
            QCoreApplication.translate("MainWindow", "Standardabw. / \u00b5s:", None)
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.histogramm),
            QCoreApplication.translate("MainWindow", "Histogramm", None),
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.list),
            QCoreApplication.translate("MainWindow", "Liste", None),
        )
        self.label_distanceInput.setText(
            QCoreApplication.translate("MainWindow", "Probenabstand (cm):", None)
        )
        # if QT_CONFIG(tooltip)
        self.distanceInput.setToolTip(
            QCoreApplication.translate(
                "MainWindow", "Abstand der Probe vom Detektor in Zentimetern", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.distanceInput.setSuffix(
            QCoreApplication.translate("MainWindow", " cm", None)
        )
        self.distanceStatus.setText(
            QCoreApplication.translate(
                "MainWindow", "Keine Messpunkte aufgezeichnet.", None
            )
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.distance),
            QCoreApplication.translate("MainWindow", "Abstandsgesetz", None),
        )
        self.label_voltageHint.setText(
            QCoreApplication.translate(
                "MainWindow",
                "Spannung wird in der Ger\u00e4testeuerung eingestellt.",
                None,
            )
        )
        self.voltageStatus.setText(
            QCoreApplication.translate(
                "MainWindow", "Keine Messpunkte aufgezeichnet.", None
            )
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.voltage),
            QCoreApplication.translate("MainWindow", "Spannungskurve", None),
        )
        self.label_intervalWidth.setText(
            QCoreApplication.translate("MainWindow", "Intervallbreite (s):", None)
        )
        self.label_intervalRepeats.setText(
            QCoreApplication.translate("MainWindow", "Wiederholungen:", None)
        )
        self.intervalStatus.setText(
            QCoreApplication.translate("MainWindow", "Keine Daten.", None)
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.interval),
            QCoreApplication.translate("MainWindow", "Intervalle", None),
        )
        self.label_4.setText(
            QCoreApplication.translate("MainWindow", "Voriges Z\u00e4hlergebnis", None)
        )
        self.label_8.setText(
            QCoreApplication.translate("MainWindow", "GM-Spannung / V", None)
        )
        # if QT_CONFIG(tooltip)
        self.cVoltage.setToolTip(
            QCoreApplication.translate("MainWindow", "Aktuelle GM-Spannung", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.label_9.setText(
            QCoreApplication.translate("MainWindow", "Z\u00e4hldauer / s", None)
        )
        # if QT_CONFIG(tooltip)
        self.cDuration.setToolTip(
            QCoreApplication.translate(
                "MainWindow",
                "Aktuelle eingestellte Z\u00e4hldauer. 999 f\u00fcr unendllich",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.query_label.setText(
            QCoreApplication.translate("MainWindow", "Abfragemodus", None)
        )
        # if QT_CONFIG(tooltip)
        self.cQueryMode.setToolTip(
            QCoreApplication.translate(
                "MainWindow",
                "Aktuell eingestellter Abfragemodus der Z\u00e4hlergebnisse",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.cQueryMode.setText(
            QCoreApplication.translate("MainWindow", "unknown", None)
        )
        self.label_12.setText(
            QCoreApplication.translate("MainWindow", "Z\u00e4hl-Modus", None)
        )
        # if QT_CONFIG(tooltip)
        self.cMode.setToolTip(
            QCoreApplication.translate(
                "MainWindow", "Aktuell eingestellter Z\u00e4hlmodus", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.cMode.setText(QCoreApplication.translate("MainWindow", "unknown", None))
        self.label_18.setText(
            QCoreApplication.translate("MainWindow", "Aktuelle GM-Parameter", None)
        )
        self.label_3.setText(
            QCoreApplication.translate(
                "MainWindow", "Aktuelles Z\u00e4hlergebnis", None
            )
        )
        self.label_21.setText(
            QCoreApplication.translate(
                "MainWindow", "Aktuelle Z\u00e4hlrate / Hz", None
            )
        )
        self.progressTimer.setText(
            QCoreApplication.translate("MainWindow", "99999 s", None)
        )
        self.label.setText(
            QCoreApplication.translate("MainWindow", "Firmware-Version", None)
        )
        # if QT_CONFIG(tooltip)
        self.cVersion.setToolTip(
            QCoreApplication.translate("MainWindow", "GM-Z\u00e4hler Firmware", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.cVersion.setText(QCoreApplication.translate("MainWindow", "unknown", None))
        self.label_11.setText(
            QCoreApplication.translate("MainWindow", "OpenBIS Code", None)
        )
        self.cOpenbis.setText(QCoreApplication.translate("MainWindow", "unknown", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", "Status:", None))
        self.statusText.setText(
            QCoreApplication.translate("MainWindow", "unknown", None)
        )

    # retranslateUi
