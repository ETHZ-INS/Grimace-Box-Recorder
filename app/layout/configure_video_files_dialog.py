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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QSizePolicy, QToolButton,
    QVBoxLayout, QWidget)

class Ui_DConfigureVideoFiles(object):
    def setupUi(self, DConfigureVideoFiles):
        if not DConfigureVideoFiles.objectName():
            DConfigureVideoFiles.setObjectName(u"DConfigureVideoFiles")
        DConfigureVideoFiles.resize(400, 250)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DConfigureVideoFiles.sizePolicy().hasHeightForWidth())
        DConfigureVideoFiles.setSizePolicy(sizePolicy)
        DConfigureVideoFiles.setMinimumSize(QSize(400, 250))
        DConfigureVideoFiles.setMaximumSize(QSize(800, 250))
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

        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label)

        self.dpd_naming_mode = QComboBox(self.frame)
        self.dpd_naming_mode.addItem("")
        self.dpd_naming_mode.addItem("")
        self.dpd_naming_mode.addItem("")
        self.dpd_naming_mode.setObjectName(u"dpd_naming_mode")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.dpd_naming_mode)

        self.label_3 = QLabel(self.frame)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_3)

        self.txt_template_top = QLineEdit(self.frame)
        self.txt_template_top.setObjectName(u"txt_template_top")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.txt_template_top)

        self.label_2 = QLabel(self.frame)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_2)

        self.txt_template_front = QLineEdit(self.frame)
        self.txt_template_front.setObjectName(u"txt_template_front")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.txt_template_front)

        self.label_5 = QLabel(self.frame)
        self.label_5.setObjectName(u"label_5")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label_5)

        self.txt_template_grimace = QLineEdit(self.frame)
        self.txt_template_grimace.setObjectName(u"txt_template_grimace")

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.txt_template_grimace)

        self.label_6 = QLabel(self.frame)
        self.label_6.setObjectName(u"label_6")

        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.label_6)

        self.txt_template_pose = QLineEdit(self.frame)
        self.txt_template_pose.setObjectName(u"txt_template_pose")

        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.txt_template_pose)


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
        self.label.setText(QCoreApplication.translate("DConfigureVideoFiles", u"Naming Mode:", None))
        self.dpd_naming_mode.setItemText(0, QCoreApplication.translate("DConfigureVideoFiles", u"Incremental Number", None))
        self.dpd_naming_mode.setItemText(1, QCoreApplication.translate("DConfigureVideoFiles", u"Start Time", None))
        self.dpd_naming_mode.setItemText(2, QCoreApplication.translate("DConfigureVideoFiles", u"Custom Template", None))

        self.label_3.setText(QCoreApplication.translate("DConfigureVideoFiles", u"Top Video:", None))
        self.txt_template_top.setText(QCoreApplication.translate("DConfigureVideoFiles", u"{recording_number}_top.avi", None))
        self.label_2.setText(QCoreApplication.translate("DConfigureVideoFiles", u"Front Video:", None))
        self.txt_template_front.setText(QCoreApplication.translate("DConfigureVideoFiles", u"{recording_number}_front.avi", None))
        self.label_5.setText(QCoreApplication.translate("DConfigureVideoFiles", u"Grimace Results:", None))
        self.txt_template_grimace.setText(QCoreApplication.translate("DConfigureVideoFiles", u"{recording_number}_grimace_results.csv", None))
        self.label_6.setText(QCoreApplication.translate("DConfigureVideoFiles", u"Pose Results:", None))
        self.txt_template_pose.setText(QCoreApplication.translate("DConfigureVideoFiles", u"{recording_number}_pose_estimation_results.csv", None))
    # retranslateUi

