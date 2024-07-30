import sys
import os
import yt_dlp
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton, 
                             QVBoxLayout, QFileDialog, QMessageBox, QProgressBar, 
                             QComboBox, QTabWidget, QScrollArea, QDialog, QFormLayout, 
                             QDialogButtonBox)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

class QualityDialog(QDialog):
    def __init__(self, parent=None, for_mp3=False):
        super().__init__(parent)
        self.for_mp3 = for_mp3
        self.setWindowTitle("Select Quality")
        self.setFixedSize(300, 200)

        layout = QFormLayout()
        layout.setLabelAlignment(Qt.AlignRight)

        self.setStyleSheet("""
            QDialog {
                background-color: #F5F5F5;
                border-radius: 12px;
            }
            QLabel {
                color: #333;
                font-size: 16px;
                font-weight: bold;
            }
            QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 8px;
                padding: 8px;
                color: #333;
                font-size: 14px;
            }
            QComboBox::drop-down {
                border-left: 1px solid #CCCCCC;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
                background-color: #FFFFFF;
            }
            QDialogButtonBox {
                alignment: center;
                margin-top: 10px;
            }
            QPushButton {
                background-color: #007BFF;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)

        if not self.for_mp3:
            self.video_quality_combo = QComboBox(self)
            self.video_quality_combo.addItems(['720p', '1080p', '1440p', '4K'])
            layout.addRow(QLabel("Video Quality:"), self.video_quality_combo)

        self.audio_quality_combo = QComboBox(self)
        self.audio_quality_combo.addItems(['128k', '192k', '256k', '320k'])
        layout.addRow(QLabel("Audio Quality:"), self.audio_quality_combo)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def get_quality(self):
        if hasattr(self, 'video_quality_combo'):
            return (self.video_quality_combo.currentText(), self.audio_quality_combo.currentText())
        return (None, self.audio_quality_combo.currentText())

class YouTubeDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.downloaded_files = []

    def initUI(self):
        self.setWindowTitle('PotsuDEV Downloader')
        self.setGeometry(100, 100, 700, 500)
        self.setWindowIcon(QIcon('icon.ico'))

        self.setStyleSheet("""
            QWidget {
                background-color: #F0F0F0;
                border-radius: 15px;
                padding: 10px;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel {
                color: #333;
                font-size: 16px;
            }
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                color: #333;
            }
            QPushButton {
                background-color: #007BFF;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QProgressBar {
                background-color: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 8px;
                text-align: center;
                font-size: 14px;
                color: #333;
            }
            QProgressBar::chunk {
                background-color: #007BFF;
                border-radius: 8px;
            }
            QTabWidget::pane {
                border: 1px solid #CCCCCC;
                border-radius: 12px;
            }
            QTabBar::tab {
                background: #FFFFFF;
                color: #333;
                border-radius: 12px;
                padding: 10px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #E0E0E0;
            }
        """)

        layout = QVBoxLayout()

        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_download_tab(), "Download")
        self.tabs.addTab(self.create_history_tab(), "History")
        layout.addWidget(self.tabs)

        self.setLayout(layout)
        self.show()

    def create_download_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.label_url = QLabel('YouTube Video URL:', self)
        layout.addWidget(self.label_url)

        self.entry_url = QLineEdit(self)
        self.entry_url.setPlaceholderText("Enter video URL here")
        layout.addWidget(self.entry_url)

        self.label_directory = QLabel('Directory to Save Video:', self)
        layout.addWidget(self.label_directory)

        self.entry_directory = QLineEdit(self)
        self.entry_directory.setPlaceholderText("Select directory")
        layout.addWidget(self.entry_directory)

        self.button_select_directory = QPushButton('Select Directory', self)
        self.button_select_directory.clicked.connect(self.select_directory)
        layout.addWidget(self.button_select_directory)

        self.button_download_video = QPushButton('Download Video', self)
        self.button_download_video.clicked.connect(self.select_quality_for_video)
        layout.addWidget(self.button_download_video)

        self.button_download_mp3 = QPushButton('Download and Convert to MP3', self)
        self.button_download_mp3.clicked.connect(self.select_quality_for_mp3)
        layout.addWidget(self.button_download_mp3)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.label_status = QLabel('', self)
        layout.addWidget(self.label_status)

        tab.setLayout(layout)
        return tab

    def create_history_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_area_widget)

        self.history_list = QVBoxLayout()
        self.scroll_area_widget.setLayout(self.history_list)

        layout.addWidget(self.scroll_area)
        tab.setLayout(layout)
        return tab

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.entry_directory.setText(directory)

    def select_quality_for_video(self):
        dialog = QualityDialog(self, for_mp3=False)
        if dialog.exec_():
            video_quality, audio_quality = dialog.get_quality()
            self.download_video(video_quality, audio_quality)

    def select_quality_for_mp3(self):
        dialog = QualityDialog(self, for_mp3=True)
        if dialog.exec_():
            _, audio_quality = dialog.get_quality()
            self.download_and_convert_mp3(audio_quality)

    def download_video(self, video_quality, audio_quality):
        url = self.entry_url.text()
        directory = self.entry_directory.text()

        if not url:
            QMessageBox.critical(self, "Error", "Please enter a YouTube video URL.")
            return

        if not directory:
            QMessageBox.critical(self, "Error", "Please select a directory to save the video.")
            return

        if not os.path.exists(directory):
            QMessageBox.critical(self, "Error", "The selected directory does not exist.")
            return

        ydl_opts = {
            'outtmpl': os.path.join(directory, '%(title)s.%(ext)s'),
            'format': f'bestvideo[height<={video_quality}]+bestaudio/best[height<={video_quality}]',
            'noplaylist': True,
            'nocheckcertificate': True,
            'quiet': True
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.label_status.setText('Download completed!')
            self.update_history(url, directory)
        except yt_dlp.utils.DownloadError as e:
            QMessageBox.critical(self, "Error", f"Error downloading video: {e}")
        except Exception as e:
            self.label_status.setText(f'Error: {e}')

    def download_and_convert_mp3(self, audio_quality):
        url = self.entry_url.text()
        directory = self.entry_directory.text()

        if not url:
            QMessageBox.critical(self, "Error", "Please enter a YouTube video URL.")
            return

        if not directory:
            QMessageBox.critical(self, "Error", "Please select a directory to save the MP3.")
            return

        if not os.path.exists(directory):
            QMessageBox.critical(self, "Error", "The selected directory does not exist.")
            return

        ydl_opts = {
            'outtmpl': os.path.join(directory, '%(title)s.%(ext)s'),
            'format': 'bestaudio/best',
            'noplaylist': True,
            'nocheckcertificate': True,
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': audio_quality
            }]
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.label_status.setText('Download and conversion completed!')
            self.update_history(url, directory)
        except yt_dlp.utils.DownloadError as e:
            QMessageBox.critical(self, "Error", f"Error downloading and converting video: {e}")
        except Exception as e:
            self.label_status.setText(f'Error: {e}')

    def update_history(self, url, directory):
        file_name = os.path.basename(directory)
        self.history_list.addWidget(QLabel(f"Downloaded: {file_name} from URL: {url}"))
        self.downloaded_files.append(directory)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = YouTubeDownloader()
    sys.exit(app.exec_())
