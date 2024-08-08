# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'DConfigureGrimaceScoring.ui'
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
    QLabel, QSizePolicy, QVBoxLayout, QWidget)

class Ui_DConfigureGrimaceScoring(object):
    def setupUi(self, DConfigureGrimaceScoring):
        if not DConfigureGrimaceScoring.objectName():
            DConfigureGrimaceScoring.setObjectName(u"DConfigureGrimaceScoring")
        DConfigureGrimaceScoring.resize(400, 300)
        DConfigureGrimaceScoring.setMinimumSize(QSize(400, 300))
        DConfigureGrimaceScoring.setMaximumSize(QSize(400, 300))
        self.verticalLayout = QVBoxLayout(DConfigureGrimaceScoring)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(DConfigureGrimaceScoring)
        self.label.setObjectName(u"label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)

        self.verticalLayout.addWidget(self.label)

        self.frame = QFrame(DConfigureGrimaceScoring)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.formLayout = QFormLayout(self.frame)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setFormAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.label_7 = QLabel(self.frame)
        self.label_7.setObjectName(u"label_7")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_7)

        self.chb_enable_grimace = QCheckBox(self.frame)
        self.chb_enable_grimace.setObjectName(u"chb_enable_grimace")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.chb_enable_grimace)

        self.label_2 = QLabel(self.frame)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.dpd_grimace_model = QComboBox(self.frame)
        self.dpd_grimace_model.addItem("")
        self.dpd_grimace_model.setObjectName(u"dpd_grimace_model")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.dpd_grimace_model)

        self.label_3 = QLabel(self.frame)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_3)

        self.dpd_frame_interval = QComboBox(self.frame)
        self.dpd_frame_interval.addItem("")
        self.dpd_frame_interval.addItem("")
        self.dpd_frame_interval.addItem("")
        self.dpd_frame_interval.addItem("")
        self.dpd_frame_interval.addItem("")
        self.dpd_frame_interval.addItem("")
        self.dpd_frame_interval.setObjectName(u"dpd_frame_interval")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.dpd_frame_interval)

        self.label_4 = QLabel(self.frame)
        self.label_4.setObjectName(u"label_4")

        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.label_4)

        self.dpd_frame_quality_device = QComboBox(self.frame)
        self.dpd_frame_quality_device.setObjectName(u"dpd_frame_quality_device")

        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.dpd_frame_quality_device)

        self.label_6 = QLabel(self.frame)
        self.label_6.setObjectName(u"label_6")

        self.formLayout.setWidget(6, QFormLayout.LabelRole, self.label_6)

        self.label_8 = QLabel(self.frame)
        self.label_8.setObjectName(u"label_8")

        self.formLayout.setWidget(7, QFormLayout.LabelRole, self.label_8)

        self.dpd_face_cropper_device = QComboBox(self.frame)
        self.dpd_face_cropper_device.setObjectName(u"dpd_face_cropper_device")

        self.formLayout.setWidget(6, QFormLayout.FieldRole, self.dpd_face_cropper_device)

        self.dpd_grimace_scoring_device = QComboBox(self.frame)
        self.dpd_grimace_scoring_device.setObjectName(u"dpd_grimace_scoring_device")

        self.formLayout.setWidget(7, QFormLayout.FieldRole, self.dpd_grimace_scoring_device)

        self.label_5 = QLabel(self.frame)
        self.label_5.setObjectName(u"label_5")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label_5)


        self.verticalLayout.addWidget(self.frame)

        self.btnbox_buttons = QDialogButtonBox(DConfigureGrimaceScoring)
        self.btnbox_buttons.setObjectName(u"btnbox_buttons")
        self.btnbox_buttons.setOrientation(Qt.Horizontal)
        self.btnbox_buttons.setStandardButtons(QDialogButtonBox.Apply|QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.btnbox_buttons)


        self.retranslateUi(DConfigureGrimaceScoring)
        self.btnbox_buttons.accepted.connect(DConfigureGrimaceScoring.accept)
        self.btnbox_buttons.rejected.connect(DConfigureGrimaceScoring.reject)

        QMetaObject.connectSlotsByName(DConfigureGrimaceScoring)
    # setupUi

    def retranslateUi(self, DConfigureGrimaceScoring):
        DConfigureGrimaceScoring.setWindowTitle(QCoreApplication.translate("DConfigureGrimaceScoring", u"Configure Grimace Scoring", None))
        self.label.setText(QCoreApplication.translate("DConfigureGrimaceScoring", u"Configure Grimace Scoring", None))
        self.label_7.setText(QCoreApplication.translate("DConfigureGrimaceScoring", u"Enable Grimace Scoring:", None))
        self.chb_enable_grimace.setText("")
        self.label_2.setText(QCoreApplication.translate("DConfigureGrimaceScoring", u"Grimace Model:", None))
        self.dpd_grimace_model.setItemText(0, QCoreApplication.translate("DConfigureGrimaceScoring", u"V1 - SuperScorer", None))

        self.label_3.setText(QCoreApplication.translate("DConfigureGrimaceScoring", u"Frame Interval:", None))
        self.dpd_frame_interval.setItemText(0, QCoreApplication.translate("DConfigureGrimaceScoring", u"10 Seconds", None))
        self.dpd_frame_interval.setItemText(1, QCoreApplication.translate("DConfigureGrimaceScoring", u"20 Seconds", None))
        self.dpd_frame_interval.setItemText(2, QCoreApplication.translate("DConfigureGrimaceScoring", u"30 Seconds", None))
        self.dpd_frame_interval.setItemText(3, QCoreApplication.translate("DConfigureGrimaceScoring", u"1 Minute", None))
        self.dpd_frame_interval.setItemText(4, QCoreApplication.translate("DConfigureGrimaceScoring", u"2 Minutes", None))
        self.dpd_frame_interval.setItemText(5, QCoreApplication.translate("DConfigureGrimaceScoring", u"5 Minutes", None))

        self.label_4.setText(QCoreApplication.translate("DConfigureGrimaceScoring", u"Frame Quality Model:", None))
#if QT_CONFIG(tooltip)
        self.dpd_frame_quality_device.setToolTip(QCoreApplication.translate("DConfigureGrimaceScoring", u"Select which device should be used to run the frame quality model", None))
#endif // QT_CONFIG(tooltip)
        self.label_6.setText(QCoreApplication.translate("DConfigureGrimaceScoring", u"Face Cropper Model:", None))
        self.label_8.setText(QCoreApplication.translate("DConfigureGrimaceScoring", u"Grimace Scoring Model:", None))
#if QT_CONFIG(tooltip)
        self.dpd_face_cropper_device.setToolTip(QCoreApplication.translate("DConfigureGrimaceScoring", u"Select which device should be used to run the frame cropper model", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.dpd_grimace_scoring_device.setToolTip(QCoreApplication.translate("DConfigureGrimaceScoring", u"Select which device should be used to run the grimace scoring model", None))
#endif // QT_CONFIG(tooltip)
        self.label_5.setText(QCoreApplication.translate("DConfigureGrimaceScoring", u"Device Selection:", None))
    # retranslateUi

