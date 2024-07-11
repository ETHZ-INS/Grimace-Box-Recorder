# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'DConfigureCamera.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QDoubleSpinBox, QFormLayout, QFrame,
    QHBoxLayout, QLabel, QLayout, QSizePolicy,
    QToolButton, QVBoxLayout, QWidget)

class Ui_DConfigureCamera(object):
    def setupUi(self, DConfigureCamera):
        if not DConfigureCamera.objectName():
            DConfigureCamera.setObjectName(u"DConfigureCamera")
        DConfigureCamera.setWindowModality(Qt.NonModal)
        DConfigureCamera.resize(400, 200)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DConfigureCamera.sizePolicy().hasHeightForWidth())
        DConfigureCamera.setSizePolicy(sizePolicy)
        DConfigureCamera.setMinimumSize(QSize(400, 200))
        DConfigureCamera.setMaximumSize(QSize(800, 200))
        self.verticalLayout = QVBoxLayout(DConfigureCamera)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SetMinAndMaxSize)
        self.lbl_title = QLabel(DConfigureCamera)
        self.lbl_title.setObjectName(u"lbl_title")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.lbl_title.sizePolicy().hasHeightForWidth())
        self.lbl_title.setSizePolicy(sizePolicy1)

        self.verticalLayout.addWidget(self.lbl_title)

        self.frame = QFrame(DConfigureCamera)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.formLayout = QFormLayout(self.frame)
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.dpd_camera = QComboBox(self.frame)
        self.dpd_camera.addItem("")
        self.dpd_camera.addItem("")
        self.dpd_camera.setObjectName(u"dpd_camera")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.dpd_camera)

        self.label_3 = QLabel(self.frame)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setMinimumSize(QSize(0, 44))

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_3)

        self.frame_2 = QFrame(self.frame)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame_2)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.lbl_selected_file = QLabel(self.frame_2)
        self.lbl_selected_file.setObjectName(u"lbl_selected_file")

        self.horizontalLayout.addWidget(self.lbl_selected_file)

        self.btn_select_file = QToolButton(self.frame_2)
        self.btn_select_file.setObjectName(u"btn_select_file")

        self.horizontalLayout.addWidget(self.btn_select_file)


        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.frame_2)

        self.spb_fps = QDoubleSpinBox(self.frame)
        self.spb_fps.setObjectName(u"spb_fps")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.spb_fps)

        self.label_2 = QLabel(self.frame)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_2)


        self.verticalLayout.addWidget(self.frame)

        self.btnbox_buttons = QDialogButtonBox(DConfigureCamera)
        self.btnbox_buttons.setObjectName(u"btnbox_buttons")
        self.btnbox_buttons.setOrientation(Qt.Horizontal)
        self.btnbox_buttons.setStandardButtons(QDialogButtonBox.Apply|QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.btnbox_buttons)


        self.retranslateUi(DConfigureCamera)
        self.btnbox_buttons.accepted.connect(DConfigureCamera.accept)
        self.btnbox_buttons.rejected.connect(DConfigureCamera.reject)

        self.dpd_camera.setCurrentIndex(-1)


        QMetaObject.connectSlotsByName(DConfigureCamera)
    # setupUi

    def retranslateUi(self, DConfigureCamera):
        DConfigureCamera.setWindowTitle(QCoreApplication.translate("DConfigureCamera", u"Configure Top Camera", None))
        self.lbl_title.setText(QCoreApplication.translate("DConfigureCamera", u"Configure Top Camera", None))
        self.label.setText(QCoreApplication.translate("DConfigureCamera", u"Camera:", None))
        self.dpd_camera.setItemText(0, QCoreApplication.translate("DConfigureCamera", u"3423423", None))
        self.dpd_camera.setItemText(1, QCoreApplication.translate("DConfigureCamera", u"2345352", None))

        self.dpd_camera.setCurrentText("")
        self.label_3.setText(QCoreApplication.translate("DConfigureCamera", u"Config File:", None))
        self.lbl_selected_file.setText(QCoreApplication.translate("DConfigureCamera", u"No File Selected", None))
        self.btn_select_file.setText(QCoreApplication.translate("DConfigureCamera", u"...", None))
        self.label_2.setText(QCoreApplication.translate("DConfigureCamera", u"FPS:", None))
    # retranslateUi

