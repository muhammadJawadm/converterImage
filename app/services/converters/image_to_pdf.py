"""
Image to PDF Converter
Converts image files to PDF using img2pdf
"""
from pathlib import Path
from typing import Tuple
import img2pdf
from .base import BaseConverter


class ImageToPdfConverter(BaseConverter):
    """Convert Image (JPG, PNG) to PDF format"""
    
    async def convert(self, input_path: Path, output_path: Path) -> Tuple[bool, str]:
        """
        Convert image to PDF
        
        Args:
            input_path: Path to input image file
            output_path: Path to output PDF file
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Validate input
            if not self.validate_input(input_path):
                return False, f"Input file not found or invalid: {input_path}"
            
            # Convert image to PDF
            with open(str(output_path), "wb") as f:
                f.write(img2pdf.convert(str(input_path)))
            
            # Verify output was created
            if not output_path.exists():
                return False, "Conversion failed: output file not created"
            
            return True, "Image converted to PDF successfully"
            
        except Exception as e:
            return False, f"Image to PDF conversion failed: {str(e)}"
