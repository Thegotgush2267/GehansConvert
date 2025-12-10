import os
import sys
import subprocess
from PyQt5 import QtCore, QtGui, QtWidgets


class FfmpegWorker(QtCore.QObject):
    log_signal = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal(bool)

    def __init__(self, command, workdir):
        super().__init__()
        self.command = command
        self.workdir = workdir

    @QtCore.pyqtSlot()
    def run(self):
        try:
            startupinfo = None
            creationflags = 0

            # Hide ffmpeg console on Windows
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                creationflags |= subprocess.CREATE_NO_WINDOW

            process = subprocess.Popen(
                self.command,
                cwd=self.workdir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                startupinfo=startupinfo,
                creationflags=creationflags,
            )
        except FileNotFoundError:
            self.log_signal.emit("ERROR: ffmpeg not found. Make sure it is installed and in PATH.\n")
            self.finished.emit(False)
            return

        for line in process.stdout:
            self.log_signal.emit(line)

        process.wait()
        self.finished.emit(process.returncode == 0)


class RetroWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gehans Audio Converter")
        self.setMinimumSize(1000, 560)
        self.setWindowIcon(QtGui.QIcon())  # add icon if you want

        self.input_path = ""
        self.output_dir = os.path.expanduser("~")

        self._setup_ui()
        self._apply_style()

        self.worker_thread = None

    def _setup_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        layout = QtWidgets.QHBoxLayout(central)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # LEFT: fake "shapes" / blocks (decorative)
        left = QtWidgets.QFrame()
        left.setObjectName("UselessPanel")
        left_layout = QtWidgets.QVBoxLayout(left)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(16)

        for name in ["shape1", "shape2", "shape3"]:
            block = QtWidgets.QFrame()
            block.setObjectName(name)
            block.setMinimumHeight(90)
            left_layout.addWidget(block)

        left_layout.addStretch()
        layout.addWidget(left, 1)

        # RIGHT: main content
        right = QtWidgets.QFrame()
        right.setObjectName("MainPanel")
        right_layout = QtWidgets.QVBoxLayout(right)
        right_layout.setContentsMargins(24, 24, 24, 24)
        right_layout.setSpacing(18)

        # Header text
        header = QtWidgets.QLabel("Files Converted This Session")
        header.setObjectName("headerLabel")
        right_layout.addWidget(header)

        # Big retro number (we'll display selected format / converted count)
        self.big_label = QtWidgets.QLabel("0")
        self.big_label.setObjectName("bigNumber")
        self.big_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        right_layout.addWidget(self.big_label)

        # Subtext (status)
        self.sub_label = QtWidgets.QLabel("Pick a file. Pick a format. Convert it with ffmpeg.")
        self.sub_label.setObjectName("subLabel")
        right_layout.addWidget(self.sub_label)

        # Input row
        file_row = QtWidgets.QHBoxLayout()
        file_label = QtWidgets.QLabel("INPUT")
        file_label.setObjectName("miniLabel")
        self.file_display = QtWidgets.QLineEdit()
        self.file_display.setPlaceholderText("Select A file Human")
        self.file_display.setReadOnly(True)
        browse_btn = QtWidgets.QPushButton("BROWSE")
        browse_btn.clicked.connect(self.choose_input_file)
        file_row.addWidget(file_label)
        file_row.addWidget(self.file_display)
        file_row.addWidget(browse_btn)
        right_layout.addLayout(file_row)

        # Output row
        out_row = QtWidgets.QHBoxLayout()
        out_label = QtWidgets.QLabel("OUTPUT FOLDER")
        out_label.setObjectName("miniLabel")
        self.out_display = QtWidgets.QLineEdit()
        self.out_display.setReadOnly(True)
        self.out_display.setText(self.output_dir)
        out_btn = QtWidgets.QPushButton("CHANGE")
        out_btn.clicked.connect(self.choose_output_dir)
        out_row.addWidget(out_label)
        out_row.addWidget(self.out_display)
        out_row.addWidget(out_btn)
        right_layout.addLayout(out_row)

        # Format + preset row
        options_row = QtWidgets.QHBoxLayout()

        fmt_col = QtWidgets.QVBoxLayout()
        fmt_label = QtWidgets.QLabel("FORMAT")
        fmt_label.setObjectName("miniLabel")
        self.format_combo = QtWidgets.QComboBox()
        self.format_combo.addItems(["mp3", "opus", "wav", "flac", "webm", "mp4"])
        self.format_combo.currentTextChanged.connect(self._update_big_label)
        fmt_col.addWidget(fmt_label)
        fmt_col.addWidget(self.format_combo)
        options_row.addLayout(fmt_col)

        preset_col = QtWidgets.QVBoxLayout()
        preset_label = QtWidgets.QLabel("Quality")
        preset_label.setObjectName("miniLabel")
        self.quality_combo = QtWidgets.QComboBox()
        self.quality_combo.addItems(["Very Good Quality", "Very Very Good Quality", "Good Quality"])
        preset_col.addWidget(preset_label)
        preset_col.addWidget(self.quality_combo)
        options_row.addLayout(preset_col)

        right_layout.addLayout(options_row)

        # Convert + progress
        action_row = QtWidgets.QHBoxLayout()
        self.convert_btn = QtWidgets.QPushButton("CONVERT")
        self.convert_btn.clicked.connect(self.start_convert)
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        action_row.addWidget(self.convert_btn, 1)
        action_row.addWidget(self.progress, 2)
        right_layout.addLayout(action_row)

        # Log
        log_label = QtWidgets.QLabel("CONVERSION LOG")
        log_label.setObjectName("miniLabel")
        right_layout.addWidget(log_label)
        self.log_box = QtWidgets.QTextEdit()
        self.log_box.setReadOnly(True)
        right_layout.addWidget(self.log_box, 1)

        layout.addWidget(right, 2)

        # Drop shadow on right panel
        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(16)
        shadow.setColor(QtGui.QColor(0, 0, 0, 200))
        right.setGraphicsEffect(shadow)

    def _apply_style(self):
        # synthwave + pixel-ish style
        self.setStyleSheet("""
            QMainWindow {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2a0033,
                    stop:0.5 #150020,
                    stop:1 #050008
                );
            }
            #leftPanel {
                background: transparent;
            }
            #rightPanel {
                background-color: rgba(10, 0, 25, 0.96);
                border-radius: 24px;
                border: 1px solid rgba(255, 0, 150, 0.35);
            }
            #headerLabel {
                color: #ff4fd8;
                font-size: 11px;
                letter-spacing: 3px;
                text-transform: uppercase;
            }
            #bigNumber {
                color: #ff4fd8;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 64px;
                font-weight: 900;
            }
            #subLabel {
                color: #f9a8ff;
                font-size: 13px;
                margin-bottom: 8px;
            }
            #miniLabel {
                color: #f472ff;
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 2px;
            }
            QLineEdit {
                background-color: #0a0015;
                border-radius: 10px;
                border: 1px solid #5b217a;
                padding: 6px 8px;
                color: #f9fafb;
            }
            QLineEdit:focus {
                border: 1px solid #ff4fd8;
            }
            QPushButton {
                background-color: #ff4fd8;
                color: #0b0010;
                border-radius: 12px;
                padding: 8px 16px;
                border: none;
                font-weight: 700;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #ff73e4;
            }
            QPushButton:pressed {
                background-color: #db2fad;
            }
            QPushButton:disabled {
                background-color: #3b143f;
                color: #a855f7;
            }
            QComboBox {
                background-color: #0a0015;
                border-radius: 10px;
                border: 1px solid #5b217a;
                padding: 6px 8px;
                color: #f9fafb;
            }
            QComboBox::drop-down {
                border: 0px;
            }
            QComboBox QAbstractItemView {
                background-color: #0a0015;
                border: 1px solid #5b217a;
                selection-background-color: #ff4fd8;
                color: #f9fafb;
            }
            QTextEdit {
                background-color: #05000e;
                border-radius: 12px;
                border: 1px solid #5b217a;
                color: #e5e7eb;
                font-family: Consolas, "Fira Code", monospace;
                font-size: 11px;
                padding: 6px;
            }
            QProgressBar {
                background-color: #05000e;
                border-radius: 10px;
                border: 1px solid #5b217a;
            }
            QProgressBar::chunk {
                background-color: #ff4fd8;
                border-radius: 10px;
            }
            #shape1, #shape2, #shape3 {
                background-color: transparent;
                border: 2px solid #ff4fd8;
                border-radius: 24px;
            }
            #shape2 {
                transform: skewX(-10deg);
            }
            #shape3 {
                border-radius: 8px;
            }
        """)

    def _update_big_label(self):
        fmt = self.format_combo.currentText().upper()
        self.big_label.setText(fmt)

    def append_log(self, text: str):
        self.log_box.moveCursor(QtGui.QTextCursor.End)
        self.log_box.insertPlainText(text)
        self.log_box.moveCursor(QtGui.QTextCursor.End)

    def set_busy(self, busy: bool):
        self.convert_btn.setDisabled(busy)
        if busy:
            self.progress.setRange(0, 0)  # busy/infinite
        else:
            self.progress.setRange(0, 1)
            self.progress.setValue(0)

    def choose_input_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Choose input file",
            self.output_dir,
            "Media files (*.*)"
        )
        if path:
            self.input_path = path
            self.file_display.setText(path)
            self.output_dir = os.path.dirname(path)
            self.out_display.setText(self.output_dir)

    def choose_output_dir(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Choose output folder",
            self.output_dir
        )
        if folder:
            self.output_dir = folder
            self.out_display.setText(folder)

    def start_convert(self):
        if not self.input_path:
            QtWidgets.QMessageBox.warning(self, "No input", "Pick a file first.")
            return

        if not os.path.isdir(self.output_dir):
            QtWidgets.QMessageBox.warning(self, "Invalid output", "Output folder does not exist.")
            return

        in_path = self.input_path
        base_name = os.path.splitext(os.path.basename(in_path))[0]
        ext = self.format_combo.currentText()
        out_path = os.path.join(self.output_dir, f"{base_name}.{ext}")
        vibe = self.quality_combo.currentText()

        cmd = ["ffmpeg", "-y", "-i", in_path]

        # Very basic presets, same logic as before
        if ext in ("mp3", "opus", "wav", "flac"):
            if ext == "mp3":
                cmd += ["-vn", "-c:a", "libmp3lame"]
                if vibe == "High quality":
                    cmd += ["-b:a", "320k"]
                elif vibe == "Smaller file":
                    cmd += ["-b:a", "128k"]
                else:
                    cmd += ["-b:a", "192k"]
            elif ext == "opus":
                cmd += ["-vn", "-c:a", "libopus"]
                if vibe == "High quality":
                    cmd += ["-b:a", "192k"]
                elif vibe == "Smaller file":
                    cmd += ["-b:a", "96k"]
                else:
                    cmd += ["-b:a", "128k"]
            elif ext == "wav":
                cmd += ["-vn", "-c:a", "pcm_s16le"]
            elif ext == "flac":
                cmd += ["-vn", "-c:a", "flac"]
        else:
            # video
            if ext == "webm":
                cmd += ["-c:v", "libvpx-vp9", "-c:a", "libopus", "-b:v", "0"]
                if vibe == "High quality":
                    cmd += ["-crf", "20"]
                elif vibe == "Smaller file":
                    cmd += ["-crf", "32"]
                else:
                    cmd += ["-crf", "28"]
            else:  # mp4
                cmd += ["-c:v", "libx264", "-c:a", "aac"]
                if vibe == "High quality":
                    cmd += ["-crf", "18", "-preset", "slow"]
                elif vibe == "Smaller file":
                    cmd += ["-crf", "28", "-preset", "faster"]
                else:
                    cmd += ["-crf", "23", "-preset", "medium"]

        cmd.append(out_path)

        self.append_log(f"\n=== Starting conversion ===\n")
        self.append_log(f"Input:  {in_path}\n")
        self.append_log(f"Output: {out_path}\n\n")

        self.set_busy(True)
        self.sub_label.setText("Converting... don’t close this or the vibes die.")

        self.worker_thread = QtCore.QThread()
        self.worker = FfmpegWorker(cmd, self.output_dir)
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.log_signal.connect(self.append_log)
        self.worker.finished.connect(self.conversion_finished)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.worker_thread.start()

    @QtCore.pyqtSlot(bool)
    def conversion_finished(self, ok: bool):
        self.set_busy(False)
        if ok:
            self.append_log("\n=== Conversion finished successfully ===\n")
            self.sub_label.setText("File converted. You’re one step closer to audio supremacy.")
            # bump number like a "files converted" stat
            try:
                current = int(self.big_label.text()) if self.big_label.text().isdigit() else 0
                self.big_label.setText(str(current + 1))
            except ValueError:
                self.big_label.setText("1")
        else:
            self.append_log("\n=== Conversion failed ===\n")
            self.sub_label.setText("Conversion failed. FFmpeg did not vibe with that file.")


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Neon Converter Checkpoint")
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

    win = RetroWindow()
    win.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
    
# Bob is a builder
# This is Created By Gehans and is Licensed under GPLv2
