# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainwindow.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QAbstractSpinBox, QApplication, QButtonGroup,
    QCheckBox, QComboBox, QDial, QFormLayout,
    QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLCDNumber, QLabel, QLayout,
    QLineEdit, QMainWindow, QMenuBar, QProgressBar,
    QPushButton, QRadioButton, QSizePolicy, QSpacerItem,
    QSpinBox, QStatusBar, QTabWidget, QTableView,
    QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1174, 942)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout_3 = QHBoxLayout(self.centralwidget)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(10, -1, -1, 10)
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.verticalLayout_2.setContentsMargins(0, -1, -1, 0)
        self.settings = QGroupBox(self.centralwidget)
        self.settings.setObjectName(u"settings")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.settings.sizePolicy().hasHeightForWidth())
        self.settings.setSizePolicy(sizePolicy)
        self.settings.setMaximumSize(QSize(1000, 16777215))
        font = QFont()
        font.setPointSize(13)
        self.settings.setFont(font)
        self.settings.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.formLayout = QFormLayout(self.settings)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.formLayout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.formLayout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.formLayout.setFormAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.formLayout.setContentsMargins(-1, 12, -1, -1)
        self.mode_label = QLabel(self.settings)
        self.mode_label.setObjectName(u"mode_label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.mode_label.sizePolicy().hasHeightForWidth())
        self.mode_label.setSizePolicy(sizePolicy1)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.mode_label)

        self.sMode = QHBoxLayout()
        self.sMode.setObjectName(u"sMode")
        self.sMode.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.sMode.setContentsMargins(-1, -1, 0, -1)
        self.sModeSingle = QRadioButton(self.settings)
        self.groupMode = QButtonGroup(MainWindow)
        self.groupMode.setObjectName(u"groupMode")
        self.groupMode.addButton(self.sModeSingle)
        self.sModeSingle.setObjectName(u"sModeSingle")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.sModeSingle.sizePolicy().hasHeightForWidth())
        self.sModeSingle.setSizePolicy(sizePolicy2)
        self.sModeSingle.setChecked(True)

        self.sMode.addWidget(self.sModeSingle)

        self.sModeMulti = QRadioButton(self.settings)
        self.groupMode.addButton(self.sModeMulti)
        self.sModeMulti.setObjectName(u"sModeMulti")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.sModeMulti.sizePolicy().hasHeightForWidth())
        self.sModeMulti.setSizePolicy(sizePolicy3)

        self.sMode.addWidget(self.sModeMulti)


        self.formLayout.setLayout(0, QFormLayout.ItemRole.FieldRole, self.sMode)

        self.label_10 = QLabel(self.settings)
        self.label_10.setObjectName(u"label_10")
        sizePolicy1.setHeightForWidth(self.label_10.sizePolicy().hasHeightForWidth())
        self.label_10.setSizePolicy(sizePolicy1)
        self.label_10.setMinimumSize(QSize(0, 20))
        self.label_10.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_10)

        self.sQueryMode = QHBoxLayout()
        self.sQueryMode.setObjectName(u"sQueryMode")
        self.sQueryMode.setSizeConstraint(QLayout.SizeConstraint.SetMaximumSize)
        self.sQModeMan = QRadioButton(self.settings)
        self.groupQMode = QButtonGroup(MainWindow)
        self.groupQMode.setObjectName(u"groupQMode")
        self.groupQMode.addButton(self.sQModeMan)
        self.sQModeMan.setObjectName(u"sQModeMan")
        self.sQModeMan.setEnabled(False)
        sizePolicy2.setHeightForWidth(self.sQModeMan.sizePolicy().hasHeightForWidth())
        self.sQModeMan.setSizePolicy(sizePolicy2)
        self.sQModeMan.setChecked(False)

        self.sQueryMode.addWidget(self.sQModeMan)

        self.sQModeAuto = QRadioButton(self.settings)
        self.groupQMode.addButton(self.sQModeAuto)
        self.sQModeAuto.setObjectName(u"sQModeAuto")
        self.sQModeAuto.setEnabled(False)
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.sQModeAuto.sizePolicy().hasHeightForWidth())
        self.sQModeAuto.setSizePolicy(sizePolicy4)
        self.sQModeAuto.setChecked(True)

        self.sQueryMode.addWidget(self.sQModeAuto)


        self.formLayout.setLayout(1, QFormLayout.ItemRole.FieldRole, self.sQueryMode)

        self.duration_label = QLabel(self.settings)
        self.duration_label.setObjectName(u"duration_label")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.duration_label.sizePolicy().hasHeightForWidth())
        self.duration_label.setSizePolicy(sizePolicy5)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.duration_label)

        self.sDuration = QComboBox(self.settings)
        self.sDuration.addItem("")
        self.sDuration.addItem("")
        self.sDuration.addItem("")
        self.sDuration.addItem("")
        self.sDuration.addItem("")
        self.sDuration.addItem("")
        self.sDuration.setObjectName(u"sDuration")
        sizePolicy6 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.sDuration.sizePolicy().hasHeightForWidth())
        self.sDuration.setSizePolicy(sizePolicy6)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.sDuration)

        self.volt_label = QLabel(self.settings)
        self.volt_label.setObjectName(u"volt_label")
        sizePolicy7 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy7.setHorizontalStretch(0)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(self.volt_label.sizePolicy().hasHeightForWidth())
        self.volt_label.setSizePolicy(sizePolicy7)
        self.volt_label.setMinimumSize(QSize(0, 100))
        self.volt_label.setMaximumSize(QSize(16777215, 100))

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.volt_label)

        self.sVolt = QHBoxLayout()
        self.sVolt.setObjectName(u"sVolt")
        self.sVolt.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.sVolt.setContentsMargins(-1, -1, 0, -1)
        self.sVoltage = QSpinBox(self.settings)
        self.sVoltage.setObjectName(u"sVoltage")
        sizePolicy8 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy8.setHorizontalStretch(0)
        sizePolicy8.setVerticalStretch(0)
        sizePolicy8.setHeightForWidth(self.sVoltage.sizePolicy().hasHeightForWidth())
        self.sVoltage.setSizePolicy(sizePolicy8)
        self.sVoltage.setMinimumSize(QSize(0, 40))
        self.sVoltage.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.sVoltage.setMinimum(300)
        self.sVoltage.setMaximum(700)
        self.sVoltage.setSingleStep(10)
        self.sVoltage.setValue(500)

        self.sVolt.addWidget(self.sVoltage)

        self.voltDial = QDial(self.settings)
        self.voltDial.setObjectName(u"voltDial")
        sizePolicy4.setHeightForWidth(self.voltDial.sizePolicy().hasHeightForWidth())
        self.voltDial.setSizePolicy(sizePolicy4)
        self.voltDial.setMinimumSize(QSize(100, 100))
        self.voltDial.setMaximumSize(QSize(100, 100))
        self.voltDial.setMinimum(300)
        self.voltDial.setMaximum(700)
        self.voltDial.setSingleStep(5)
        self.voltDial.setValue(500)
        self.voltDial.setWrapping(False)
        self.voltDial.setNotchesVisible(True)

        self.sVolt.addWidget(self.voltDial)


        self.formLayout.setLayout(3, QFormLayout.ItemRole.FieldRole, self.sVolt)

        self.buttonSetting = QPushButton(self.settings)
        self.buttonSetting.setObjectName(u"buttonSetting")
        self.buttonSetting.setEnabled(True)
        self.buttonSetting.setAutoDefault(False)

        self.formLayout.setWidget(4, QFormLayout.ItemRole.SpanningRole, self.buttonSetting)

        self.label_10.raise_()
        self.mode_label.raise_()
        self.duration_label.raise_()
        self.sDuration.raise_()
        self.volt_label.raise_()
        self.buttonSetting.raise_()

        self.verticalLayout_2.addWidget(self.settings)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.groupBox = QGroupBox(self.centralwidget)
        self.groupBox.setObjectName(u"groupBox")
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setMinimumSize(QSize(0, 50))
        self.groupBox.setFont(font)
        self.groupBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.groupBox.setFlat(False)
        self.groupBox.setCheckable(False)
        self.verticalLayout = QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.formLayout_2.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.formLayout_2.setContentsMargins(-1, -1, 0, 0)
        self.label_6 = QLabel(self.groupBox)
        self.label_6.setObjectName(u"label_6")

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_6)

        self.radSample = QComboBox(self.groupBox)
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.setObjectName(u"radSample")
        sizePolicy9 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        sizePolicy9.setHorizontalStretch(0)
        sizePolicy9.setVerticalStretch(0)
        sizePolicy9.setHeightForWidth(self.radSample.sizePolicy().hasHeightForWidth())
        self.radSample.setSizePolicy(sizePolicy9)
        self.radSample.setEditable(True)
        self.radSample.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.FieldRole, self.radSample)

        self.label_7 = QLabel(self.groupBox)
        self.label_7.setObjectName(u"label_7")

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_7)

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
        self.groupLetter.setObjectName(u"groupLetter")
        sizePolicy9.setHeightForWidth(self.groupLetter.sizePolicy().hasHeightForWidth())
        self.groupLetter.setSizePolicy(sizePolicy9)
        self.groupLetter.setMaxCount(24)
        self.groupLetter.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.FieldRole, self.groupLetter)

        self.label_5 = QLabel(self.groupBox)
        self.label_5.setObjectName(u"label_5")

        self.formLayout_2.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_5)

        self.suffix = QLineEdit(self.groupBox)
        self.suffix.setObjectName(u"suffix")
        sizePolicy9.setHeightForWidth(self.suffix.sizePolicy().hasHeightForWidth())
        self.suffix.setSizePolicy(sizePolicy9)
        self.suffix.setText(u"")
        self.suffix.setMaxLength(20)

        self.formLayout_2.setWidget(2, QFormLayout.ItemRole.FieldRole, self.suffix)


        self.verticalLayout.addLayout(self.formLayout_2)

        self.buttonSave = QPushButton(self.groupBox)
        self.buttonSave.setObjectName(u"buttonSave")
        self.buttonSave.setEnabled(False)
        sizePolicy10 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy10.setHorizontalStretch(0)
        sizePolicy10.setVerticalStretch(0)
        sizePolicy10.setHeightForWidth(self.buttonSave.sizePolicy().hasHeightForWidth())
        self.buttonSave.setSizePolicy(sizePolicy10)
        self.buttonSave.setMinimumSize(QSize(100, 30))
        self.buttonSave.setMaximumSize(QSize(1000, 40))

        self.verticalLayout.addWidget(self.buttonSave)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(-1, -1, 0, 0)
        self.autoSave = QCheckBox(self.groupBox)
        self.autoSave.setObjectName(u"autoSave")
        sizePolicy2.setHeightForWidth(self.autoSave.sizePolicy().hasHeightForWidth())
        self.autoSave.setSizePolicy(sizePolicy2)
        self.autoSave.setMaximumSize(QSize(850, 16777215))
        self.autoSave.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.autoSave.setChecked(True)
        self.autoSave.setTristate(False)

        self.horizontalLayout_5.addWidget(self.autoSave)


        self.verticalLayout.addLayout(self.horizontalLayout_5)


        self.verticalLayout_2.addWidget(self.groupBox)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(2, 2, 2, 2)
        self.buttonStart = QPushButton(self.centralwidget)
        self.buttonStart.setObjectName(u"buttonStart")
        self.buttonStart.setEnabled(False)
        self.buttonStart.setMinimumSize(QSize(75, 30))
        self.buttonStart.setMaximumSize(QSize(500, 40))

        self.horizontalLayout.addWidget(self.buttonStart)

        self.buttonStop = QPushButton(self.centralwidget)
        self.buttonStop.setObjectName(u"buttonStop")
        self.buttonStop.setEnabled(False)
        self.buttonStop.setMinimumSize(QSize(75, 30))
        self.buttonStop.setMaximumSize(QSize(500, 40))

        self.horizontalLayout.addWidget(self.buttonStop)


        self.verticalLayout_2.addLayout(self.horizontalLayout)


        self.horizontalLayout_3.addLayout(self.verticalLayout_2)

        self.line = QFrame(self.centralwidget)
        self.line.setObjectName(u"line")
        self.line.setFrameShadow(QFrame.Shadow.Plain)
        self.line.setFrameShape(QFrame.Shape.VLine)

        self.horizontalLayout_3.addWidget(self.line)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(-1, -1, 0, -1)
        self.gridGroupBox = QGroupBox(self.centralwidget)
        self.gridGroupBox.setObjectName(u"gridGroupBox")
        sizePolicy11 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy11.setHorizontalStretch(0)
        sizePolicy11.setVerticalStretch(0)
        sizePolicy11.setHeightForWidth(self.gridGroupBox.sizePolicy().hasHeightForWidth())
        self.gridGroupBox.setSizePolicy(sizePolicy11)
        self.gridGroupBox.setFont(font)
        self.gridGroupBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gridGroupBox.setFlat(False)
        self.gridLayout_2 = QGridLayout(self.gridGroupBox)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setHorizontalSpacing(-1)
        self.gridLayout_2.setContentsMargins(-1, 12, -1, -1)
        self.line_2 = QFrame(self.gridGroupBox)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShadow(QFrame.Shadow.Plain)
        self.line_2.setFrameShape(QFrame.Shape.HLine)

        self.gridLayout_2.addWidget(self.line_2, 3, 0, 1, 1)

        self.tabWidget = QTabWidget(self.gridGroupBox)
        self.tabWidget.setObjectName(u"tabWidget")
        sizePolicy12 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy12.setHorizontalStretch(0)
        sizePolicy12.setVerticalStretch(10)
        sizePolicy12.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy12)
        self.timePlot = QWidget()
        self.timePlot.setObjectName(u"timePlot")
        self.tabWidget.addTab(self.timePlot, "")
        self.histogramm = QWidget()
        self.histogramm.setObjectName(u"histogramm")
        sizePolicy13 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy13.setHorizontalStretch(0)
        sizePolicy13.setVerticalStretch(0)
        sizePolicy13.setHeightForWidth(self.histogramm.sizePolicy().hasHeightForWidth())
        self.histogramm.setSizePolicy(sizePolicy13)
        self.gridLayout_4 = QGridLayout(self.histogramm)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setContentsMargins(10, -1, 10, 5)
        self.histWidget = QWidget(self.histogramm)
        self.histWidget.setObjectName(u"histWidget")

        self.gridLayout_4.addWidget(self.histWidget, 1, 0, 1, 1)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_13 = QLabel(self.histogramm)
        self.label_13.setObjectName(u"label_13")

        self.horizontalLayout_6.addWidget(self.label_13)

        self.cStatPoints = QLineEdit(self.histogramm)
        self.cStatPoints.setObjectName(u"cStatPoints")
        self.cStatPoints.setEnabled(True)
        self.cStatPoints.setText(u"")
        self.cStatPoints.setReadOnly(True)

        self.horizontalLayout_6.addWidget(self.cStatPoints)

        self.label_14 = QLabel(self.histogramm)
        self.label_14.setObjectName(u"label_14")

        self.horizontalLayout_6.addWidget(self.label_14)

        self.cStatMin = QLineEdit(self.histogramm)
        self.cStatMin.setObjectName(u"cStatMin")
        self.cStatMin.setEnabled(True)
        self.cStatMin.setText(u"")
        self.cStatMin.setReadOnly(True)

        self.horizontalLayout_6.addWidget(self.cStatMin)

        self.label_15 = QLabel(self.histogramm)
        self.label_15.setObjectName(u"label_15")

        self.horizontalLayout_6.addWidget(self.label_15)

        self.cStatMax = QLineEdit(self.histogramm)
        self.cStatMax.setObjectName(u"cStatMax")
        self.cStatMax.setEnabled(True)
        self.cStatMax.setText(u"")
        self.cStatMax.setReadOnly(True)

        self.horizontalLayout_6.addWidget(self.cStatMax)

        self.label_16 = QLabel(self.histogramm)
        self.label_16.setObjectName(u"label_16")

        self.horizontalLayout_6.addWidget(self.label_16)

        self.cStatAvg = QLineEdit(self.histogramm)
        self.cStatAvg.setObjectName(u"cStatAvg")
        self.cStatAvg.setEnabled(True)
        self.cStatAvg.setText(u"")
        self.cStatAvg.setReadOnly(True)

        self.horizontalLayout_6.addWidget(self.cStatAvg)

        self.label_17 = QLabel(self.histogramm)
        self.label_17.setObjectName(u"label_17")

        self.horizontalLayout_6.addWidget(self.label_17)

        self.cStatSD = QLineEdit(self.histogramm)
        self.cStatSD.setObjectName(u"cStatSD")
        self.cStatSD.setEnabled(True)
        self.cStatSD.setText(u"")
        self.cStatSD.setReadOnly(True)

        self.horizontalLayout_6.addWidget(self.cStatSD)


        self.gridLayout_4.addLayout(self.horizontalLayout_6, 0, 0, 1, 1)

        self.gridLayout_4.setRowStretch(1, 1)
        self.tabWidget.addTab(self.histogramm, "")
        self.list = QWidget()
        self.list.setObjectName(u"list")
        sizePolicy13.setHeightForWidth(self.list.sizePolicy().hasHeightForWidth())
        self.list.setSizePolicy(sizePolicy13)
        self.gridLayout = QGridLayout(self.list)
        self.gridLayout.setObjectName(u"gridLayout")
        self.tableView = QTableView(self.list)
        self.tableView.setObjectName(u"tableView")
        self.tableView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.gridLayout.addWidget(self.tableView, 0, 0, 1, 1)

        self.tabWidget.addTab(self.list, "")

        self.gridLayout_2.addWidget(self.tabWidget, 4, 0, 1, 1)

        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.lastCount = QLCDNumber(self.gridGroupBox)
        self.lastCount.setObjectName(u"lastCount")
        sizePolicy2.setHeightForWidth(self.lastCount.sizePolicy().hasHeightForWidth())
        self.lastCount.setSizePolicy(sizePolicy2)
        self.lastCount.setMinimumSize(QSize(200, 70))
        self.lastCount.setMaximumSize(QSize(0, 70))
        self.lastCount.setFrameShape(QFrame.Shape.Box)
        self.lastCount.setFrameShadow(QFrame.Shadow.Raised)

        self.gridLayout_3.addWidget(self.lastCount, 3, 2, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.statusLED = QLabel(self.gridGroupBox)
        self.statusLED.setObjectName(u"statusLED")
        sizePolicy3.setHeightForWidth(self.statusLED.sizePolicy().hasHeightForWidth())
        self.statusLED.setSizePolicy(sizePolicy3)
        self.statusLED.setMinimumSize(QSize(20, 20))
        self.statusLED.setMaximumSize(QSize(20, 20))
        self.statusLED.setStyleSheet(u"background-color: rgb(255, 11, 3); border: 0px; padding: 4px; border-radius: 10px")
        self.statusLED.setFrameShape(QFrame.Shape.Box)
        self.statusLED.setText(u"")

        self.horizontalLayout_2.addWidget(self.statusLED)

        self.statusText = QLabel(self.gridGroupBox)
        self.statusText.setObjectName(u"statusText")
        sizePolicy1.setHeightForWidth(self.statusText.sizePolicy().hasHeightForWidth())
        self.statusText.setSizePolicy(sizePolicy1)

        self.horizontalLayout_2.addWidget(self.statusText)


        self.gridLayout_3.addLayout(self.horizontalLayout_2, 0, 3, 1, 1)

        self.line_4 = QFrame(self.gridGroupBox)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setFrameShape(QFrame.Shape.VLine)
        self.line_4.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout_3.addWidget(self.line_4, 0, 1, 4, 1)

        self.label_2 = QLabel(self.gridGroupBox)
        self.label_2.setObjectName(u"label_2")
        sizePolicy1.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy1)
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_3.addWidget(self.label_2, 0, 2, 1, 1)

        self.currentCount = QLCDNumber(self.gridGroupBox)
        self.currentCount.setObjectName(u"currentCount")
        sizePolicy2.setHeightForWidth(self.currentCount.sizePolicy().hasHeightForWidth())
        self.currentCount.setSizePolicy(sizePolicy2)
        self.currentCount.setMinimumSize(QSize(200, 70))
        self.currentCount.setMaximumSize(QSize(0, 70))
        self.currentCount.setFrameShape(QFrame.Shape.Box)
        self.currentCount.setFrameShadow(QFrame.Shadow.Raised)

        self.gridLayout_3.addWidget(self.currentCount, 3, 3, 1, 1)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(-1, -1, -1, 0)
        self.progressBar = QProgressBar(self.gridGroupBox)
        self.progressBar.setObjectName(u"progressBar")
        sizePolicy14 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        sizePolicy14.setHorizontalStretch(0)
        sizePolicy14.setVerticalStretch(0)
        sizePolicy14.setHeightForWidth(self.progressBar.sizePolicy().hasHeightForWidth())
        self.progressBar.setSizePolicy(sizePolicy14)
        self.progressBar.setValue(0)

        self.horizontalLayout_4.addWidget(self.progressBar)

        self.progressTimer = QLabel(self.gridGroupBox)
        self.progressTimer.setObjectName(u"progressTimer")
        sizePolicy1.setHeightForWidth(self.progressTimer.sizePolicy().hasHeightForWidth())
        self.progressTimer.setSizePolicy(sizePolicy1)

        self.horizontalLayout_4.addWidget(self.progressTimer)


        self.gridLayout_3.addLayout(self.horizontalLayout_4, 1, 2, 1, 2)

        self.label_3 = QLabel(self.gridGroupBox)
        self.label_3.setObjectName(u"label_3")
        sizePolicy1.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy1)
        self.label_3.setMaximumSize(QSize(16777215, 100))
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignBottom|Qt.AlignmentFlag.AlignHCenter)

        self.gridLayout_3.addWidget(self.label_3, 2, 3, 1, 1)

        self.label_4 = QLabel(self.gridGroupBox)
        self.label_4.setObjectName(u"label_4")
        sizePolicy1.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy1)
        self.label_4.setMaximumSize(QSize(16777215, 100))
        self.label_4.setAlignment(Qt.AlignmentFlag.AlignBottom|Qt.AlignmentFlag.AlignHCenter)

        self.gridLayout_3.addWidget(self.label_4, 2, 2, 1, 1)

        self.formLayout_3 = QFormLayout()
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.formLayout_3.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.formLayout_3.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.label_8 = QLabel(self.gridGroupBox)
        self.label_8.setObjectName(u"label_8")

        self.formLayout_3.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_8)

        self.cVoltage = QLCDNumber(self.gridGroupBox)
        self.cVoltage.setObjectName(u"cVoltage")
        sizePolicy4.setHeightForWidth(self.cVoltage.sizePolicy().hasHeightForWidth())
        self.cVoltage.setSizePolicy(sizePolicy4)
        self.cVoltage.setMinimumSize(QSize(0, 30))
        self.cVoltage.setMaximumSize(QSize(120, 50))
        self.cVoltage.setDigitCount(3)

        self.formLayout_3.setWidget(0, QFormLayout.ItemRole.FieldRole, self.cVoltage)

        self.label_9 = QLabel(self.gridGroupBox)
        self.label_9.setObjectName(u"label_9")

        self.formLayout_3.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_9)

        self.cDuration = QLCDNumber(self.gridGroupBox)
        self.cDuration.setObjectName(u"cDuration")
        sizePolicy4.setHeightForWidth(self.cDuration.sizePolicy().hasHeightForWidth())
        self.cDuration.setSizePolicy(sizePolicy4)
        self.cDuration.setMinimumSize(QSize(100, 30))
        self.cDuration.setMaximumSize(QSize(120, 50))
        self.cDuration.setDigitCount(3)

        self.formLayout_3.setWidget(1, QFormLayout.ItemRole.FieldRole, self.cDuration)

        self.query_label = QLabel(self.gridGroupBox)
        self.query_label.setObjectName(u"query_label")
        sizePolicy1.setHeightForWidth(self.query_label.sizePolicy().hasHeightForWidth())
        self.query_label.setSizePolicy(sizePolicy1)

        self.formLayout_3.setWidget(2, QFormLayout.ItemRole.LabelRole, self.query_label)

        self.cQueryMode = QLabel(self.gridGroupBox)
        self.cQueryMode.setObjectName(u"cQueryMode")
        sizePolicy2.setHeightForWidth(self.cQueryMode.sizePolicy().hasHeightForWidth())
        self.cQueryMode.setSizePolicy(sizePolicy2)
        self.cQueryMode.setMinimumSize(QSize(0, 20))
        self.cQueryMode.setMaximumSize(QSize(120, 50))

        self.formLayout_3.setWidget(2, QFormLayout.ItemRole.FieldRole, self.cQueryMode)

        self.label_12 = QLabel(self.gridGroupBox)
        self.label_12.setObjectName(u"label_12")
        sizePolicy1.setHeightForWidth(self.label_12.sizePolicy().hasHeightForWidth())
        self.label_12.setSizePolicy(sizePolicy1)
        self.label_12.setMinimumSize(QSize(0, 20))

        self.formLayout_3.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_12)

        self.cMode = QLabel(self.gridGroupBox)
        self.cMode.setObjectName(u"cMode")
        sizePolicy2.setHeightForWidth(self.cMode.sizePolicy().hasHeightForWidth())
        self.cMode.setSizePolicy(sizePolicy2)
        self.cMode.setMinimumSize(QSize(0, 20))
        self.cMode.setMaximumSize(QSize(120, 50))

        self.formLayout_3.setWidget(3, QFormLayout.ItemRole.FieldRole, self.cMode)

        self.label = QLabel(self.gridGroupBox)
        self.label.setObjectName(u"label")
        sizePolicy1.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy1)
        self.label.setMinimumSize(QSize(0, 20))

        self.formLayout_3.setWidget(4, QFormLayout.ItemRole.LabelRole, self.label)

        self.cVersion = QLabel(self.gridGroupBox)
        self.cVersion.setObjectName(u"cVersion")
        sizePolicy2.setHeightForWidth(self.cVersion.sizePolicy().hasHeightForWidth())
        self.cVersion.setSizePolicy(sizePolicy2)
        self.cVersion.setMinimumSize(QSize(0, 20))
        self.cVersion.setMaximumSize(QSize(120, 50))

        self.formLayout_3.setWidget(4, QFormLayout.ItemRole.FieldRole, self.cVersion)

        self.label_11 = QLabel(self.gridGroupBox)
        self.label_11.setObjectName(u"label_11")

        self.formLayout_3.setWidget(5, QFormLayout.ItemRole.LabelRole, self.label_11)

        self.cOpenbis = QLabel(self.gridGroupBox)
        self.cOpenbis.setObjectName(u"cOpenbis")
        sizePolicy.setHeightForWidth(self.cOpenbis.sizePolicy().hasHeightForWidth())
        self.cOpenbis.setSizePolicy(sizePolicy)
        self.cOpenbis.setMaximumSize(QSize(120, 50))

        self.formLayout_3.setWidget(5, QFormLayout.ItemRole.FieldRole, self.cOpenbis)


        self.gridLayout_3.addLayout(self.formLayout_3, 1, 0, 3, 1)

        self.label_18 = QLabel(self.gridGroupBox)
        self.label_18.setObjectName(u"label_18")
        sizePolicy.setHeightForWidth(self.label_18.sizePolicy().hasHeightForWidth())
        self.label_18.setSizePolicy(sizePolicy)
        self.label_18.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_3.addWidget(self.label_18, 0, 0, 1, 1)

        self.gridLayout_3.setColumnStretch(1, 1)
        self.gridLayout_3.setColumnStretch(2, 2)
        self.gridLayout_3.setColumnStretch(3, 2)

        self.gridLayout_2.addLayout(self.gridLayout_3, 0, 0, 1, 1)

        self.gridLayout_2.setRowStretch(0, 1)

        self.verticalLayout_3.addWidget(self.gridGroupBox)


        self.horizontalLayout_3.addLayout(self.verticalLayout_3)

        self.horizontalLayout_3.setStretch(2, 5)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1174, 24))
        MainWindow.setMenuBar(self.menubar)
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setObjectName(u"statusBar")
        MainWindow.setStatusBar(self.statusBar)

        self.retranslateUi(MainWindow)
        self.voltDial.valueChanged.connect(self.sVoltage.setValue)
        self.sVoltage.valueChanged.connect(self.voltDial.setValue)

        self.buttonSetting.setDefault(False)
        self.radSample.setCurrentIndex(-1)
        self.groupLetter.setCurrentIndex(-1)
        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"GM-Counter", None))
        self.settings.setTitle(QCoreApplication.translate("MainWindow", u"Einstellungen", None))
        self.mode_label.setText(QCoreApplication.translate("MainWindow", u"Z\u00e4hl-Modus", None))
