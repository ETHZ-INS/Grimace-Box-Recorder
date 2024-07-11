# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'GGrimaceResults.ui'
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
from PySide6.QtWidgets import (QAbstractScrollArea, QApplication, QFrame, QHBoxLayout,
    QLabel, QScrollArea, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_GGrimaceResults(object):
    def setupUi(self, GGrimaceResults):
        if not GGrimaceResults.objectName():
            GGrimaceResults.setObjectName(u"GGrimaceResults")
        GGrimaceResults.resize(412, 324)
        GGrimaceResults.setWindowOpacity(1.000000000000000)
        self.horizontalLayout = QHBoxLayout(GGrimaceResults)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.frm_grimace_stats = QFrame(GGrimaceResults)
        self.frm_grimace_stats.setObjectName(u"frm_grimace_stats")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frm_grimace_stats.sizePolicy().hasHeightForWidth())
        self.frm_grimace_stats.setSizePolicy(sizePolicy)
        self.frm_grimace_stats.setFrameShape(QFrame.StyledPanel)
        self.frm_grimace_stats.setFrameShadow(QFrame.Raised)
        self.verticalLayout = QVBoxLayout(self.frm_grimace_stats)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.lbl_grimace_stats = QLabel(self.frm_grimace_stats)
        self.lbl_grimace_stats.setObjectName(u"lbl_grimace_stats")
        self.lbl_grimace_stats.setTextFormat(Qt.MarkdownText)

        self.verticalLayout.addWidget(self.lbl_grimace_stats)


        self.horizontalLayout.addWidget(self.frm_grimace_stats)

        self.scrollArea = QScrollArea(GGrimaceResults)
        self.scrollArea.setObjectName(u"scrollArea")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy1)
        self.scrollArea.setMinimumSize(QSize(150, 0))
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, -40, 219, 350))
        self.verticalLayout_2 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.frm_grimace_images = QFrame(self.scrollAreaWidgetContents)
        self.frm_grimace_images.setObjectName(u"frm_grimace_images")
        self.frm_grimace_images.setFrameShape(QFrame.StyledPanel)
        self.frm_grimace_images.setFrameShadow(QFrame.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.frm_grimace_images)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label_2 = QLabel(self.frm_grimace_images)
        self.label_2.setObjectName(u"label_2")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy2)
        self.label_2.setMinimumSize(QSize(150, 150))
        self.label_2.setMaximumSize(QSize(150, 150))
        self.label_2.setStyleSheet(u"background-color: red")

        self.verticalLayout_3.addWidget(self.label_2)

        self.label_3 = QLabel(self.frm_grimace_images)
        self.label_3.setObjectName(u"label_3")
        sizePolicy2.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy2)
        self.label_3.setMinimumSize(QSize(150, 150))
        self.label_3.setMaximumSize(QSize(150, 150))
        self.label_3.setStyleSheet(u"background-color: red")

        self.verticalLayout_3.addWidget(self.label_3)


        self.verticalLayout_2.addWidget(self.frm_grimace_images)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.horizontalLayout.addWidget(self.scrollArea)


        self.retranslateUi(GGrimaceResults)

        QMetaObject.connectSlotsByName(GGrimaceResults)
    # setupUi

    def retranslateUi(self, GGrimaceResults):
        GGrimaceResults.setWindowTitle(QCoreApplication.translate("GGrimaceResults", u"Grimace Analysis Results", None))
        self.lbl_grimace_stats.setText(QCoreApplication.translate("GGrimaceResults", u"Frames Sampled: 10  \n"
"Mean Grimace Score: 0.5", None))
        self.label_2.setText(QCoreApplication.translate("GGrimaceResults", u"TextLabel", None))
        self.label_3.setText(QCoreApplication.translate("GGrimaceResults", u"TextLabel", None))
    # retranslateUi

