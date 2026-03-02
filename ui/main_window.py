import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QLineEdit, QFileDialog, 
    QProgressBar, QTextBrowser, QComboBox, QGroupBox, QFormLayout, QMessageBox,
    QStackedWidget
)
from PySide6.QtCore import Qt, Signal, QObject
from loguru import logger

from models.config_model import AppConfig, SharepointConfig, GoogleDriveConfig
from config.config_manager import ConfigManager
from services.directory_scanner import DirectoryScannerService
from services.gestion_detector import GestionDetectorService
from repositories.dbf_repository import DBFRepository
from services.polars_transformer import PolarsTransformerService
from services.master_file_builder import MasterFileBuilderService
from services.process_orchestrator import ProcessOrchestrator
from services.export_service import LocalExportService, SharepointExportService, GoogleDriveExportService

from ui.worker import ProcessWorker

class LogSignal(QObject):
    new_log = Signal(str)

class GUILogSink:
    def __init__(self, log_signal: LogSignal):
        self.log_signal = log_signal

    def write(self, message):
        # We emit the message to be picked up by the UI thread safely
        self.log_signal.new_log.emit(message.strip())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Infinitum APP")
        self.resize(800, 600)
        self.config = ConfigManager.load_config()
        self.worker = None

        # Setup Logging to GUI
        self.log_signal = LogSignal()
        self.log_signal.new_log.connect(self.append_log)
        logger.add(GUILogSink(self.log_signal), format="{time:HH:mm:ss} | {level} | {message}")

        self._setup_ui()
        self._load_config_to_ui()

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 1. Input Configuration
        input_group = QGroupBox("Directory Options")
        input_layout = QFormLayout()

        self.root_path_input = QLineEdit()
        self.root_path_btn = QPushButton("Browse")
        self.root_path_btn.clicked.connect(self._browse_root)
        
        root_hlayout = QHBoxLayout()
        root_hlayout.addWidget(self.root_path_input)
        root_hlayout.addWidget(self.root_path_btn)

        self.regex_input = QLineEdit()
        
        input_layout.addRow("Root Folder (Gestiones):", root_hlayout)
        input_layout.addRow("Gestion Regex:", self.regex_input)
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        # 2. Output Configuration
        output_group = QGroupBox("Export Destination")
        output_layout = QVBoxLayout()
        
        # Dropdown
        combo_layout = QFormLayout()
        self.dest_combo = QComboBox()
        # self.dest_combo.addItems(["local", "sharepoint", "gdrive"])

        self.dest_combo.addItems(["local"])
        self.dest_combo.currentTextChanged.connect(self._toggle_output_fields)
        combo_layout.addRow("Type:", self.dest_combo)
        output_layout.addLayout(combo_layout)

        # Stacked Widget to hold the dynamic fields
        self.dest_stacked = QStackedWidget()
        
        # --- Local Form ---
        self.local_widget = QWidget()
        local_form = QFormLayout(self.local_widget)
        local_form.setContentsMargins(0, 0, 0, 0)
        
        self.local_path_input = QLineEdit()
        self.local_path_btn = QPushButton("Browse")
        self.local_path_btn.clicked.connect(self._browse_local)
        
        local_hlayout = QHBoxLayout()
        local_hlayout.addWidget(self.local_path_input)
        local_hlayout.addWidget(self.local_path_btn)
        local_form.addRow("Local Folder:", local_hlayout)
        
        self.dest_stacked.addWidget(self.local_widget)

        # --- Sharepoint Form ---
        self.sp_widget = QWidget()
        sp_form = QFormLayout(self.sp_widget)
        sp_form.setContentsMargins(0, 0, 0, 0)

        self.sp_url_input = QLineEdit()
        self.sp_client_id = QLineEdit()
        self.sp_client_secret = QLineEdit()
        self.sp_target_folder = QLineEdit()
        
        sp_form.addRow("SP Site URL:", self.sp_url_input)
        sp_form.addRow("SP Client ID:", self.sp_client_id)
        sp_form.addRow("SP Secret:", self.sp_client_secret)
        sp_form.addRow("SP Folder:", self.sp_target_folder)
        
        self.dest_stacked.addWidget(self.sp_widget)

        # --- GDrive Form ---
        self.gdrive_widget = QWidget()
        gdrive_form = QFormLayout(self.gdrive_widget)
        gdrive_form.setContentsMargins(0, 0, 0, 0)
        
        self.gdrive_creds_input = QLineEdit()
        self.gdrive_creds_btn = QPushButton("Select JSON")
        self.gdrive_creds_btn.clicked.connect(lambda: self.gdrive_creds_input.setText(QFileDialog.getOpenFileName(self, "Select Credentials JSON")[0]))
        self.gdrive_folder_id = QLineEdit()
        
        gdrive_creds_hlayout = QHBoxLayout()
        gdrive_creds_hlayout.addWidget(self.gdrive_creds_input)
        gdrive_creds_hlayout.addWidget(self.gdrive_creds_btn)
        
        gdrive_form.addRow("GDrive Creds JSON:", gdrive_creds_hlayout)
        gdrive_form.addRow("GDrive Folder ID:", self.gdrive_folder_id)
        
        self.dest_stacked.addWidget(self.gdrive_widget)

        output_layout.addWidget(self.dest_stacked)

        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)

        # 3. Actions / Progress
        action_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Processing")
        self.start_btn.setMinimumHeight(40)
        self.start_btn.clicked.connect(self.start_process)
        action_layout.addWidget(self.start_btn)
        main_layout.addLayout(action_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_label = QLabel("Ready.")
        
        main_layout.addWidget(self.progress_label)
        main_layout.addWidget(self.progress_bar)

        # 4. Logs
        self.log_browser = QTextBrowser()
        main_layout.addWidget(self.log_browser)

        self._toggle_output_fields(self.dest_combo.currentText())

    def _toggle_output_fields(self, dest_type):
        if dest_type == "local":
            self.dest_stacked.setCurrentWidget(self.local_widget)
        elif dest_type == "sharepoint":
            self.dest_stacked.setCurrentWidget(self.sp_widget)
        elif dest_type == "gdrive":
            self.dest_stacked.setCurrentWidget(self.gdrive_widget)

    def _browse_root(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Root Client Directory")
        if folder:
            self.root_path_input.setText(folder)

    def _browse_local(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Local Export Destination")
        if folder:
            self.local_path_input.setText(folder)

    def _load_config_to_ui(self):
        self.root_path_input.setText(self.config.last_root_path)
        self.regex_input.setText(self.config.regex_gestion)
        
        idx = self.dest_combo.findText(self.config.export_destination)
        if idx >= 0:
            self.dest_combo.setCurrentIndex(idx)
            
        self.local_path_input.setText(self.config.local_export_path)
        
        self.sp_url_input.setText(self.config.sharepoint.site_url)
        self.sp_client_id.setText(self.config.sharepoint.client_id)
        self.sp_client_secret.setText(self.config.sharepoint.client_secret)
        self.sp_target_folder.setText(self.config.sharepoint.target_folder)
        
        self.gdrive_creds_input.setText(self.config.gdrive.credentials_path)
        self.gdrive_folder_id.setText(self.config.gdrive.folder_id)

    def _save_config_from_ui(self):
        self.config.last_root_path = self.root_path_input.text()
        self.config.regex_gestion = self.regex_input.text()
        self.config.export_destination = self.dest_combo.currentText()
        self.config.local_export_path = self.local_path_input.text()
        
        self.config.sharepoint = SharepointConfig(
            site_url=self.sp_url_input.text(),
            client_id=self.sp_client_id.text(),
            client_secret=self.sp_client_secret.text(),
            target_folder=self.sp_target_folder.text()
        )
        
        self.config.gdrive = GoogleDriveConfig(
            credentials_path=self.gdrive_creds_input.text(),
            folder_id=self.gdrive_folder_id.text()
        )
        ConfigManager.save_config(self.config)

    def append_log(self, text):
        self.log_browser.append(text)
        # Auto-scroll to bottom
        scrollbar = self.log_browser.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def start_process(self):
        root_path_str = self.root_path_input.text()
        if not root_path_str or not Path(root_path_str).exists():
            QMessageBox.critical(self, "Error", "Invalid root folder path specified.")
            return

        # Save current UI settings into ConfigManager so they are remembered
        self._save_config_from_ui()

        # Build strategy
        export_mode = self.config.export_destination
        if export_mode == "local":
            if not self.config.local_export_path:
                QMessageBox.critical(self, "Error", "Local export destination missing.")
                return
            strategy = LocalExportService(self.config.local_export_path)
        elif export_mode == "sharepoint":
            strategy = SharepointExportService(self.config.sharepoint)
        elif export_mode == "gdrive":
            strategy = GoogleDriveExportService(self.config.gdrive)
        else:
            return

        # Compose Orchestrator
        scanner = DirectoryScannerService(GestionDetectorService(self.config.regex_gestion))
        orchestrator = ProcessOrchestrator(
            scanner,
            DBFRepository(),
            PolarsTransformerService(),
            MasterFileBuilderService()
        )

        self.start_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log_browser.clear()
        
        # Setup Background Worker
        self.worker = ProcessWorker(orchestrator, Path(root_path_str), strategy)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.process_finished.connect(self.process_completed)
        self.worker.error_occurred.connect(self.process_error)
        
        logger.info("Initializing Process...")
        self.worker.start()

    def update_progress(self, current, total, desc):
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
        self.progress_label.setText(desc)

    def process_completed(self, result):
        self.start_btn.setEnabled(True)
        if result.success:
            QMessageBox.information(self, "Success", f"Processed {result.processed_files} files successfully.")
        else:
            QMessageBox.warning(self, "Completed with Errors", "Process finished but with some errors. Check logs.")

    def process_error(self, error_msg):
        self.start_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", f"A fatal error occurred:\n{error_msg}")