#if QT_CONFIG(tooltip)
        self.sModeSingle.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>Stoppt die Messung nach Ablauf Z\u00e4hldauer</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.sModeSingle.setText(QCoreApplication.translate("MainWindow", u"Einzel", None))
#if QT_CONFIG(tooltip)
        self.sModeMulti.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>Wiederholt die Messung automatisch nach Ablauf Z\u00e4hldauer</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.sModeMulti.setText(QCoreApplication.translate("MainWindow", u"Wiederholung", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"Abfragemodus", None))
        self.sQModeMan.setText(QCoreApplication.translate("MainWindow", u"Manuell", None))
        self.sQModeAuto.setText(QCoreApplication.translate("MainWindow", u"Automatik", None))
        self.duration_label.setText(QCoreApplication.translate("MainWindow", u"Z\u00e4hldauer", None))
        self.sDuration.setItemText(0, QCoreApplication.translate("MainWindow", u"unendlich", u"f0"))
        self.sDuration.setItemText(1, QCoreApplication.translate("MainWindow", u"1 Sekunde", u"f1"))
        self.sDuration.setItemText(2, QCoreApplication.translate("MainWindow", u"10 Sekunden", u"f2"))
        self.sDuration.setItemText(3, QCoreApplication.translate("MainWindow", u"60 Sekunden", u"f3"))
        self.sDuration.setItemText(4, QCoreApplication.translate("MainWindow", u"100 Sekunden", u"f4"))
        self.sDuration.setItemText(5, QCoreApplication.translate("MainWindow", u"300 Sekunden", u"f5"))

