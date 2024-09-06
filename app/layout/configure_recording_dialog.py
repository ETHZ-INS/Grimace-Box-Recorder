# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'DConfigureRecording.ui'
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
    QDialogButtonBox, QFormLayout, QFrame, QLabel,
    QLayout, QSizePolicy, QTimeEdit, QVBoxLayout,
    QWidget)

class Ui_DConfigureRecording(object):
    def setupUi(self, DConfigureRecording):
        if not DConfigureRecording.objectName():
            DConfigureRecording.setObjectName(u"DConfigureRecording")
        DConfigureRecording.resize(400, 200)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DConfigureRecording.sizePolicy().hasHeightForWidth())
        DConfigureRecording.setSizePolicy(sizePolicy)
        DConfigureRecording.setMinimumSize(QSize(400, 200))
        DConfigureRecording.setMaximumSize(QSize(400, 200))
        DConfigureRecording.setModal(False)
        self.verticalLayout = QVBoxLayout(DConfigureRecording)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SetMinAndMaxSize)
        self.frame = QFrame(DConfigureRecording)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.formLayout = QFormLayout(self.frame)
        self.formLayout.setObjectName(u"formLayout")
        self.label_2 = QLabel(self.frame)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_2)

        self.dpd_recording_mode = QComboBox(self.frame)
        self.dpd_recording_mode.addItem("")
        self.dpd_recording_mode.addItem("")
        self.dpd_recording_mode.setObjectName(u"dpd_recording_mode")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.dpd_recording_mode)

        self.label_3 = QLabel(self.frame)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_3)

        self.tme_time = QTimeEdit(self.frame)
        self.tme_time.setObjectName(u"tme_time")
        self.tme_time.setInputMethodHints(Qt.ImhPreferNumbers|Qt.ImhTime)
        self.tme_time.setTimeSpec(Qt.LocalTime)
        self.tme_time.setTime(QTime(0, 10, 0))

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.tme_time)

        self.label_4 = QLabel(self.frame)
        self.label_4.setObjectName(u"label_4")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_4)

        self.dpd_codec = QComboBox(self.frame)
        self.dpd_codec.addItem("")
        self.dpd_codec.addItem("")
        self.dpd_codec.addItem("")
        self.dpd_codec.setObjectName(u"dpd_codec")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.dpd_codec)


        self.verticalLayout.addWidget(self.frame)

        self.btnbox_buttons = QDialogButtonBox(DConfigureRecording)
        self.btnbox_buttons.setObjectName(u"btnbox_buttons")
        self.btnbox_buttons.setOrientation(Qt.Horizontal)
        self.btnbox_buttons.setStandardButtons(QDialogButtonBox.Apply|QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.btnbox_buttons)


        self.retranslateUi(DConfigureRecording)
        self.btnbox_buttons.accepted.connect(DConfigureRecording.accept)
        self.btnbox_buttons.rejected.connect(DConfigureRecording.reject)

        QMetaObject.connectSlotsByName(DConfigureRecording)
    # setupUi

    def retranslateUi(self, DConfigureRecording):
        DConfigureRecording.setWindowTitle(QCoreApplication.translate("DConfigureRecording", u"Configure Recording", None))
        self.label_2.setText(QCoreApplication.translate("DConfigureRecording", u"Recording Mode:", None))
        self.dpd_recording_mode.setItemText(0, QCoreApplication.translate("DConfigureRecording", u"Timed", None))
        self.dpd_recording_mode.setItemText(1, QCoreApplication.translate("DConfigureRecording", u"Manual", None))

        self.label_3.setText(QCoreApplication.translate("DConfigureRecording", u"Duration:", None))
        self.tme_time.setDisplayFormat(QCoreApplication.translate("DConfigureRecording", u"HH'h' mm'm' ss.zzz's'", None))
        self.label_4.setText(QCoreApplication.translate("DConfigureRecording", u"Video Codec:", None))
        self.dpd_codec.setItemText(0, QCoreApplication.translate("DConfigureRecording", u"FMP4", None))
        self.dpd_codec.setItemText(1, QCoreApplication.translate("DConfigureRecording", u"MP4V", None))
        self.dpd_codec.setItemText(2, QCoreApplication.translate("DConfigureRecording", u"FFV1", None))

#if QT_CONFIG(tooltip)
        self.dpd_codec.setToolTip(QCoreApplication.translate("DConfigureRecording", u"Select which video codec should be used to encode the recorded videos", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

