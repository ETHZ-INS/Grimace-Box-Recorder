# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'DConfigureVideoFiles.ui'
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
    QFormLayout, QFrame, QHBoxLayout, QLabel,
    QSizePolicy, QToolButton, QVBoxLayout, QWidget)

class Ui_DConfigureVideoFiles(object):
    def setupUi(self, DConfigureVideoFiles):
        if not DConfigureVideoFiles.objectName():
            DConfigureVideoFiles.setObjectName(u"DConfigureVideoFiles")
        DConfigureVideoFiles.resize(400, 120)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DConfigureVideoFiles.sizePolicy().hasHeightForWidth())
        DConfigureVideoFiles.setSizePolicy(sizePolicy)
        DConfigureVideoFiles.setMinimumSize(QSize(400, 120))
        DConfigureVideoFiles.setMaximumSize(QSize(800, 120))
        self.verticalLayout = QVBoxLayout(DConfigureVideoFiles)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frame = QFrame(DConfigureVideoFiles)
        self.frame.setObjectName(u"frame")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy1)
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.formLayout = QFormLayout(self.frame)
        self.formLayout.setObjectName(u"formLayout")
        self.label_4 = QLabel(self.frame)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setMinimumSize(QSize(0, 44))

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_4)

        self.frame_2 = QFrame(self.frame)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame_2)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.lbl_selected_folder = QLabel(self.frame_2)
        self.lbl_selected_folder.setObjectName(u"lbl_selected_folder")

        self.horizontalLayout.addWidget(self.lbl_selected_folder)

        self.btn_select_folder = QToolButton(self.frame_2)
        self.btn_select_folder.setObjectName(u"btn_select_folder")

        self.horizontalLayout.addWidget(self.btn_select_folder)


        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.frame_2)


        self.verticalLayout.addWidget(self.frame)

        self.btnbox_buttons = QDialogButtonBox(DConfigureVideoFiles)
        self.btnbox_buttons.setObjectName(u"btnbox_buttons")
        self.btnbox_buttons.setOrientation(Qt.Horizontal)
        self.btnbox_buttons.setStandardButtons(QDialogButtonBox.Apply|QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.btnbox_buttons)


        self.retranslateUi(DConfigureVideoFiles)

        QMetaObject.connectSlotsByName(DConfigureVideoFiles)
    # setupUi

    def retranslateUi(self, DConfigureVideoFiles):
        DConfigureVideoFiles.setWindowTitle(QCoreApplication.translate("DConfigureVideoFiles", u"Configure Video Files", None))
        self.label_4.setText(QCoreApplication.translate("DConfigureVideoFiles", u"Target Directory:", None))
        self.lbl_selected_folder.setText(QCoreApplication.translate("DConfigureVideoFiles", u"No Folder Selected", None))
        self.btn_select_folder.setText(QCoreApplication.translate("DConfigureVideoFiles", u"...", None))
    # retranslateUi