#if QT_CONFIG(tooltip)
        self.sDuration.setToolTip(QCoreApplication.translate("MainWindow", u"Wie lange der Z\u00e4hler misst", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.volt_label.setToolTip(QCoreApplication.translate("MainWindow", u"Spannung des Geiger-M\u00fcller Z\u00e4hlrohrs", None))
#endif // QT_CONFIG(tooltip)
        self.volt_label.setText(QCoreApplication.translate("MainWindow", u"GM-Spannung", None))
        self.sVoltage.setSuffix(QCoreApplication.translate("MainWindow", u" V", None))
        self.buttonSetting.setText(QCoreApplication.translate("MainWindow", u"Einstellungen \u00e4ndern", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"Speicherung", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"Radioaktive Probe*", None))
        self.radSample.setItemText(0, QCoreApplication.translate("MainWindow", u"E00200", None))
        self.radSample.setItemText(1, QCoreApplication.translate("MainWindow", u"E03607", None))
        self.radSample.setItemText(2, QCoreApplication.translate("MainWindow", u"E23303", None))
        self.radSample.setItemText(3, QCoreApplication.translate("MainWindow", u"E30347", None))
        self.radSample.setItemText(4, QCoreApplication.translate("MainWindow", u"E32090", None))
        self.radSample.setItemText(5, QCoreApplication.translate("MainWindow", u"E34316", None))
        self.radSample.setItemText(6, QCoreApplication.translate("MainWindow", u"E38069", None))
        self.radSample.setItemText(7, QCoreApplication.translate("MainWindow", u"E43002", None))
        self.radSample.setItemText(8, QCoreApplication.translate("MainWindow", u"E44367", None))
        self.radSample.setItemText(9, QCoreApplication.translate("MainWindow", u"E52165", None))
        self.radSample.setItemText(10, QCoreApplication.translate("MainWindow", u"E54024", None))
        self.radSample.setItemText(11, QCoreApplication.translate("MainWindow", u"E55600", None))
        self.radSample.setItemText(12, QCoreApplication.translate("MainWindow", u"E62894", None))
        self.radSample.setItemText(13, QCoreApplication.translate("MainWindow", u"E63699", None))
        self.radSample.setItemText(14, QCoreApplication.translate("MainWindow", u"E67594", None))
        self.radSample.setItemText(15, QCoreApplication.translate("MainWindow", u"E75572", None))
        self.radSample.setItemText(16, QCoreApplication.translate("MainWindow", u"E76054", None))
        self.radSample.setItemText(17, QCoreApplication.translate("MainWindow", u"E78857", None))
        self.radSample.setItemText(18, QCoreApplication.translate("MainWindow", u"E80533", None))
        self.radSample.setItemText(19, QCoreApplication.translate("MainWindow", u"E82518", None))
        self.radSample.setItemText(20, QCoreApplication.translate("MainWindow", u"E87198", None))
        self.radSample.setItemText(21, QCoreApplication.translate("MainWindow", u"E89152", None))
        self.radSample.setItemText(22, QCoreApplication.translate("MainWindow", u"E92206", None))
        self.radSample.setItemText(23, QCoreApplication.translate("MainWindow", u"E93652", None))
        self.radSample.setItemText(24, QCoreApplication.translate("MainWindow", u"E93945", None))
        self.radSample.setItemText(25, QCoreApplication.translate("MainWindow", u"E95829", None))
        self.radSample.setItemText(26, QCoreApplication.translate("MainWindow", u"E96269", None))
        self.radSample.setItemText(27, QCoreApplication.translate("MainWindow", u"E99208", None))

#if QT_CONFIG(tooltip)
        self.radSample.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>Auswahl der verwendeten radioaktiven Probe <span style=\" color:#ff001a;\">(Pflichtfeld)</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.radSample.setCurrentText("")
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"Gruppe*", None))
        self.groupLetter.setItemText(0, QCoreApplication.translate("MainWindow", u"A", None))
        self.groupLetter.setItemText(1, QCoreApplication.translate("MainWindow", u"B", None))
        self.groupLetter.setItemText(2, QCoreApplication.translate("MainWindow", u"C", None))
        self.groupLetter.setItemText(3, QCoreApplication.translate("MainWindow", u"D", None))
        self.groupLetter.setItemText(4, QCoreApplication.translate("MainWindow", u"E", None))
        self.groupLetter.setItemText(5, QCoreApplication.translate("MainWindow", u"F", None))
        self.groupLetter.setItemText(6, QCoreApplication.translate("MainWindow", u"G", None))
        self.groupLetter.setItemText(7, QCoreApplication.translate("MainWindow", u"H", None))
        self.groupLetter.setItemText(8, QCoreApplication.translate("MainWindow", u"I", None))
        self.groupLetter.setItemText(9, QCoreApplication.translate("MainWindow", u"J", None))
        self.groupLetter.setItemText(10, QCoreApplication.translate("MainWindow", u"K", None))
        self.groupLetter.setItemText(11, QCoreApplication.translate("MainWindow", u"L", None))
        self.groupLetter.setItemText(12, QCoreApplication.translate("MainWindow", u"M", None))
        self.groupLetter.setItemText(13, QCoreApplication.translate("MainWindow", u"N", None))
        self.groupLetter.setItemText(14, QCoreApplication.translate("MainWindow", u"O", None))
        self.groupLetter.setItemText(15, QCoreApplication.translate("MainWindow", u"P", None))

