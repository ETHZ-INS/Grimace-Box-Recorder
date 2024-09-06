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
    QLabel, QLayout, QScrollArea, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_GGrimaceResults(object):
    def setupUi(self, GGrimaceResults):
        if not GGrimaceResults.objectName():
            GGrimaceResults.setObjectName(u"GGrimaceResults")
        GGrimaceResults.resize(439, 355)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(GGrimaceResults.sizePolicy().hasHeightForWidth())
        GGrimaceResults.setSizePolicy(sizePolicy)
        GGrimaceResults.setMinimumSize(QSize(430, 0))
        GGrimaceResults.setMaximumSize(QSize(600, 16777215))
        GGrimaceResults.setWindowOpacity(1.000000000000000)
        self.horizontalLayout = QHBoxLayout(GGrimaceResults)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.frm_grimace_stats = QFrame(GGrimaceResults)
        self.frm_grimace_stats.setObjectName(u"frm_grimace_stats")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.frm_grimace_stats.sizePolicy().hasHeightForWidth())
        self.frm_grimace_stats.setSizePolicy(sizePolicy1)
        self.frm_grimace_stats.setMinimumSize(QSize(200, 0))
        self.frm_grimace_stats.setMaximumSize(QSize(200, 16777215))
        self.frm_grimace_stats.setFrameShape(QFrame.StyledPanel)
        self.frm_grimace_stats.setFrameShadow(QFrame.Raised)
        self.verticalLayout = QVBoxLayout(self.frm_grimace_stats)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(8, 9, 9, 9)
        self.lbl_grimace_legend = QLabel(self.frm_grimace_stats)
        self.lbl_grimace_legend.setObjectName(u"lbl_grimace_legend")
        self.lbl_grimace_legend.setMaximumSize(QSize(16777215, 191))
        self.lbl_grimace_legend.setScaledContents(True)

        self.verticalLayout.addWidget(self.lbl_grimace_legend)

        self.lbl_grimace_stats = QLabel(self.frm_grimace_stats)
        self.lbl_grimace_stats.setObjectName(u"lbl_grimace_stats")
        self.lbl_grimace_stats.setStyleSheet(u"")
        self.lbl_grimace_stats.setTextFormat(Qt.MarkdownText)

        self.verticalLayout.addWidget(self.lbl_grimace_stats)

        self.frm_gauge_plot = QFrame(self.frm_grimace_stats)
        self.frm_gauge_plot.setObjectName(u"frm_gauge_plot")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.frm_gauge_plot.sizePolicy().hasHeightForWidth())
        self.frm_gauge_plot.setSizePolicy(sizePolicy2)
        self.frm_gauge_plot.setMinimumSize(QSize(0, 40))
        self.frm_gauge_plot.setMaximumSize(QSize(16777215, 40))
        self.frm_gauge_plot.setFrameShape(QFrame.NoFrame)
        self.frm_gauge_plot.setFrameShadow(QFrame.Plain)
        self.verticalLayout_4 = QVBoxLayout(self.frm_gauge_plot)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout.addWidget(self.frm_gauge_plot)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)


        self.horizontalLayout.addWidget(self.frm_grimace_stats)

        self.horizontalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.scrollArea = QScrollArea(GGrimaceResults)
        self.scrollArea.setObjectName(u"scrollArea")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Expanding)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy3)
        self.scrollArea.setMinimumSize(QSize(0, 0))
        self.scrollArea.setMaximumSize(QSize(16777215, 16777215))
        self.scrollArea.setStyleSheet(u"")
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 188, 335))
        sizePolicy.setHeightForWidth(self.scrollAreaWidgetContents.sizePolicy().hasHeightForWidth())
        self.scrollAreaWidgetContents.setSizePolicy(sizePolicy)
        self.scrollAreaWidgetContents.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout_2 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.frm_grimace_images = QFrame(self.scrollAreaWidgetContents)
        self.frm_grimace_images.setObjectName(u"frm_grimace_images")
        self.frm_grimace_images.setFrameShape(QFrame.StyledPanel)
        self.frm_grimace_images.setFrameShadow(QFrame.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.frm_grimace_images)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.label_2 = QLabel(self.frm_grimace_images)
        self.label_2.setObjectName(u"label_2")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy4)
        self.label_2.setMinimumSize(QSize(150, 150))
        self.label_2.setMaximumSize(QSize(150, 150))
        self.label_2.setStyleSheet(u"background-color: red")

        self.verticalLayout_3.addWidget(self.label_2)

        self.label_3 = QLabel(self.frm_grimace_images)
        self.label_3.setObjectName(u"label_3")
        sizePolicy4.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy4)
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
        self.lbl_grimace_legend.setText("")
        self.lbl_grimace_stats.setText(QCoreApplication.translate("GGrimaceResults", u"Frames Sampled: 10  \n"
"Mean Grimace Score: 0.5", None))
        self.label_2.setText(QCoreApplication.translate("GGrimaceResults", u"TextLabel", None))
        self.label_3.setText(QCoreApplication.translate("GGrimaceResults", u"TextLabel", None))
    # retranslateUi

