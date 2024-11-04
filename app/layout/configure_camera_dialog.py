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
    QDialogButtonBox, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QLayout, QSizePolicy, QStackedWidget,
    QToolButton, QVBoxLayout, QWidget)

class Ui_DConfigureCamera(object):
    def setupUi(self, DConfigureCamera):
        if not DConfigureCamera.objectName():
            DConfigureCamera.setObjectName(u"DConfigureCamera")
        DConfigureCamera.setWindowModality(Qt.NonModal)
        DConfigureCamera.resize(400, 160)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DConfigureCamera.sizePolicy().hasHeightForWidth())
        DConfigureCamera.setSizePolicy(sizePolicy)
        DConfigureCamera.setMinimumSize(QSize(400, 160))
        DConfigureCamera.setMaximumSize(QSize(800, 160))
        self.verticalLayout = QVBoxLayout(DConfigureCamera)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SetMinAndMaxSize)
        self.frm_camera_type = QFrame(DConfigureCamera)
        self.frm_camera_type.setObjectName(u"frm_camera_type")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.frm_camera_type.sizePolicy().hasHeightForWidth())
        self.frm_camera_type.setSizePolicy(sizePolicy1)
        self.frm_camera_type.setFrameShape(QFrame.StyledPanel)
        self.frm_camera_type.setFrameShadow(QFrame.Raised)
        self.formLayout_2 = QFormLayout(self.frm_camera_type)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.label_4 = QLabel(self.frm_camera_type)
        self.label_4.setObjectName(u"label_4")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_4)

        self.dpd_camera_type = QComboBox(self.frm_camera_type)
        self.dpd_camera_type.addItem("")
        self.dpd_camera_type.addItem("")
        self.dpd_camera_type.setObjectName(u"dpd_camera_type")

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.dpd_camera_type)


        self.verticalLayout.addWidget(self.frm_camera_type)

        self.stk_camera = QStackedWidget(DConfigureCamera)
        self.stk_camera.setObjectName(u"stk_camera")
        self.page_pylon_camera = QWidget()
        self.page_pylon_camera.setObjectName(u"page_pylon_camera")
        self.verticalLayout_2 = QVBoxLayout(self.page_pylon_camera)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(self.page_pylon_camera)
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


        self.verticalLayout_2.addWidget(self.frame)

        self.stk_camera.addWidget(self.page_pylon_camera)
        self.page_file_camera = QWidget()
        self.page_file_camera.setObjectName(u"page_file_camera")
        self.horizontalLayout_2 = QHBoxLayout(self.page_file_camera)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.frame_4 = QFrame(self.page_file_camera)
        self.frame_4.setObjectName(u"frame_4")
        self.frame_4.setFrameShape(QFrame.StyledPanel)
        self.frame_4.setFrameShadow(QFrame.Raised)
        self.formLayout_3 = QFormLayout(self.frame_4)
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.label_5 = QLabel(self.frame_4)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setMinimumSize(QSize(0, 44))

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.label_5)

        self.frame_5 = QFrame(self.frame_4)
        self.frame_5.setObjectName(u"frame_5")
        self.frame_5.setFrameShape(QFrame.StyledPanel)
        self.frame_5.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_3 = QHBoxLayout(self.frame_5)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.lbl_selected_video_file = QLabel(self.frame_5)
        self.lbl_selected_video_file.setObjectName(u"lbl_selected_video_file")

        self.horizontalLayout_3.addWidget(self.lbl_selected_video_file)

        self.btn_select_video_file = QToolButton(self.frame_5)
        self.btn_select_video_file.setObjectName(u"btn_select_video_file")

        self.horizontalLayout_3.addWidget(self.btn_select_video_file)


        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.frame_5)


        self.horizontalLayout_2.addWidget(self.frame_4)

        self.stk_camera.addWidget(self.page_file_camera)

        self.verticalLayout.addWidget(self.stk_camera)

        self.btnbox_buttons = QDialogButtonBox(DConfigureCamera)
        self.btnbox_buttons.setObjectName(u"btnbox_buttons")
        self.btnbox_buttons.setMinimumSize(QSize(0, 0))
        self.btnbox_buttons.setOrientation(Qt.Horizontal)
        self.btnbox_buttons.setStandardButtons(QDialogButtonBox.Apply|QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.btnbox_buttons)


        self.retranslateUi(DConfigureCamera)
        self.btnbox_buttons.accepted.connect(DConfigureCamera.accept)
        self.btnbox_buttons.rejected.connect(DConfigureCamera.reject)

        self.stk_camera.setCurrentIndex(1)
        self.dpd_camera.setCurrentIndex(-1)


        QMetaObject.connectSlotsByName(DConfigureCamera)
    # setupUi

    def retranslateUi(self, DConfigureCamera):
        DConfigureCamera.setWindowTitle(QCoreApplication.translate("DConfigureCamera", u"Configure Top Camera", None))
        self.label_4.setText(QCoreApplication.translate("DConfigureCamera", u"Camera Type:", None))
        self.dpd_camera_type.setItemText(0, QCoreApplication.translate("DConfigureCamera", u"Pylon", None))
        self.dpd_camera_type.setItemText(1, QCoreApplication.translate("DConfigureCamera", u"Video File", None))

        self.label.setText(QCoreApplication.translate("DConfigureCamera", u"Camera:", None))
        self.dpd_camera.setItemText(0, QCoreApplication.translate("DConfigureCamera", u"3423423", None))
        self.dpd_camera.setItemText(1, QCoreApplication.translate("DConfigureCamera", u"2345352", None))

        self.dpd_camera.setCurrentText("")
        self.label_5.setText(QCoreApplication.translate("DConfigureCamera", u"Video File:", None))
        self.lbl_selected_video_file.setText(QCoreApplication.translate("DConfigureCamera", u"No File Selected", None))
        self.btn_select_video_file.setText(QCoreApplication.translate("DConfigureCamera", u"...", None))
    # retranslateUi