#if QT_CONFIG(tooltip)
        self.groupLetter.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>Auswahl der GP Praktikumsgruppe <span style=\" color:#ff001a;\">(Pflichtfeld)</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Eigenes Suffix", None))
#if QT_CONFIG(tooltip)
        self.suffix.setToolTip(QCoreApplication.translate("MainWindow", u"Ein benutzerdefiniertes Suffix mit maximal 20 Zeichen", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.buttonSave.setToolTip(QCoreApplication.translate("MainWindow", u"Messung speichern (Dateidialog)", None))
#endif // QT_CONFIG(tooltip)
        self.buttonSave.setText(QCoreApplication.translate("MainWindow", u"Speichern", None))
#if QT_CONFIG(tooltip)
        self.autoSave.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>Bei Aktivierung werden die Messungen automatisch im Format:</p><p>YYYY_MM_DD-<span style=\" font-style:italic;\">Radioaktive Probe</span>-<span style=\" font-style:italic;\">Suffix</span>.csv</p><p>im Ordner Dokumente/Geiger-Mueller/ gespeichert.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.autoSave.setText(QCoreApplication.translate("MainWindow", u"Automatische Speicherung. ", None))
#if QT_CONFIG(tooltip)
        self.buttonStart.setToolTip(QCoreApplication.translate("MainWindow", u"Start der Messung", None))
#endif // QT_CONFIG(tooltip)
        self.buttonStart.setText(QCoreApplication.translate("MainWindow", u"Start", None))
#if QT_CONFIG(tooltip)
        self.buttonStop.setToolTip(QCoreApplication.translate("MainWindow", u"Aktuelle Messung stoppen", None))
#endif // QT_CONFIG(tooltip)
        self.buttonStop.setText(QCoreApplication.translate("MainWindow", u"Stop", None))
        self.gridGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"Live-Metriken", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.timePlot), QCoreApplication.translate("MainWindow", u"Zeitverlauf", None))
        self.label_13.setText(QCoreApplication.translate("MainWindow", u"Anzahl:", None))
        self.label_14.setText(QCoreApplication.translate("MainWindow", u"Min / \u00b5s:", None))
        self.label_15.setText(QCoreApplication.translate("MainWindow", u"Max / \u00b5s:", None))
        self.label_16.setText(QCoreApplication.translate("MainWindow", u"Mittelwert / \u00b5s:", None))
        self.label_17.setText(QCoreApplication.translate("MainWindow", u"Standardabw. / \u00b5s:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.histogramm), QCoreApplication.translate("MainWindow", u"Histogramm", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.list), QCoreApplication.translate("MainWindow", u"Liste", None))
        self.statusText.setText(QCoreApplication.translate("MainWindow", u"unknown", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Status:", None))
        self.progressTimer.setText(QCoreApplication.translate("MainWindow", u"999", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Aktuell", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Voriger Wert", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"GM-Spannung / V", None))
#if QT_CONFIG(tooltip)
        self.cVoltage.setToolTip(QCoreApplication.translate("MainWindow", u"Aktuelle GM-Spannung", None))
#endif // QT_CONFIG(tooltip)
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"Z\u00e4hldauer / s", None))
#if QT_CONFIG(tooltip)
        self.cDuration.setToolTip(QCoreApplication.translate("MainWindow", u"Aktuelle eingestellte Z\u00e4hldauer. 999 f\u00fcr unendllich", None))
#endif // QT_CONFIG(tooltip)
        self.query_label.setText(QCoreApplication.translate("MainWindow", u"Abfragemodus", None))
#if QT_CONFIG(tooltip)
        self.cQueryMode.setToolTip(QCoreApplication.translate("MainWindow", u"Aktuell eingestellter Abfragemodus der Z\u00e4hlergebnisse", None))
#endif // QT_CONFIG(tooltip)
        self.cQueryMode.setText(QCoreApplication.translate("MainWindow", u"unknown", None))
        self.label_12.setText(QCoreApplication.translate("MainWindow", u"Z\u00e4hl-Modus", None))
#if QT_CONFIG(tooltip)
        self.cMode.setToolTip(QCoreApplication.translate("MainWindow", u"Aktuell eingestellter Z\u00e4hlmodus", None))
#endif // QT_CONFIG(tooltip)
        self.cMode.setText(QCoreApplication.translate("MainWindow", u"unknown", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Firmware-Version", None))
#if QT_CONFIG(tooltip)
        self.cVersion.setToolTip(QCoreApplication.translate("MainWindow", u"GM-Z\u00e4hler Firmware", None))
#endif // QT_CONFIG(tooltip)
        self.cVersion.setText(QCoreApplication.translate("MainWindow", u"unknown", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"OpenBIS Code", None))
        self.cOpenbis.setText(QCoreApplication.translate("MainWindow", u"unknown", None))
        self.label_18.setText(QCoreApplication.translate("MainWindow", u"Aktuelle GM-Parameter", None))
    # retranslateUi

