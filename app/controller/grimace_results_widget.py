import cv2
import numpy as np
from PySide6 import QtCore
from PySide6.QtCore import Signal, QRect
from PySide6.QtGui import QImage, QPixmap, QPainter, Qt, QColor, QPainterPath, QFont
from PySide6.QtWidgets import QDialog, QLabel, QSizePolicy

from app.config.video_files import VideoFilesConfig
from app.layout.grimace_results_widget import Ui_GGrimaceResults
from app.dataflow.qlist import QList


class HorizontalGaugePlot(QLabel):
    def __init__(self, parent):
        super().__init__(parent)

        self.color_green = QColor('#a5d46a')
        self.color_yellow = QColor('#ffdf80')
        self.color_red = QColor('#ffa080')

        self.needle_color = QColor('#000000')
        self.needle_width = 12
        self.needle_height = 10

        self.text_color = QColor('#000000')
        self.text_height = 10
        self.text_width = 30
        self.text_font = QFont('Arial', self.text_height)

        self.min_score = 0
        self.max_score = 2
        self.score = 1.5

    def paintEvent(self, event):
        needle_offset = self.text_height + 2

        gauge_offset_y = int(self.needle_height/2) + self.text_height
        gauge_offset_x = int(self.text_width/2)

        gauge_width = self.width() - self.text_width
        gauge_height = self.height() - gauge_offset_y

        # fill colored segments
        x1 = gauge_offset_x
        x2 = gauge_offset_x + int(gauge_width / 3)
        x3 = gauge_offset_x + int(gauge_width * 2 / 3)
        x4 = gauge_offset_x + gauge_width

        qp = QPainter(self)
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(self.color_green)
        qp.drawRect(x1, gauge_offset_y, x2, gauge_height)
        qp.setBrush(self.color_yellow)
        qp.drawRect(x2, gauge_offset_y, x3 - x2, gauge_height)
        qp.setBrush(self.color_red)
        qp.drawRect(x3, gauge_offset_y, x4 - x3, gauge_height)

        # draw needle
        score_percentage = (self.score - self.min_score) / (self.max_score - self.min_score)
        score_x = int(x1 + score_percentage * (x4 - x1))

        path = QPainterPath()
        path.moveTo(score_x, needle_offset + self.needle_height)
        path.lineTo(int(score_x - self.needle_width/2), needle_offset)
        path.lineTo(int(score_x + self.needle_width/2), needle_offset)
        path.lineTo(score_x, needle_offset + self.needle_height)

        qp.fillPath(path, self.needle_color)

        # draw text on top of needle
        text_x = int(score_x - self.text_width/2)
        text_y = 0
        qp.setPen(self.text_color)
        qp.setFont(self.text_font)
        qp.drawText(QRect(text_x, text_y, self.text_width, self.text_height), f"{self.score:.2f}", QtCore.Qt.AlignmentFlag.AlignCenter)


STATS_TEMPLATE = """
Intervals Analyzed: {num_intervals}  
Frames Sampled: {num_frames_sampled}  
Mean Grimace Score: {mean_grimace_score:.2f}
"""


class GrimaceResults(Ui_GGrimaceResults, QDialog):
    applied_signal = Signal(VideoFilesConfig)

    def __init__(self, parent, grimace_images: QList):
        super().__init__(parent)
        self.setupUi(self)

        self.grimace_images = grimace_images
        self.num_images = 0
        self.num_frames_sampled = 0

        self.gauge_plot = HorizontalGaugePlot(self)
        self.gauge_plot.setSizePolicy(QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed))
        self.gauge_plot.setMinimumHeight(40)
        self.gauge_plot.setMinimumHeight(40)
        self.gauge_plot.setMinimumWidth(100)
        self.frm_grimace_stats.layout().addWidget(self.gauge_plot)

        self.clear_images()
        self.refresh()

        self.grimace_images.list_cleared.connect(self.clear_images)
        self.grimace_images.list_changed.connect(self.refresh)

    def clear_images(self):
        while self.frm_grimace_images.layout().count() > 0:
            item = self.frm_grimace_images.layout().takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.num_images = 0
        self.num_frames_sampled = 0

    def refresh(self):
        # The way I'm keeping track of the number of images is a bit hacky, but it works for now

        if len(self.grimace_images.items) < self.num_images:
            # If the list was cleared (or for some other reason less images are in the list than before),
            # remove all images from the layout
            self.clear_images()

        for image, grimace_scores in self.grimace_images.items[self.num_images:]:
            # Add all images in the list that have not been added yet to the layout

            label = QLabel()
            if image is not None:
                # Render the 5 grimace scores on the image. This is mostly for debugging purposes
                # and may be removed in the future
                image = cv2.resize(image, (150, 150), interpolation=cv2.INTER_LINEAR)

                if grimace_scores is not None:
                    grimace_scores_string = "|".join([f"{score}" if score != 3 else "X" for score in grimace_scores])
                    image = cv2.putText(image, grimace_scores_string, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2, cv2.LINE_AA)

                # Support grayscale and color images
                h, w, ch = image.shape
                bytes_per_line = ch * w
                if ch == 1:
                    image = QImage(image.data, w, h, bytes_per_line, QImage.Format.Format_Grayscale8)
                else:
                    image = QImage(image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

                pixmap = QPixmap.fromImage(image)

                label.setPixmap(pixmap)
                self.num_frames_sampled += 1
            else:
                label.setText("No suitable image found")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.setMinimumWidth(150)
                label.setMinimumHeight(150)
                label.setMaximumWidth(150)
                label.setMaximumHeight(150)
                label.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed))

            self.frm_grimace_images.layout().addWidget(label)
            self.num_images += 1

        all_grimace_scores = [grimace_scores for _, grimace_scores in self.grimace_images.items if
                              grimace_scores is not None]
        if len(all_grimace_scores) == 0:
            mean_grimace_score = 0.0
        else:
            all_grimace_scores = np.stack(all_grimace_scores, axis=0)
            all_grimace_scores = all_grimace_scores.astype(np.float32)
            all_grimace_scores[all_grimace_scores == 3] = np.nan
            grimace_scores = np.nanmean(all_grimace_scores, axis=1)
            mean_grimace_score = np.nanmean(grimace_scores)

        stats = STATS_TEMPLATE.format(
            num_intervals=self.num_images,
            num_frames_sampled=self.num_frames_sampled,
            mean_grimace_score=mean_grimace_score
        )

        self.lbl_grimace_stats.setText(stats)
        self.gauge_plot.score = mean_grimace_score
        self.gauge_plot.update()


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dialog = GrimaceResults(None, QList())
    dialog.show()
    sys.exit(app.exec_())
