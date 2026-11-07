# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'connection.ui'
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
    QAbstractButton,
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class Ui_ConnectionDialog(object):
    def setupUi(self, ConnectionDialog):
        if not ConnectionDialog.objectName():
            ConnectionDialog.setObjectName("ConnectionDialog")
        ConnectionDialog.resize(550, 500)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ConnectionDialog.sizePolicy().hasHeightForWidth())
        ConnectionDialog.setSizePolicy(sizePolicy)
        ConnectionDialog.setMinimumSize(QSize(550, 500))
        ConnectionDialog.setMaximumSize(QSize(550, 510))
        font = QFont()
        font.setPointSize(12)
        ConnectionDialog.setFont(font)
        ConnectionDialog.setSizeGripEnabled(True)
        self.gridLayout = QGridLayout(ConnectionDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.buttonBox = QDialogButtonBox(ConnectionDialog)
        self.buttonBox.setObjectName("buttonBox")
        font1 = QFont()
        font1.setPointSize(11)
        self.buttonBox.setFont(font1)
        self.buttonBox.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Open
        )

        self.gridLayout.addWidget(self.buttonBox, 8, 0, 1, 1)

        self.labelIntro = QLabel(ConnectionDialog)
        self.labelIntro.setObjectName("labelIntro")
        sizePolicy1 = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.labelIntro.sizePolicy().hasHeightForWidth())
        self.labelIntro.setSizePolicy(sizePolicy1)
        self.labelIntro.setMaximumSize(QSize(700, 500))
        self.labelIntro.setFont(font1)
        self.labelIntro.setTextFormat(Qt.TextFormat.RichText)
        self.labelIntro.setWordWrap(False)
        self.labelIntro.setMargin(0)
        self.labelIntro.setIndent(0)

        self.gridLayout.addWidget(self.labelIntro, 0, 0, 1, 1)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.horizontalLayout = QHBoxLayout()
        # ifndef Q_OS_MAC
        self.horizontalLayout.setSpacing(-1)
        # endif
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.comboPort = QComboBox(ConnectionDialog)
        self.comboPort.setObjectName("comboPort")
        sizePolicy2 = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.comboPort.sizePolicy().hasHeightForWidth())
        self.comboPort.setSizePolicy(sizePolicy2)
        self.comboPort.setMinimumSize(QSize(300, 40))
        self.comboPort.setMaximumSize(QSize(16777215, 60))
        self.comboPort.setBaseSize(QSize(0, 0))
        self.comboPort.setFont(font1)
        self.comboPort.setFrame(True)

        self.horizontalLayout.addWidget(self.comboPort)

        self.buttonRefreshPorts = QPushButton(ConnectionDialog)
        self.buttonRefreshPorts.setObjectName("buttonRefreshPorts")
        sizePolicy3 = QSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum
        )
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(
            self.buttonRefreshPorts.sizePolicy().hasHeightForWidth()
        )
        self.buttonRefreshPorts.setSizePolicy(sizePolicy3)
        self.buttonRefreshPorts.setMinimumSize(QSize(0, 40))
        self.buttonRefreshPorts.setMaximumSize(QSize(35, 40))
        self.buttonRefreshPorts.setFont(font1)
        icon = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.ViewRefresh))
        self.buttonRefreshPorts.setIcon(icon)

        self.horizontalLayout.addWidget(self.buttonRefreshPorts)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.horizontalLayout_3.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.labelBaud = QLabel(ConnectionDialog)
        self.labelBaud.setObjectName("labelBaud")
        sizePolicy4 = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum
        )
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.labelBaud.sizePolicy().hasHeightForWidth())
        self.labelBaud.setSizePolicy(sizePolicy4)
        self.labelBaud.setMinimumSize(QSize(90, 20))
        self.labelBaud.setFont(font1)
        self.labelBaud.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignTrailing
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.horizontalLayout_3.addWidget(self.labelBaud)

        self.comboBaud = QComboBox(ConnectionDialog)
        self.comboBaud.addItem("")
        self.comboBaud.addItem("")
        self.comboBaud.addItem("")
        self.comboBaud.addItem("")
        self.comboBaud.addItem("")
        self.comboBaud.addItem("")
        self.comboBaud.addItem("")
        self.comboBaud.addItem("")
        self.comboBaud.addItem("")
        self.comboBaud.addItem("")
        self.comboBaud.addItem("")
        self.comboBaud.addItem("")
        self.comboBaud.addItem("")
        self.comboBaud.addItem("")
        self.comboBaud.setObjectName("comboBaud")
        sizePolicy2.setHeightForWidth(self.comboBaud.sizePolicy().hasHeightForWidth())
        self.comboBaud.setSizePolicy(sizePolicy2)
        self.comboBaud.setMinimumSize(QSize(0, 40))
        self.comboBaud.setFont(font1)

        self.horizontalLayout_3.addWidget(self.comboBaud)

        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.gridLayout.addLayout(self.verticalLayout, 3, 0, 1, 1)

        self.lineSeparator = QFrame(ConnectionDialog)
        self.lineSeparator.setObjectName("lineSeparator")
        self.lineSeparator.setFont(font1)
        self.lineSeparator.setFrameShape(QFrame.Shape.HLine)
        self.lineSeparator.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.lineSeparator, 2, 0, 1, 1)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.formLayout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.formLayout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )
        self.formLayout.setContentsMargins(8, -1, -1, -1)
        self.labelAddress = QLabel(ConnectionDialog)
        self.labelAddress.setObjectName("labelAddress")
        self.labelAddress.setMinimumSize(QSize(90, 0))
        self.labelAddress.setFont(font1)
        self.labelAddress.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignTrailing
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.labelAddress)

        self.editAddress = QLineEdit(ConnectionDialog)
        self.editAddress.setObjectName("editAddress")
        self.editAddress.setEnabled(True)
        sizePolicy5 = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.editAddress.sizePolicy().hasHeightForWidth())
        self.editAddress.setSizePolicy(sizePolicy5)
        self.editAddress.setFont(font1)
        self.editAddress.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.editAddress.setMouseTracking(False)
        self.editAddress.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.editAddress.setAutoFillBackground(False)
        self.editAddress.setText("")
        self.editAddress.setFrame(False)
        self.editAddress.setReadOnly(True)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.editAddress)

        self.labelName = QLabel(ConnectionDialog)
        self.labelName.setObjectName("labelName")
        self.labelName.setMinimumSize(QSize(90, 0))
        self.labelName.setFont(font1)
        self.labelName.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignTrailing
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.labelName)

        self.editName = QLineEdit(ConnectionDialog)
        self.editName.setObjectName("editName")
        self.editName.setEnabled(True)
        self.editName.setFont(font1)
        self.editName.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.editName.setFrame(False)
        self.editName.setReadOnly(True)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.editName)

        self.labelDescription = QLabel(ConnectionDialog)
        self.labelDescription.setObjectName("labelDescription")
        self.labelDescription.setMinimumSize(QSize(90, 0))
        self.labelDescription.setFont(font1)
        self.labelDescription.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignTrailing
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.formLayout.setWidget(
            2, QFormLayout.ItemRole.LabelRole, self.labelDescription
        )

        self.editDescription = QLineEdit(ConnectionDialog)
        self.editDescription.setObjectName("editDescription")
        self.editDescription.setEnabled(True)
        self.editDescription.setFont(font1)
        self.editDescription.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.editDescription.setFrame(False)
        self.editDescription.setReadOnly(True)

        self.formLayout.setWidget(
            2, QFormLayout.ItemRole.FieldRole, self.editDescription
        )

        self.gridLayout.addLayout(self.formLayout, 5, 0, 1, 1)

        self.valueStatus = QLabel(ConnectionDialog)
        self.valueStatus.setObjectName("valueStatus")
        self.valueStatus.setMinimumSize(QSize(0, 30))
        self.valueStatus.setFont(font1)
        self.valueStatus.setWordWrap(True)

        self.gridLayout.addWidget(self.valueStatus, 1, 0, 1, 1)

        self.retranslateUi(ConnectionDialog)
        self.buttonBox.rejected.connect(ConnectionDialog.reject)
        self.buttonBox.accepted.connect(ConnectionDialog.accept)

        self.comboBaud.setCurrentIndex(12)

        QMetaObject.connectSlotsByName(ConnectionDialog)

    # setupUi

    def retranslateUi(self, ConnectionDialog):
        ConnectionDialog.setWindowTitle(
            QCoreApplication.translate(
                "ConnectionDialog", "Verbindung herstellen", None
            )
        )
        self.labelIntro.setText(
            QCoreApplication.translate(
                "ConnectionDialog",
                '<html><head/><body><p>Einen Port und passende Baud-Rate ausw\u00e4hlen und mit &quot;\u00d6ffnen&quot; verbinden. </p><p><span style=" color:#ff9300;">Besonderheit Windows:</span></p><p>Ger\u00e4teinformationen werden nicht korrekt dargestellt. Meistens ist es der letzte &quot;COM&quot; Port. </p><p>Ansonsten: </p><p>GM-Z\u00e4hler abstecken, Liste aktualisieren, Z\u00e4hler anstecken, Liste aktualisieren, <br/>Neuen Port ausw\u00e4hlen</p></body></html>',
                None,
            )
        )
        # if QT_CONFIG(tooltip)
        self.comboPort.setToolTip(
            QCoreApplication.translate(
                "ConnectionDialog",
                "<html><head/><body><p>Kommunikation mit dem Arduino erfolgt \u00fcber die serielle Schnittstelle. </p><p>Wenn Arduino nicht erkannt wird, die Verbindung pr\u00fcfen und evtl. Treiber installieren.</p></body></html>",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.comboPort.setPlaceholderText(
            QCoreApplication.translate(
                "ConnectionDialog", "Bitte Seriellen Port ausw\u00e4hlen", None
            )
        )
        # if QT_CONFIG(tooltip)
        self.buttonRefreshPorts.setToolTip(
            QCoreApplication.translate(
                "ConnectionDialog", "Die Liste der Ports aktualisieren", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.buttonRefreshPorts.setText("")
        self.labelBaud.setText(
            QCoreApplication.translate("ConnectionDialog", "Baud Rate", None)
        )
        self.comboBaud.setItemText(
            0, QCoreApplication.translate("ConnectionDialog", "2400", None)
        )
        self.comboBaud.setItemText(
            1, QCoreApplication.translate("ConnectionDialog", "4800", None)
        )
        self.comboBaud.setItemText(
            2, QCoreApplication.translate("ConnectionDialog", "9600", None)
        )
        self.comboBaud.setItemText(
            3, QCoreApplication.translate("ConnectionDialog", "14400", None)
        )
        self.comboBaud.setItemText(
            4, QCoreApplication.translate("ConnectionDialog", "19200", None)
        )
        self.comboBaud.setItemText(
            5, QCoreApplication.translate("ConnectionDialog", "38400", None)
        )
        self.comboBaud.setItemText(
            6, QCoreApplication.translate("ConnectionDialog", "57600", None)
        )
        self.comboBaud.setItemText(
            7, QCoreApplication.translate("ConnectionDialog", "115200", None)
        )
        self.comboBaud.setItemText(
            8, QCoreApplication.translate("ConnectionDialog", "230400", None)
        )
        self.comboBaud.setItemText(
            9, QCoreApplication.translate("ConnectionDialog", "460800", None)
        )
        self.comboBaud.setItemText(
            10, QCoreApplication.translate("ConnectionDialog", "500000", None)
        )
        self.comboBaud.setItemText(
            11, QCoreApplication.translate("ConnectionDialog", "921600", None)
        )
        self.comboBaud.setItemText(
            12, QCoreApplication.translate("ConnectionDialog", "1000000", None)
        )
        self.comboBaud.setItemText(
            13, QCoreApplication.translate("ConnectionDialog", "2000000", None)
        )

        self.labelAddress.setText(
            QCoreApplication.translate("ConnectionDialog", "Adresse", None)
        )
        self.labelName.setText(
            QCoreApplication.translate("ConnectionDialog", "Name", None)
        )
        self.labelDescription.setText(
            QCoreApplication.translate("ConnectionDialog", "Beschreibung", None)
        )
        self.editDescription.setPlaceholderText("")
        self.valueStatus.setText("")

    # retranslateUi
