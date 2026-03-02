from pydantic import BaseModel, Field
from typing import Optional

class SharepointConfig(BaseModel):
    site_url: str = ""
    client_id: str = ""
    client_secret: str = ""
    target_folder: str = "Shared Documents/DBF_Master"

class GoogleDriveConfig(BaseModel):
    credentials_path: str = ""
    folder_id: str = ""

class AppConfig(BaseModel):
    last_root_path: str = ""
    export_destination: str = "local" # 'local', 'sharepoint', 'gdrive'
    local_export_path: str = ""
    sharepoint: SharepointConfig = Field(default_factory=SharepointConfig)
    gdrive: GoogleDriveConfig = Field(default_factory=GoogleDriveConfig)
    regex_gestion: str = r"\b(20[0-9]{2}|[0-9]{2})\b" # Default regex
