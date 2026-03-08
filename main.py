import sys
import os
import shutil
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QFileDialog, QListWidget, QSpinBox,
                               QCheckBox, QLineEdit, QProgressBar, QFormLayout,
                               QGroupBox, QMessageBox, QAbstractItemView)
from PySide6.QtCore import QThread, Signal, Slot

from i18n import TRANSLATIONS, detect_system_lang
from video_engine import VideoEngine
from image_engine import ImageEngine


class Worker(QThread):
    """协调视频引擎与图像引擎的异步线程"""
    progress = Signal(int, str)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, video_paths, settings):
        super().__init__()
        self.video_paths = video_paths
        self.settings = settings
        self.v_engine = VideoEngine()
        self.i_engine = ImageEngine()

    def run(self):
        try:
            total_videos = len(self.video_paths)
            for idx, video_path in enumerate(self.video_paths):
                # 1. 获取视频信息
                info = self.v_engine.get_video_info(video_path)

                # 2. 计算截图点
                rows, cols = self.settings.get('rows', 4), self.settings.get('cols', 4)
                num_thumbs = rows * cols
                start, end = info['duration'] * 0.05, info['duration'] * 0.95
                timestamps = [start + i * (end - start) / (num_thumbs - 1) for i in
                              range(num_thumbs)] if num_thumbs > 1 else [info['duration'] / 2]

                # 3. 提取截图
                temp_dir = os.path.join(os.path.dirname(video_path), ".veetgem_tmp")
                os.makedirs(temp_dir, exist_ok=True)
                thumb_files = []

                lang = self.settings.get('lang', 'zh')
                msg_template = TRANSLATIONS[lang]['status_extracting']

                for i, ts in enumerate(timestamps):
                    t_path = os.path.join(temp_dir, f"t_{i}.jpg")
                    self.v_engine.extract_frame(video_path, ts, t_path)
                    thumb_files.append((t_path, ts))

                    p = int((idx / total_videos) * 100 + ((i + 1) / (num_thumbs + 2) / total_videos) * 100)
                    self.progress.emit(p, f"[{idx + 1}/{total_videos}] {msg_template.format(i + 1, num_thumbs)}")

                # 4. 拼接预览图
                # 传递 output_dir
                actual_settings = self.settings.copy()
                if not actual_settings.get('output_dir'):
                    actual_settings['output_dir'] = os.path.dirname(video_path)

                self.i_engine.create_grid_preview(info, thumb_files, actual_settings)

                # 清理临时目录
                shutil.rmtree(temp_dir, ignore_errors=True)

            self.finished.emit(str(total_videos))
        except Exception as e:
            self.error.emit(str(e))


class DropListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        valid_exts = ('.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.webm', '.m4v')
        for f in files:
            if os.path.isdir(f):
                for r, d, fnames in os.walk(f):
                    for fn in fnames:
                        if fn.lower().endswith(valid_exts): self.addItem(os.path.join(r, fn))
            elif f.lower().endswith(valid_exts):
                self.addItem(f)


class VeetgemApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.lang = detect_system_lang()

        # 声明组件
        self.file_list_label = None;
        self.file_list = None
        self.btn_add = None;
        self.btn_remove = None;
        self.btn_clear = None
        self.settings_group = None;
        self.btn_lang = None;
        self.btn_start = None
        self.label_rows = None;
        self.spin_rows = None;
        self.label_cols = None;
        self.spin_cols = None
        self.label_width = None;
        self.spin_width = None;
        self.check_header = None;
        self.check_timestamp = None
        self.label_margin = None;
        self.spin_margin = None;
        self.label_output = None;
        self.line_output = None
        self.btn_browse = None;
        self.label_filename = None;
        self.line_filename = None
        self.progress_bar = None;
        self.status_label = None;
        self.worker = None

        self.setMinimumSize(850, 600)
        self.init_ui()
        self.retranslate_ui()

    def init_ui(self):
        central = QWidget();
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # Left
        left = QVBoxLayout()
        self.file_list_label = QLabel("")
        left.addWidget(self.file_list_label)
        self.file_list = DropListWidget()
        left.addWidget(self.file_list)
        btns = QHBoxLayout()
        self.btn_add = QPushButton("");
        self.btn_add.clicked.connect(self.add_files)
        self.btn_remove = QPushButton("");
        self.btn_remove.clicked.connect(self.remove_files)
        self.btn_clear = QPushButton("");
        self.btn_clear.clicked.connect(self.file_list.clear)
        btns.addWidget(self.btn_add);
        btns.addWidget(self.btn_remove);
        btns.addWidget(self.btn_clear)
        left.addLayout(btns);
        main_layout.addLayout(left, 2)

        # Right
        right = QVBoxLayout()
        l_btn_lyt = QHBoxLayout();
        l_btn_lyt.addStretch()
        self.btn_lang = QPushButton("");
        self.btn_lang.setFixedWidth(80);
        self.btn_lang.clicked.connect(self.toggle_lang)
        l_btn_lyt.addWidget(self.btn_lang);
        right.addLayout(l_btn_lyt)

        self.settings_group = QGroupBox("");
        form = QFormLayout()
        self.spin_rows = QSpinBox();
        self.spin_rows.setRange(1, 20);
        self.spin_rows.setValue(4)
        self.spin_cols = QSpinBox();
        self.spin_cols.setRange(1, 20);
        self.spin_cols.setValue(4)
        self.label_rows = QLabel("");
        self.label_cols = QLabel("")
        form.addRow(self.label_rows, self.spin_rows);
        form.addRow(self.label_cols, self.spin_cols)
        self.spin_width = QSpinBox();
        self.spin_width.setRange(720, 7680);
        self.spin_width.setSingleStep(120);
        self.spin_width.setValue(1920)
        self.label_width = QLabel("");
        form.addRow(self.label_width, self.spin_width)
        self.check_header = QCheckBox("");
        self.check_header.setChecked(True)
        self.check_timestamp = QCheckBox("");
        self.check_timestamp.setChecked(True)
        form.addRow(self.check_header);
        form.addRow(self.check_timestamp)
        self.spin_margin = QSpinBox();
        self.spin_margin.setRange(0, 100);
        self.spin_margin.setValue(10)
        self.label_margin = QLabel("");
        form.addRow(self.label_margin, self.spin_margin)
        self.label_output = QLabel("");
        self.line_output = QLineEdit();
        self.btn_browse = QPushButton("")
        self.btn_browse.clicked.connect(self.browse_out);
        ol = QHBoxLayout();
        ol.addWidget(self.line_output);
        ol.addWidget(self.btn_browse)
        form.addRow(self.label_output, ol);
        self.label_filename = QLabel("");
        self.line_filename = QLineEdit()
        form.addRow(self.label_filename, self.line_filename)
        self.settings_group.setLayout(form);
        right.addWidget(self.settings_group)
        right.addStretch()
        self.progress_bar = QProgressBar();
        right.addWidget(self.progress_bar)
        self.status_label = QLabel("");
        right.addWidget(self.status_label)
        self.btn_start = QPushButton("");
        self.btn_start.setFixedHeight(50)
        self.btn_start.setStyleSheet(
            "background-color: #007AFF; color: white; font-weight: bold; font-size: 16px; border-radius: 8px;")
        self.btn_start.clicked.connect(self.start)
        right.addWidget(self.btn_start);
        main_layout.addLayout(right, 1)

    def retranslate_ui(self):
        t = TRANSLATIONS[self.lang]
        self.setWindowTitle(t['window_title']);
        self.file_list_label.setText(t['file_list_label'])
        self.btn_add.setText(t['btn_add']);
        self.btn_remove.setText(t['btn_remove']);
        self.btn_clear.setText(t['btn_clear'])
        self.settings_group.setTitle(t['settings_group']);
        self.label_rows.setText(t['rows']);
        self.label_cols.setText(t['cols'])
        self.label_width.setText(t['width']);
        self.check_header.setText(t['show_header']);
        self.check_timestamp.setText(t['show_timestamp'])
        self.label_margin.setText(t['margin']);
        self.label_output.setText(t['output_path']);
        self.btn_browse.setText(t['browse'])
        self.label_filename.setText(t['custom_name']);
        self.line_output.setPlaceholderText(t['output_placeholder'])
        self.line_filename.setPlaceholderText(t['filename_placeholder'])
        self.btn_start.setText(t['btn_start'] if self.btn_start.isEnabled() else t['processing'])
        self.status_label.setText(t['status_ready']);
        self.btn_lang.setText(t['lang_btn'])

    def toggle_lang(self):
        self.lang = 'en' if self.lang == 'zh' else 'zh';
        self.retranslate_ui()

    def add_files(self):
        t = TRANSLATIONS[self.lang]
        fs, _ = QFileDialog.getOpenFileNames(self, t['btn_add'], "",
                                             "Videos (*.mp4 *.mkv *.avi *.mov *.flv *.wmv *.webm *.m4v)")
        if fs: self.file_list.addItems(fs)

    def remove_files(self):
        for i in self.file_list.selectedItems(): self.file_list.takeItem(self.file_list.row(i))

    def browse_out(self):
        d = QFileDialog.getExistingDirectory(self, TRANSLATIONS[self.lang]['output_path'])
        if d: self.line_output.setText(d)

    def start(self):
        v_paths = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        if not v_paths:
            QMessageBox.warning(self, TRANSLATIONS[self.lang]['msg_error_title'],
                                TRANSLATIONS[self.lang]['msg_no_files'])
            return
        self.set_ui_enabled(False)
        self.worker = Worker(v_paths, {
            'rows': self.spin_rows.value(), 'cols': self.spin_cols.value(), 'width': self.spin_width.value(),
            'show_header': self.check_header.isChecked(), 'show_timestamp': self.check_timestamp.isChecked(),
            'margin': self.spin_margin.value(), 'output_dir': self.line_output.text().strip(),
            'custom_name': self.line_filename.text().strip(), 'lang': self.lang
        })
        self.worker.progress.connect(self.update_p);
        self.worker.finished.connect(self.done);
        self.worker.error.connect(self.err)
        self.worker.start()

    def set_ui_enabled(self, e):
        t = TRANSLATIONS[self.lang]
        self.btn_start.setEnabled(e);
        self.file_list.setEnabled(e);
        self.btn_add.setEnabled(e)
        self.btn_remove.setEnabled(e);
        self.btn_clear.setEnabled(e);
        self.btn_lang.setEnabled(e)
        if e:
            self.btn_start.setText(t['btn_start']); self.btn_start.setStyleSheet(
                "background-color: #007AFF; color: white; font-weight: bold; font-size: 16px; border-radius: 8px;")
        else:
            self.btn_start.setText(t['processing']); self.btn_start.setStyleSheet(
                "background-color: #A0A0A0; color: white; font-weight: bold; font-size: 16px; border-radius: 8px;")

    @Slot(int, str)
    def update_p(self, v, m):
        self.progress_bar.setValue(v); self.status_label.setText(m)

    @Slot(str)
    def done(self, c):
        t = TRANSLATIONS[self.lang];
        self.set_ui_enabled(True);
        self.progress_bar.setValue(100)
        self.status_label.setText(t['status_done']);
        QMessageBox.information(self, t['status_done'], t['msg_success'].format(c))

    @Slot(str)
    def err(self, e):
        t = TRANSLATIONS[self.lang];
        self.set_ui_enabled(True);
        self.status_label.setText(t['status_error'])
        QMessageBox.critical(self, t['msg_error_title'], t['msg_error_content'].format(e))


if __name__ == "__main__":
    app = QApplication(sys.argv);
    app.setStyle("Fusion");
    w = VeetgemApp();
    w.show();
    sys.exit(app.exec())
