from dataclasses import replace
from typing import List, Tuple

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QDialogButtonBox

from app.config.pose_top import PoseTopConfig

import logging

from app.layout.configure_pose_tracking_dialog import Ui_DConfigurePoseTracking
from util.trace import Trace

logger = logging.getLogger("grimace_recorder.app.analysis.configure_pose_tracking_dialog")


class ConfigurePoseTracking(Ui_DConfigurePoseTracking, QDialog):
    applied_signal = Signal(PoseTopConfig)

    @Trace.trace(logger)
    def __init__(self, parent, pose_top_config: PoseTopConfig, available_devices: List[Tuple[str, str]], debug_mode: bool = False):
        super().__init__(parent)
        self.setupUi(self)

        self.pose_top_config = replace(pose_top_config)
        self.last_pose_top_config = replace(pose_top_config)

        self.chb_enable_pose.setChecked(pose_top_config.enabled)

        pose_models = pose_top_config.POSE_TOP_MODELS
        if not debug_mode:
            pose_models = [model for model in pose_models if model != "Demo (Fake Mouse)"]
        self.dpd_pose_model.clear()
        self.dpd_pose_model.addItems(pose_models)
        if pose_top_config.pose_model is not None:
            self.dpd_pose_model.setCurrentText(pose_top_config.pose_model)
        else:
            self.dpd_pose_model.setCurrentIndex(-1)

        self.dpd_pose_tracking_device.clear()
        for device in available_devices:
            self.dpd_pose_tracking_device.addItem(device[1], device[0])
        current_index = self.dpd_pose_tracking_device.findData(pose_top_config.pose_device)
        self.dpd_pose_tracking_device.setCurrentIndex(current_index)

        self.chb_show_pose_preview.setChecked(pose_top_config.show_preview)

        self.chb_enable_pose.stateChanged.connect(self.enable_pose_changed)
        self.chb_show_pose_preview.stateChanged.connect(self.show_pose_preview_changed)

        self.dpd_pose_model.currentIndexChanged.connect(self.pose_model_changed)

        self.dpd_pose_tracking_device.currentIndexChanged.connect(self.pose_tracking_device_changed)

        self.btn_apply = self.btnbox_buttons.button(QDialogButtonBox.StandardButton.Apply)
        self.btn_apply.clicked.connect(self.apply)

        self.enable_pose_changed()

    @Trace.trace(logger)
    def enable_pose_changed(self, *_):
        pose_enabled = self.chb_enable_pose.isChecked()
        self.pose_top_config.enabled = pose_enabled
        logger.info("Pose Tracking Enabled: %s", pose_enabled)

        self.dpd_pose_model.setEnabled(self.pose_top_config.enabled)
        self.chb_show_pose_preview.setEnabled(self.pose_top_config.enabled)

    @Trace.trace(logger)
    def show_pose_preview_changed(self, *_):
        show_preview = self.chb_show_pose_preview.isChecked()
        self.pose_top_config.show_preview = show_preview
        logger.info("Pose Preview Enabled: %s", show_preview)

    @Trace.trace(logger)
    def pose_model_changed(self, *_):
        pose_model = self.dpd_pose_model.currentText()
        self.pose_top_config.pose_model = pose_model
        logger.info("Pose Tracking Enabled: %s", pose_model)

    @Trace.trace(logger)
    def pose_tracking_device_changed(self, *_):
        pose_tracking_device = self.dpd_pose_tracking_device.currentData()
        self.pose_top_config.pose_device = pose_tracking_device
        logger.info("Pose Tracking Device Selected: %s", pose_tracking_device)

    @Trace.trace(logger)
    def apply(self):
        self.last_pose_top_config = replace(self.pose_top_config)
        self.applied_signal.emit(self.pose_top_config)

    @Trace.trace(logger)
    def accept(self):
        if self.pose_top_config != self.last_pose_top_config:
            self.apply()
        super().accept()
