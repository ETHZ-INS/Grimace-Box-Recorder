from copy import deepcopy
from dataclasses import replace

from PySide6.QtWidgets import QDialog, QDialogButtonBox

import logging

from app.layout.configure_pose_tracking_dialog import Ui_DConfigurePoseTracking
from app.model.devices import Devices
from app.model.grimace_recorder_model import GrimaceRecorderModel
from util.trace import Trace

logger = logging.getLogger("grimace_box."+__name__)


class ConfigurePoseEstimation(Ui_DConfigurePoseTracking, QDialog):
    @Trace.trace(logger)
    def __init__(self, parent, model: GrimaceRecorderModel):
        super().__init__(parent)
        self.setupUi(self)

        self.model = model
        self.temp_config = deepcopy(model.recording.pose_config)

        debug_mode = model.debug_mode

        pose_models = self.temp_config.POSE_TOP_MODELS
        if not debug_mode:
            pose_models = [model for model in pose_models if model != "Demo (Fake Mouse)"]
        self.dpd_pose_model.clear()
        self.dpd_pose_model.addItems(pose_models)
        if self.temp_config.pose_model is not None:
            self.dpd_pose_model.setCurrentText(self.temp_config.pose_model)
        else:
            self.dpd_pose_model.setCurrentIndex(-1)

        available_devices = Devices.get_computation_devices()

        self.dpd_pose_tracking_device.clear()
        for device in available_devices:
            self.dpd_pose_tracking_device.addItem(device[1], device[0])
        current_index = self.dpd_pose_tracking_device.findData(self.temp_config.pose_device)
        self.dpd_pose_tracking_device.setCurrentIndex(current_index)

        if not self.model.debug_mode:
            self.dpd_pose_tracking_device.setEnabled(False)

        self.chb_show_pose_preview.setChecked(self.temp_config.show_preview)

        self.chb_show_pose_preview.stateChanged.connect(self.show_pose_preview_changed)

        self.dpd_pose_model.currentIndexChanged.connect(self.pose_model_changed)

        self.dpd_pose_tracking_device.currentIndexChanged.connect(self.pose_tracking_device_changed)

        self.btn_apply = self.btnbox_buttons.button(QDialogButtonBox.StandardButton.Apply)
        self.btn_apply.clicked.connect(self.apply)

    @Trace.trace(logger)
    def show_pose_preview_changed(self, *_):
        show_preview = self.chb_show_pose_preview.isChecked()
        self.temp_config.show_preview = show_preview
        logger.info("Pose Preview Enabled: %s", show_preview)

    @Trace.trace(logger)
    def pose_model_changed(self, *_):
        pose_model = self.dpd_pose_model.currentText()
        self.temp_config.pose_model = pose_model
        logger.info("Pose Tracking Enabled: %s", pose_model)

    @Trace.trace(logger)
    def pose_tracking_device_changed(self, *_):
        pose_tracking_device = self.dpd_pose_tracking_device.currentData()
        self.temp_config.pose_device = pose_tracking_device
        logger.info("Pose Tracking Device Selected: %s", pose_tracking_device)

    @Trace.trace(logger)
    def apply(self):
        self.model.recording.set_pose_config(self.temp_config)

    @Trace.trace(logger)
    def accept(self):
        if self.temp_config != self.model.recording.pose_config:
            self.apply()
        super().accept()
