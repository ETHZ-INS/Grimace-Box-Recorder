# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'DConfigureBothCameras.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialogButtonBox,
    QFormLayout, QFrame, QHBoxLayout, QLabel,
    QSizePolicy, QStackedWidget, QToolButton, QVBoxLayout,
    QWidget)

class Ui_DConfigureBothCameras(object):
    def setupUi(self, DConfigureBothCameras):
        if not DConfigureBothCameras.objectName():
            DConfigureBothCameras.setObjectName(u"DConfigureBothCameras")
        DConfigureBothCameras.resize(400, 250)
        DConfigureBothCameras.setMinimumSize(QSize(400, 250))
        DConfigureBothCameras.setMaximumSize(QSize(800, 250))
        self.verticalLayout = QVBoxLayout(DConfigureBothCameras)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frm_camera_type = QFrame(DConfigureBothCameras)
        self.frm_camera_type.setObjectName(u"frm_camera_type")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frm_camera_type.sizePolicy().hasHeightForWidth())
        self.frm_camera_type.setSizePolicy(sizePolicy)
        self.frm_camera_type.setFrameShape(QFrame.StyledPanel)
        self.frm_camera_type.setFrameShadow(QFrame.Raised)
        self.formLayout_2 = QFormLayout(self.frm_camera_type)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.label_4 = QLabel(self.frm_camera_type)
        self.label_4.setObjectName(u"label_4")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_4)

        self.dpd_top_camera_type = QComboBox(self.frm_camera_type)
        self.dpd_top_camera_type.addItem("")
        self.dpd_top_camera_type.addItem("")
        self.dpd_top_camera_type.setObjectName(u"dpd_top_camera_type")

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.dpd_top_camera_type)

        self.label_6 = QLabel(self.frm_camera_type)
        self.label_6.setObjectName(u"label_6")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label_6)

        self.dpd_front_camera_type = QComboBox(self.frm_camera_type)
        self.dpd_front_camera_type.addItem("")
        self.dpd_front_camera_type.addItem("")
        self.dpd_front_camera_type.setObjectName(u"dpd_front_camera_type")

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.dpd_front_camera_type)


        self.verticalLayout.addWidget(self.frm_camera_type)

        self.stk_camera = QStackedWidget(DConfigureBothCameras)
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

        self.label_2 = QLabel(self.frame)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.dpd_top_camera = QComboBox(self.frame)
        self.dpd_top_camera.addItem("")
        self.dpd_top_camera.addItem("")
        self.dpd_top_camera.setObjectName(u"dpd_top_camera")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.dpd_top_camera)

        self.dpd_front_camera = QComboBox(self.frame)
        self.dpd_front_camera.setObjectName(u"dpd_front_camera")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.dpd_front_camera)


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
        self.lbl_top_selected_video_file = QLabel(self.frame_5)
        self.lbl_top_selected_video_file.setObjectName(u"lbl_top_selected_video_file")

        self.horizontalLayout_3.addWidget(self.lbl_top_selected_video_file)

        self.btn_select_front_video_file = QToolButton(self.frame_5)
        self.btn_select_front_video_file.setObjectName(u"btn_select_front_video_file")

        self.horizontalLayout_3.addWidget(self.btn_select_front_video_file)


        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.frame_5)

        self.label_3 = QLabel(self.frame_4)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setMinimumSize(QSize(0, 44))

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.label_3)

        self.frame_6 = QFrame(self.frame_4)
        self.frame_6.setObjectName(u"frame_6")
        self.frame_6.setFrameShape(QFrame.StyledPanel)
        self.frame_6.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.frame_6)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.lbl_front_selected_video_file = QLabel(self.frame_6)
        self.lbl_front_selected_video_file.setObjectName(u"lbl_front_selected_video_file")

        self.horizontalLayout_4.addWidget(self.lbl_front_selected_video_file)

        self.btn_select_top_video_file = QToolButton(self.frame_6)
        self.btn_select_top_video_file.setObjectName(u"btn_select_top_video_file")

        self.horizontalLayout_4.addWidget(self.btn_select_top_video_file)


        self.formLayout_3.setWidget(1, QFormLayout.FieldRole, self.frame_6)


        self.horizontalLayout_2.addWidget(self.frame_4)

        self.stk_camera.addWidget(self.page_file_camera)
        self.page_camera_video = QWidget()
        self.page_camera_video.setObjectName(u"page_camera_video")
        self.formLayout_6 = QFormLayout(self.page_camera_video)
        self.formLayout_6.setObjectName(u"formLayout_6")
        self.label_11 = QLabel(self.page_camera_video)
        self.label_11.setObjectName(u"label_11")

        self.formLayout_6.setWidget(0, QFormLayout.LabelRole, self.label_11)

        self.label_12 = QLabel(self.page_camera_video)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setMinimumSize(QSize(0, 44))

        self.formLayout_6.setWidget(1, QFormLayout.LabelRole, self.label_12)

        self.frame_7 = QFrame(self.page_camera_video)
        self.frame_7.setObjectName(u"frame_7")
        self.frame_7.setFrameShape(QFrame.StyledPanel)
        self.frame_7.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_8 = QHBoxLayout(self.frame_7)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.lbl_front_selected_video_file_2 = QLabel(self.frame_7)
        self.lbl_front_selected_video_file_2.setObjectName(u"lbl_front_selected_video_file_2")

        self.horizontalLayout_8.addWidget(self.lbl_front_selected_video_file_2)

        self.btn_select_front_video_file_2 = QToolButton(self.frame_7)
        self.btn_select_front_video_file_2.setObjectName(u"btn_select_front_video_file_2")

        self.horizontalLayout_8.addWidget(self.btn_select_front_video_file_2)


        self.formLayout_6.setWidget(1, QFormLayout.FieldRole, self.frame_7)

        self.dpd_top_camera_2 = QComboBox(self.page_camera_video)
        self.dpd_top_camera_2.setObjectName(u"dpd_top_camera_2")

        self.formLayout_6.setWidget(0, QFormLayout.FieldRole, self.dpd_top_camera_2)

        self.stk_camera.addWidget(self.page_camera_video)
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.formLayout_4 = QFormLayout(self.page)
        self.formLayout_4.setObjectName(u"formLayout_4")
        self.label_7 = QLabel(self.page)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setMinimumSize(QSize(0, 44))

        self.formLayout_4.setWidget(0, QFormLayout.LabelRole, self.label_7)

        self.label_8 = QLabel(self.page)
        self.label_8.setObjectName(u"label_8")

        self.formLayout_4.setWidget(1, QFormLayout.LabelRole, self.label_8)

        self.dpd_front_camera_2 = QComboBox(self.page)
        self.dpd_front_camera_2.setObjectName(u"dpd_front_camera_2")

        self.formLayout_4.setWidget(1, QFormLayout.FieldRole, self.dpd_front_camera_2)

        self.frame_8 = QFrame(self.page)
        self.frame_8.setObjectName(u"frame_8")
        self.frame_8.setFrameShape(QFrame.StyledPanel)
        self.frame_8.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_9 = QHBoxLayout(self.frame_8)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.lbl_top_selected_video_file_2 = QLabel(self.frame_8)
        self.lbl_top_selected_video_file_2.setObjectName(u"lbl_top_selected_video_file_2")

        self.horizontalLayout_9.addWidget(self.lbl_top_selected_video_file_2)

        self.btn_select_top_video_file_2 = QToolButton(self.frame_8)
        self.btn_select_top_video_file_2.setObjectName(u"btn_select_top_video_file_2")

        self.horizontalLayout_9.addWidget(self.btn_select_top_video_file_2)


        self.formLayout_4.setWidget(0, QFormLayout.FieldRole, self.frame_8)

        self.stk_camera.addWidget(self.page)

        self.verticalLayout.addWidget(self.stk_camera)

        self.btnbox_buttons = QDialogButtonBox(DConfigureBothCameras)
        self.btnbox_buttons.setObjectName(u"btnbox_buttons")
        self.btnbox_buttons.setOrientation(Qt.Horizontal)
        self.btnbox_buttons.setStandardButtons(QDialogButtonBox.Apply|QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.btnbox_buttons)


        self.retranslateUi(DConfigureBothCameras)

        self.stk_camera.setCurrentIndex(3)
        self.dpd_top_camera.setCurrentIndex(-1)


        QMetaObject.connectSlotsByName(DConfigureBothCameras)
    # setupUi

    def retranslateUi(self, DConfigureBothCameras):
        DConfigureBothCameras.setWindowTitle(QCoreApplication.translate("DConfigureBothCameras", u"Configure Cameras", None))
        self.label_4.setText(QCoreApplication.translate("DConfigureBothCameras", u"Top Camera Type:", None))
        self.dpd_top_camera_type.setItemText(0, QCoreApplication.translate("DConfigureBothCameras", u"Pylon", None))
        self.dpd_top_camera_type.setItemText(1, QCoreApplication.translate("DConfigureBothCameras", u"Video File", None))

        self.label_6.setText(QCoreApplication.translate("DConfigureBothCameras", u"Front Camera Type:", None))
        self.dpd_front_camera_type.setItemText(0, QCoreApplication.translate("DConfigureBothCameras", u"Pylon", None))
        self.dpd_front_camera_type.setItemText(1, QCoreApplication.translate("DConfigureBothCameras", u"Video File", None))

        self.label.setText(QCoreApplication.translate("DConfigureBothCameras", u"Top Camera:", None))
        self.label_2.setText(QCoreApplication.translate("DConfigureBothCameras", u"Front Camera:", None))
        self.dpd_top_camera.setItemText(0, QCoreApplication.translate("DConfigureBothCameras", u"3423423", None))
        self.dpd_top_camera.setItemText(1, QCoreApplication.translate("DConfigureBothCameras", u"2345352", None))

        self.dpd_top_camera.setCurrentText("")
        self.label_5.setText(QCoreApplication.translate("DConfigureBothCameras", u"Top Video File:", None))
        self.lbl_top_selected_video_file.setText(QCoreApplication.translate("DConfigureBothCameras", u"No File Selected", None))
        self.btn_select_front_video_file.setText(QCoreApplication.translate("DConfigureBothCameras", u"...", None))
        self.label_3.setText(QCoreApplication.translate("DConfigureBothCameras", u"Front Video File:", None))
        self.lbl_front_selected_video_file.setText(QCoreApplication.translate("DConfigureBothCameras", u"No File Selected", None))
        self.btn_select_top_video_file.setText(QCoreApplication.translate("DConfigureBothCameras", u"...", None))
        self.label_11.setText(QCoreApplication.translate("DConfigureBothCameras", u"Top Camera:", None))
        self.label_12.setText(QCoreApplication.translate("DConfigureBothCameras", u"Front Video File:", None))
        self.lbl_front_selected_video_file_2.setText(QCoreApplication.translate("DConfigureBothCameras", u"No File Selected", None))
        self.btn_select_front_video_file_2.setText(QCoreApplication.translate("DConfigureBothCameras", u"...", None))
        self.label_7.setText(QCoreApplication.translate("DConfigureBothCameras", u"Top Video File:", None))
        self.label_8.setText(QCoreApplication.translate("DConfigureBothCameras", u"Front Camera:", None))
        self.lbl_top_selected_video_file_2.setText(QCoreApplication.translate("DConfigureBothCameras", u"No File Selected", None))
        self.btn_select_top_video_file_2.setText(QCoreApplication.translate("DConfigureBothCameras", u"...", None))
    # retranslateUi

