# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'WGrimaceBox.ui'
##
## Created by: Qt User Interface Compiler version 6.7.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QLayout, QMainWindow, QMenu, QMenuBar,
    QPushButton, QSizePolicy, QSpacerItem, QStatusBar,
    QVBoxLayout, QWidget)

class Ui_WGrimaceBox(object):
    def setupUi(self, WGrimaceBox):
        if not WGrimaceBox.objectName():
            WGrimaceBox.setObjectName(u"WGrimaceBox")
        WGrimaceBox.resize(1235, 843)
        self.action_save_project = QAction(WGrimaceBox)
        self.action_save_project.setObjectName(u"action_save_project")
        self.action_load_project = QAction(WGrimaceBox)
        self.action_load_project.setObjectName(u"action_load_project")
        self.actionConfigure_Video_Files = QAction(WGrimaceBox)
        self.actionConfigure_Video_Files.setObjectName(u"actionConfigure_Video_Files")
        self.action_configure_recording = QAction(WGrimaceBox)
        self.action_configure_recording.setObjectName(u"action_configure_recording")
        self.action_configure_video_files = QAction(WGrimaceBox)
        self.action_configure_video_files.setObjectName(u"action_configure_video_files")
        self.action_configure_top_camera = QAction(WGrimaceBox)
        self.action_configure_top_camera.setObjectName(u"action_configure_top_camera")
        self.action_configure_front_camera = QAction(WGrimaceBox)
        self.action_configure_front_camera.setObjectName(u"action_configure_front_camera")
        self.action_save_project_as = QAction(WGrimaceBox)
        self.action_save_project_as.setObjectName(u"action_save_project_as")
        self.actionConfigure_Frame_Extraction = QAction(WGrimaceBox)
        self.actionConfigure_Frame_Extraction.setObjectName(u"actionConfigure_Frame_Extraction")
        self.action_configure_grimace_scoring = QAction(WGrimaceBox)
        self.action_configure_grimace_scoring.setObjectName(u"action_configure_grimace_scoring")
        self.actionReport_Bug = QAction(WGrimaceBox)
        self.actionReport_Bug.setObjectName(u"actionReport_Bug")
        self.actionContact_Authors = QAction(WGrimaceBox)
        self.actionContact_Authors.setObjectName(u"actionContact_Authors")
        self.action_open_grimace_results_window = QAction(WGrimaceBox)
        self.action_open_grimace_results_window.setObjectName(u"action_open_grimace_results_window")
        self.centralwidget = QWidget(WGrimaceBox)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frame_2 = QFrame(self.centralwidget)
        self.frame_2.setObjectName(u"frame_2")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_2.sizePolicy().hasHeightForWidth())
        self.frame_2.setSizePolicy(sizePolicy)
        self.frame_2.setMinimumSize(QSize(0, 0))
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_3 = QHBoxLayout(self.frame_2)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setSizeConstraint(QLayout.SetMinimumSize)
        self.lbl_video_top = QLabel(self.frame_2)
        self.lbl_video_top.setObjectName(u"lbl_video_top")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.lbl_video_top.sizePolicy().hasHeightForWidth())
        self.lbl_video_top.setSizePolicy(sizePolicy1)
        self.lbl_video_top.setMinimumSize(QSize(375, 300))
        self.lbl_video_top.setMaximumSize(QSize(750, 600))
        self.lbl_video_top.setStyleSheet(u"border: 2px solid black;")
        self.lbl_video_top.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_3.addWidget(self.lbl_video_top)

        self.lbl_video_front = QLabel(self.frame_2)
        self.lbl_video_front.setObjectName(u"lbl_video_front")
        sizePolicy1.setHeightForWidth(self.lbl_video_front.sizePolicy().hasHeightForWidth())
        self.lbl_video_front.setSizePolicy(sizePolicy1)
        self.lbl_video_front.setMinimumSize(QSize(375, 300))
        self.lbl_video_front.setMaximumSize(QSize(750, 600))
        self.lbl_video_front.setStyleSheet(u"border: 2px solid black;")
        self.lbl_video_front.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_3.addWidget(self.lbl_video_front)

        self.horizontalLayout_3.setStretch(0, 1)
        self.horizontalLayout_3.setStretch(1, 1)

        self.verticalLayout.addWidget(self.frame_2)

        self.lbl_overview = QLabel(self.centralwidget)
        self.lbl_overview.setObjectName(u"lbl_overview")
        self.lbl_overview.setTextFormat(Qt.MarkdownText)
        self.lbl_overview.setWordWrap(False)

        self.verticalLayout.addWidget(self.lbl_overview)

        self.verticalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.frame = QFrame(self.centralwidget)
        self.frame.setObjectName(u"frame")
        sizePolicy1.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy1)
        self.frame.setMinimumSize(QSize(0, 60))
        self.frame.setMaximumSize(QSize(16777215, 60))
        self.frame.setStyleSheet(u"")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.btn_record = QPushButton(self.frame)
        self.btn_record.setObjectName(u"btn_record")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.MinimumExpanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.btn_record.sizePolicy().hasHeightForWidth())
        self.btn_record.setSizePolicy(sizePolicy2)
        self.btn_record.setMinimumSize(QSize(0, 0))

        self.horizontalLayout_2.addWidget(self.btn_record)

        self.lbl_message = QLabel(self.frame)
        self.lbl_message.setObjectName(u"lbl_message")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.lbl_message.sizePolicy().hasHeightForWidth())
        self.lbl_message.setSizePolicy(sizePolicy3)
        self.lbl_message.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_2.addWidget(self.lbl_message)

        self.lbl_time = QLabel(self.frame)
        self.lbl_time.setObjectName(u"lbl_time")
        sizePolicy2.setHeightForWidth(self.lbl_time.sizePolicy().hasHeightForWidth())
        self.lbl_time.setSizePolicy(sizePolicy2)
        self.lbl_time.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_2.addWidget(self.lbl_time)


        self.verticalLayout.addWidget(self.frame)

        WGrimaceBox.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(WGrimaceBox)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1235, 21))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuCamera = QMenu(self.menubar)
        self.menuCamera.setObjectName(u"menuCamera")
        self.menu_configure_cameras = QMenu(self.menuCamera)
        self.menu_configure_cameras.setObjectName(u"menu_configure_cameras")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        self.menuAnalysis = QMenu(self.menubar)
        self.menuAnalysis.setObjectName(u"menuAnalysis")
        WGrimaceBox.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(WGrimaceBox)
        self.statusbar.setObjectName(u"statusbar")
        WGrimaceBox.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuCamera.menuAction())
        self.menubar.addAction(self.menuAnalysis.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuFile.addAction(self.action_save_project)
        self.menuFile.addAction(self.action_save_project_as)
        self.menuFile.addAction(self.action_load_project)
        self.menuCamera.addAction(self.menu_configure_cameras.menuAction())
        self.menuCamera.addAction(self.action_configure_recording)
        self.menuCamera.addAction(self.action_configure_video_files)
        self.menu_configure_cameras.addAction(self.action_configure_top_camera)
        self.menu_configure_cameras.addAction(self.action_configure_front_camera)
        self.menuHelp.addAction(self.actionReport_Bug)
        self.menuHelp.addAction(self.actionContact_Authors)
        self.menuAnalysis.addAction(self.action_configure_grimace_scoring)
        self.menuAnalysis.addAction(self.action_open_grimace_results_window)

        self.retranslateUi(WGrimaceBox)

        QMetaObject.connectSlotsByName(WGrimaceBox)
    # setupUi

    def retranslateUi(self, WGrimaceBox):
        WGrimaceBox.setWindowTitle(QCoreApplication.translate("WGrimaceBox", u"Grimace Box", None))
        self.action_save_project.setText(QCoreApplication.translate("WGrimaceBox", u"Save Project", None))
        self.action_load_project.setText(QCoreApplication.translate("WGrimaceBox", u"Load Project", None))
        self.actionConfigure_Video_Files.setText(QCoreApplication.translate("WGrimaceBox", u"Configure Video Files", None))
        self.action_configure_recording.setText(QCoreApplication.translate("WGrimaceBox", u"Configure Recording", None))
        self.action_configure_video_files.setText(QCoreApplication.translate("WGrimaceBox", u"Configure Video Files", None))
        self.action_configure_top_camera.setText(QCoreApplication.translate("WGrimaceBox", u"Top Camera", None))
        self.action_configure_front_camera.setText(QCoreApplication.translate("WGrimaceBox", u"Front Camera", None))
        self.action_save_project_as.setText(QCoreApplication.translate("WGrimaceBox", u"Save Project As...", None))
        self.actionConfigure_Frame_Extraction.setText(QCoreApplication.translate("WGrimaceBox", u"Configure Frame Extraction", None))
        self.action_configure_grimace_scoring.setText(QCoreApplication.translate("WGrimaceBox", u"Configure Grimace Scoring", None))
        self.actionReport_Bug.setText(QCoreApplication.translate("WGrimaceBox", u"Report Bug", None))
        self.actionContact_Authors.setText(QCoreApplication.translate("WGrimaceBox", u"Contact Support", None))
        self.action_open_grimace_results_window.setText(QCoreApplication.translate("WGrimaceBox", u"Open Grimace Results Window", None))
        self.lbl_video_top.setText(QCoreApplication.translate("WGrimaceBox", u"Top camera not configured", None))
        self.lbl_video_front.setText(QCoreApplication.translate("WGrimaceBox", u"Front camera not configured", None))
        self.lbl_overview.setText(QCoreApplication.translate("WGrimaceBox", u"### Overview for next recording:  \n"
"Recording Number: 1  \n"
"Recording Duration: 00:10:00.000  \n"
"Top Camera Frame Rate: 30.0 FPS  \n"
"Front Camera Frame Rate: 30.0 FPS  \n"
"Top Video Filename: top_1.avi  \n"
"Front Video Filename: front_1.avi  \n"
"", None))
        self.btn_record.setText(QCoreApplication.translate("WGrimaceBox", u"Start Recording", None))
        self.lbl_message.setText(QCoreApplication.translate("WGrimaceBox", u"Ready to record", None))
        self.lbl_time.setText(QCoreApplication.translate("WGrimaceBox", u"00:00:00", None))
        self.menuFile.setTitle(QCoreApplication.translate("WGrimaceBox", u"File", None))
        self.menuCamera.setTitle(QCoreApplication.translate("WGrimaceBox", u"Recording", None))
        self.menu_configure_cameras.setTitle(QCoreApplication.translate("WGrimaceBox", u"Configure Cameras", None))
        self.menuHelp.setTitle(QCoreApplication.translate("WGrimaceBox", u"Help", None))
        self.menuAnalysis.setTitle(QCoreApplication.translate("WGrimaceBox", u"Analysis", None))
    # retranslateUi

