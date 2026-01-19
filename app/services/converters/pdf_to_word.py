"""
PDF to Word Converter
Converts PDF files to Word documents using pdf2docx
"""
from pathlib import Path
from typing import Tuple
from pdf2docx import Converter
from .base import BaseConverter


class PdfToWordConverter(BaseConverter):
    """Convert PDF to Word (DOCX) format"""
    
    async def convert(self, input_path: Path, output_path: Path) -> Tuple[bool, str]:
        """
        Convert PDF to DOCX
        
        Args:
            input_path: Path to input PDF file
            output_path: Path to output DOCX file
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Validate input
            if not self.validate_input(input_path):
                return False, f"Input file not found or invalid: {input_path}"
            
            # Convert PDF to DOCX
            cv = Converter(str(input_path))
            cv.convert(str(output_path))
            cv.close()
            
            # Verify output was created
            if not output_path.exists():
                return False, "Conversion failed: output file not created"
            
            return True, "PDF converted to Word successfully"
            
        except Exception as e:
            return False, f"PDF to Word conversion failed: {str(e)}"
