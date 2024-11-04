# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'DConfigurePoseTracking.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QComboBox,
    QDialog, QDialogButtonBox, QFormLayout, QFrame,
    QLabel, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_DConfigurePoseTracking(object):
    def setupUi(self, DConfigurePoseTracking):
        if not DConfigurePoseTracking.objectName():
            DConfigurePoseTracking.setObjectName(u"DConfigurePoseTracking")
        DConfigurePoseTracking.resize(400, 250)
        DConfigurePoseTracking.setMinimumSize(QSize(400, 250))
        DConfigurePoseTracking.setMaximumSize(QSize(400, 250))
        self.verticalLayout = QVBoxLayout(DConfigurePoseTracking)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frame = QFrame(DConfigurePoseTracking)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.formLayout = QFormLayout(self.frame)
        self.formLayout.setObjectName(u"formLayout")
        self.label_2 = QLabel(self.frame)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_2)

        self.dpd_pose_model = QComboBox(self.frame)
        self.dpd_pose_model.addItem("")
        self.dpd_pose_model.setObjectName(u"dpd_pose_model")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.dpd_pose_model)

        self.label_5 = QLabel(self.frame)
        self.label_5.setObjectName(u"label_5")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_5)

        self.chb_show_pose_preview = QCheckBox(self.frame)
        self.chb_show_pose_preview.setObjectName(u"chb_show_pose_preview")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.chb_show_pose_preview)

        self.verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.formLayout.setItem(2, QFormLayout.LabelRole, self.verticalSpacer)

        self.label_4 = QLabel(self.frame)
        self.label_4.setObjectName(u"label_4")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_4)

        self.label_3 = QLabel(self.frame)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label_3)

        self.dpd_pose_tracking_device = QComboBox(self.frame)
        self.dpd_pose_tracking_device.setObjectName(u"dpd_pose_tracking_device")

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.dpd_pose_tracking_device)


        self.verticalLayout.addWidget(self.frame)

        self.btnbox_buttons = QDialogButtonBox(DConfigurePoseTracking)
        self.btnbox_buttons.setObjectName(u"btnbox_buttons")
        self.btnbox_buttons.setOrientation(Qt.Horizontal)
        self.btnbox_buttons.setStandardButtons(QDialogButtonBox.Apply|QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.btnbox_buttons)


        self.retranslateUi(DConfigurePoseTracking)
        self.btnbox_buttons.accepted.connect(DConfigurePoseTracking.accept)
        self.btnbox_buttons.rejected.connect(DConfigurePoseTracking.reject)

        QMetaObject.connectSlotsByName(DConfigurePoseTracking)
    # setupUi

    def retranslateUi(self, DConfigurePoseTracking):
        DConfigurePoseTracking.setWindowTitle(QCoreApplication.translate("DConfigurePoseTracking", u"Configure Pose Estimation", None))
        self.label_2.setText(QCoreApplication.translate("DConfigurePoseTracking", u"Pose Tracking Model:", None))
        self.dpd_pose_model.setItemText(0, QCoreApplication.translate("DConfigurePoseTracking", u"V1 - Hohlbot", None))

        self.label_5.setText(QCoreApplication.translate("DConfigurePoseTracking", u"Show Pose on Preview:", None))
        self.chb_show_pose_preview.setText(QCoreApplication.translate("DConfigurePoseTracking", u"(May cause performance issues)", None))
        self.label_4.setText(QCoreApplication.translate("DConfigurePoseTracking", u"Device Selection:", None))
        self.label_3.setText(QCoreApplication.translate("DConfigurePoseTracking", u"Pose Tracking Model:", None))
    # retranslateUi

