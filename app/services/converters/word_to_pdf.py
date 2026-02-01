"""
Word to PDF Converter
Converts Word documents to PDF using LibreOffice headless mode
"""
import subprocess
import os
import shutil
from pathlib import Path
from typing import Tuple
from app.core.config import settings
from .base import BaseConverter


class WordToPdfConverter(BaseConverter):
    """Convert Word (DOCX/DOC) to PDF format using LibreOffice"""
    
    def __init__(self):
        self.libreoffice_path = settings.LIBREOFFICE_PATH
    
    async def convert(self, input_path: Path, output_path: Path) -> Tuple[bool, str]:
        """
        Convert Word document to PDF using LibreOffice
        
        Args:
            input_path: Path to input Word file
            output_path: Path to output PDF file
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Validate input
            if not self.validate_input(input_path):
                return False, f"Input file not found or invalid: {input_path}"
            
            # Get output directory
            output_dir = output_path.parent
            
            # Try to find LibreOffice in PATH first, then fall back to configured path
            libreoffice_cmd = shutil.which("soffice")
            
            if not libreoffice_cmd:
                # Check configured path
                if os.path.exists(self.libreoffice_path):
                    libreoffice_cmd = self.libreoffice_path
                else:
                    return False, f"LibreOffice not found. Please install LibreOffice or set LIBREOFFICE_PATH."
            
            # LibreOffice command
            # --headless: run without GUI
            # --convert-to pdf: output format
            # --outdir: output directory
            command = [
                libreoffice_cmd,
                "--headless",
                "--convert-to", "pdf",
                "--outdir", str(output_dir),
                str(input_path)
            ]
            
            # Execute conversion
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            # LibreOffice creates file with same name but .pdf extension
            # Need to rename it to our expected output path
            expected_output = output_dir / f"{input_path.stem}.pdf"
            
            if expected_output.exists() and expected_output != output_path:
                expected_output.rename(output_path)
            
            # Check if conversion succeeded
            if output_path.exists():
                return True, "Word converted to PDF successfully"
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
                return False, f"Word to PDF conversion failed: {error_msg}"
            
        except subprocess.TimeoutExpired:
            return False, "Word to PDF conversion timed out (>60s)"
        except Exception as e:
            return False, f"Word to PDF conversion failed: {str(e)}"
