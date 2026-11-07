# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'event_log_panel.ui'
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
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class Ui_EventLogPanel(object):
    def setupUi(self, EventLogPanel):
        if not EventLogPanel.objectName():
            EventLogPanel.setObjectName("EventLogPanel")
        EventLogPanel.resize(480, 140)
        self.layoutEventLogPanel = QVBoxLayout(EventLogPanel)
        self.layoutEventLogPanel.setSpacing(4)
        self.layoutEventLogPanel.setObjectName("layoutEventLogPanel")
        self.layoutEventLogPanel.setContentsMargins(0, 0, 0, 0)
        self.editLog = QPlainTextEdit(EventLogPanel)
        self.editLog.setObjectName("editLog")
        self.editLog.setReadOnly(True)
        self.editLog.setMaximumBlockCount(500)
        self.editLog.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)

        self.layoutEventLogPanel.addWidget(self.editLog)

        self.buttonClear = QPushButton(EventLogPanel)
        self.buttonClear.setObjectName("buttonClear")
        self.buttonClear.setAutoDefault(False)

        self.layoutEventLogPanel.addWidget(self.buttonClear, 0, Qt.AlignRight)

        self.retranslateUi(EventLogPanel)

        QMetaObject.connectSlotsByName(EventLogPanel)

    # setupUi

    def retranslateUi(self, EventLogPanel):
        self.buttonClear.setText(
            QCoreApplication.translate("EventLogPanel", "Leeren", None)
        )
        # if QT_CONFIG(tooltip)
        self.buttonClear.setToolTip(
            QCoreApplication.translate(
                "EventLogPanel", "Ereignisprotokoll leeren", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        pass

    # retranslateUi
