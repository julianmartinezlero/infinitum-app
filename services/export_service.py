from abc import ABC, abstractmethod
import shutil
from pathlib import Path
from utils.logger import log
from models.config_model import SharepointConfig, GoogleDriveConfig

class ExportStrategy(ABC):
    @abstractmethod
    def export(self, source_file: Path, target_name: str) -> bool:
        """
        Exports the master CSV file to the designated destination.
        Returns True if successful, False otherwise.
        """
        pass

class LocalExportService(ExportStrategy):
    def __init__(self, target_directory: str):
        self.target_dir = Path(target_directory)
        self.target_dir.mkdir(parents=True, exist_ok=True)

    def export(self, source_file: Path, target_name: str) -> bool:
        try:
            destination = self.target_dir / target_name
            shutil.copy2(source_file, destination)
            log.success(f"Locally exported: {destination}")
            return True
        except Exception as e:
            log.error(f"Local export failed for {target_name}: {str(e)}")
            return False

class SharepointExportService(ExportStrategy):
    def __init__(self, config: SharepointConfig):
        self.config = config
        # Placeholder for actual office365 authentication
        # from office365.sharepoint.client_context import ClientContext
        # from office365.runtime.auth.client_credential import ClientCredential
        
    def _get_context(self):
        from office365.sharepoint.client_context import ClientContext
        from office365.runtime.auth.client_credential import ClientCredential
        try:
            ctx = ClientContext(self.config.site_url).with_credentials(
                ClientCredential(self.config.client_id, self.config.client_secret)
            )
            return ctx
        except Exception as e:
            log.error(f"Failed to authenticate with SharePoint: {str(e)}")
            return None

    def export(self, source_file: Path, target_name: str) -> bool:
        log.info(f"Uploading {target_name} to SharePoint...")
        ctx = self._get_context()
        if not ctx:
            return False
            
        try:
            target_url = f"{self.config.target_folder}/{target_name}"
            with open(source_file, 'rb') as content_file:
                content = content_file.read()
                
            list_title = "Documents" # Default standard list
            # We assume target_folder is something like 'Shared Documents'
            folder = ctx.web.get_folder_by_server_relative_url(self.config.target_folder)
            folder.upload_file(target_name, content).execute_query()
            
            log.success(f"SharePoint export successful for {target_name}")
            return True
        except Exception as e:
            log.error(f"SharePoint upload failed for {target_name}: {str(e)}")
            return False

class GoogleDriveExportService(ExportStrategy):
    def __init__(self, config: GoogleDriveConfig):
        self.config = config

    def _get_drive(self):
        try:
            from pydrive2.auth import GoogleAuth
            from pydrive2.drive import GoogleDrive
            gauth = GoogleAuth()
            # Try to load credentials using pydrive2 mechanism
            # typically needs client_secrets.json in root or configured
            if self.config.credentials_path:
                gauth.LoadCredentialsFile(self.config.credentials_path)
            
            if gauth.credentials is None or gauth.access_token_expired:
                # Force local webserver auth if no valid creds (Requires UI interaction though)
                log.warning("Google Drive credentials expired or missing. Needs manual auth.")
                return None
            else:
                gauth.Authorize()
                return GoogleDrive(gauth)
        except Exception as e:
            log.error(f"Google Drive auth failed: {str(e)}")
            return None

    def export(self, source_file: Path, target_name: str) -> bool:
        log.info(f"Uploading {target_name} to Google Drive...")
        drive = self._get_drive()
        if not drive:
            return False
            
        try:
            file_metadata = {
                'title': target_name,
                'parents': [{'id': self.config.folder_id}] if self.config.folder_id else []
            }
            
            gfile = drive.CreateFile(file_metadata)
            gfile.SetContentFile(str(source_file))
            gfile.Upload()
            
            log.success(f"Google Drive export successful for {target_name}")
            return True
        except Exception as e:
            log.error(f"Google Drive upload failed for {target_name}: {str(e)}")
            return False
