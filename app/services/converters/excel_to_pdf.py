"""
Excel to PDF Converter
Converts Excel spreadsheets to PDF using LibreOffice headless mode
"""
import subprocess
import shutil
import os
from pathlib import Path
from typing import Tuple
from app.core.config import settings
from .base import BaseConverter


class ExcelToPdfConverter(BaseConverter):
    """Convert Excel (XLSX/XLS) to PDF format using LibreOffice"""
    
    def __init__(self):
        self.libreoffice_path = settings.LIBREOFFICE_PATH
    
    async def convert(self, input_path: Path, output_path: Path) -> Tuple[bool, str]:
        """
        Convert Excel spreadsheet to PDF using LibreOffice
        
        Args:
            input_path: Path to input Excel file
            output_path: Path to output PDF file
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Validate input
            if not self.validate_input(input_path):
                return False, f"Input file not found or invalid: {input_path}"
            
            # Check if LibreOffice is available
            if not os.path.exists(self.libreoffice_path):
                return False, f"LibreOffice not found at {self.libreoffice_path}. Please install LibreOffice."
            
            # Get output directory
            output_dir = output_path.parent
            
            def get_libreoffice_cmd():
                cmd = shutil.which("soffice")
                if not cmd:
                    raise RuntimeError("LibreOffice (soffice) not found in PATH")
                return cmd


            # LibreOffice command for Excel to PDF
            command = [
                get_libreoffice_cmd(),
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
                timeout=60
            )
            
            # Rename output file if needed
            expected_output = output_dir / f"{input_path.stem}.pdf"
            
            if expected_output.exists() and expected_output != output_path:
                expected_output.rename(output_path)
            
            # Check if conversion succeeded
            if output_path.exists():
                return True, "Excel converted to PDF successfully"
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
                return False, f"Excel to PDF conversion failed: {error_msg}"
            
        except subprocess.TimeoutExpired:
            return False, "Excel to PDF conversion timed out (>60s)"
        except Exception as e:
            return False, f"Excel to PDF conversion failed: {str(e)}"
