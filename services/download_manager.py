import logging
import uuid
import httpx
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DownloadManager:
    """
    Generic media download manager.
    Downloads files, handles retries, validates formats, and manages temporary storage.
    Agnostic to source platforms (no TikTok logic here).
    """

    def __init__(self, temp_dir: str | Path = "temp"):
        # Make path absolute relative to project root (2 levels up from services if imported there, 
        # but let's be safe and resolve relative to this file's grand-parent)
        base_dir = Path(__file__).resolve().parent.parent
        self.temp_dir = base_dir / str(temp_dir)
        
        # Ensure temp dir exists
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def _format_success(self, data: Any) -> Dict[str, Any]:
        return {"success": True, "data": data}

    def _format_error(self, message: str) -> Dict[str, Any]:
        return {"success": False, "error": message, "data": None}

    def validate_video(self, file_path: Path) -> Dict[str, Any]:
        """Validates that the downloaded file is a valid non-empty mp4."""
        logger.info("Validating video")
        try:
            if not file_path.exists():
                return self._format_error("File does not exist")
                
            if file_path.suffix.lower() != ".mp4":
                return self._format_error(f"Invalid extension: {file_path.suffix}. Expected .mp4")
                
            size = file_path.stat().st_size
            if size == 0:
                return self._format_error("File is empty (0 bytes)")
                
            # Basic readability check
            with open(file_path, 'rb') as f:
                header = f.read(10)
                if len(header) == 0:
                    return self._format_error("File cannot be read")
                    
            return self._format_success({"size": size, "path": str(file_path)})
            
        except Exception as e:
            return self._format_error(f"Validation exception: {e}")

    def download(self, download_url: str, filename: str = "") -> Dict[str, Any]:
        """Download URL to temp directory with retries."""
        if not download_url:
            return self._format_error("Download URL is empty")
            
        if not filename:
            filename = f"media_{uuid.uuid4().hex[:8]}.mp4"
            
        # Ensure filename ends with mp4 for safety
        if not filename.endswith(".mp4"):
            filename += ".mp4"
            
        file_path = self.temp_dir / filename
        
        max_retries = 3
        timeout = 60.0  # 60s timeout for stream connection

        for attempt in range(1, max_retries + 1):
            logger.info(f"Starting download (Attempt {attempt}/{max_retries})")
            logger.info(f"Saving file to {filename}")
            
            try:
                with httpx.stream("GET", download_url, timeout=timeout, follow_redirects=True) as response:
                    response.raise_for_status()
                    
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_bytes(chunk_size=8192):
                            f.write(chunk)
                
                # Validation
                val_res = self.validate_video(file_path)
                if not val_res["success"]:
                    logger.warning(f"Validation failed: {val_res['error']}")
                    # Delete invalid file
                    if file_path.exists():
                        file_path.unlink()
                    continue # Retry on bad file
                    
                logger.info("Download completed")
                
                return {
                    "success": True,
                    "path": str(file_path),
                    "filename": filename,
                    "size": val_res["data"]["size"]
                }
                
            except Exception as e:
                logger.warning(f"Download error on attempt {attempt}: {e}")
                if file_path.exists():
                    file_path.unlink()
                    
                if attempt == max_retries:
                    return self._format_error(f"Failed after {max_retries} attempts: {e}")

    def cleanup(self) -> Dict[str, Any]:
        """Remove all video files from temp directory."""
        logger.info(f"Cleaning up {self.temp_dir}")
        deleted_count = 0
        try:
            if not self.temp_dir.exists():
                return self._format_success({"deleted_count": 0})
                
            for file_path in self.temp_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() == ".mp4":
                    try:
                        file_path.unlink()
                        deleted_count += 1
                    except Exception as e:
                        logger.warning(f"Could not delete {file_path.name}: {e}")
                        
            return self._format_success({"deleted_count": deleted_count})
        except Exception as e:
            return self._format_error(f"Cleanup error: {e}")
