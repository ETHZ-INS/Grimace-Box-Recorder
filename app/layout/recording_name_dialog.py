# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'DRecordingName.ui'
##
## Created by: Qt User Interface Compiler version 6.7.1
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QLabel, QLineEdit, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_DRecordingName(object):
    def setupUi(self, DRecordingName):
        if not DRecordingName.objectName():
            DRecordingName.setObjectName(u"DRecordingName")
        DRecordingName.resize(400, 200)
        DRecordingName.setMinimumSize(QSize(400, 200))
        DRecordingName.setMaximumSize(QSize(400, 200))
        self.verticalLayout = QVBoxLayout(DRecordingName)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(DRecordingName)
        self.label.setObjectName(u"label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)

        self.verticalLayout.addWidget(self.label)

        self.txt_recording_name = QLineEdit(DRecordingName)
        self.txt_recording_name.setObjectName(u"txt_recording_name")

        self.verticalLayout.addWidget(self.txt_recording_name)

        self.label_2 = QLabel(DRecordingName)
        self.label_2.setObjectName(u"label_2")

        self.verticalLayout.addWidget(self.label_2)

        self.label_4 = QLabel(DRecordingName)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setAlignment(Qt.AlignBottom|Qt.AlignLeading|Qt.AlignLeft)

        self.verticalLayout.addWidget(self.label_4)

        self.lbl_preview = QLabel(DRecordingName)
        self.lbl_preview.setObjectName(u"lbl_preview")
        self.lbl_preview.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.verticalLayout.addWidget(self.lbl_preview)

        self.btnbox_buttons = QDialogButtonBox(DRecordingName)
        self.btnbox_buttons.setObjectName(u"btnbox_buttons")
        self.btnbox_buttons.setMinimumSize(QSize(0, 0))
        self.btnbox_buttons.setMaximumSize(QSize(16777215, 16777215))
        self.btnbox_buttons.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.btnbox_buttons)


        self.retranslateUi(DRecordingName)

        QMetaObject.connectSlotsByName(DRecordingName)
    # setupUi

    def retranslateUi(self, DRecordingName):
        DRecordingName.setWindowTitle(QCoreApplication.translate("DRecordingName", u"Set Recording Name", None))
        self.label.setText(QCoreApplication.translate("DRecordingName", u"Recording Identifier (Optional):", None))
        self.txt_recording_name.setText("")
        self.txt_recording_name.setPlaceholderText(QCoreApplication.translate("DRecordingName", u"animal_xyz_day_n", None))
        self.label_2.setText(QCoreApplication.translate("DRecordingName", u"Enter an optional prefix for the recording files.\n"
"The filenames will always include an incremental number suffix.", None))
        self.label_4.setText(QCoreApplication.translate("DRecordingName", u"Preview:", None))
        self.lbl_preview.setText(QCoreApplication.translate("DRecordingName", u"animal_xyz_day_n_grimace_results_1.csv", None))
    # retranslateUi

