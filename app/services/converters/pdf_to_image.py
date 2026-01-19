"""
PDF to Image Converter
Converts PDF files to images using PyMuPDF (fitz) - no external dependencies
"""
from pathlib import Path
from typing import Tuple
import io
from PIL import Image
import fitz  # PyMuPDF
from .base import BaseConverter


class PdfToImageConverter(BaseConverter):
    """Convert PDF to Image (PNG/JPG) format"""
    
    async def convert(self, input_path: Path, output_path: Path) -> Tuple[bool, str]:
        """
        Convert PDF to images (all pages)
        
        Args:
            input_path: Path to input PDF file
            output_path: Path to output file (will be a ZIP for multi-page PDFs)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Validate input
            if not self.validate_input(input_path):
                return False, f"Input file not found or invalid: {input_path}"
            
            # Open PDF with PyMuPDF
            pdf_document = fitz.open(str(input_path))
            
            if pdf_document.page_count == 0:
                pdf_document.close()
                return False, "No pages found in PDF"
            
            page_count = pdf_document.page_count
            
            # Determine output format
            output_format = output_path.suffix.lstrip('.').upper()
            if output_format == 'JPG':
                output_format = 'JPEG'
            
            # Set resolution (2.0 = 144 DPI, good quality)
            zoom = 2.0
            mat = fitz.Matrix(zoom, zoom)
            
            # If single page, save directly
            if page_count == 1:
                page = pdf_document[0]
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                # Save in requested format
                if output_format == 'PNG':
                    img.save(str(output_path), 'PNG')
                elif output_format in ['JPG', 'JPEG']:
                    if img.mode == 'RGBA':
                        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                        rgb_img.paste(img, mask=img.split()[3])
                        rgb_img.save(str(output_path), 'JPEG', quality=95)
                    else:
                        img.save(str(output_path), 'JPEG', quality=95)
                else:
                    img.save(str(output_path), output_format)
                
                pdf_document.close()
                
                if not output_path.exists():
                    return False, "Conversion failed: output file not created"
                
                return True, "PDF converted to image successfully (1 page)"
            
            # Multi-page PDF - create ZIP with all pages
            else:
                import zipfile
                import tempfile
                
                # Create temporary directory for images
                temp_dir = Path(tempfile.mkdtemp())
                image_files = []
                
                try:
                    # Convert each page
                    for page_num in range(page_count):
                        page = pdf_document[page_num]
                        pix = page.get_pixmap(matrix=mat)
                        
                        # Convert to PIL Image
                        img_data = pix.tobytes("png")
                        img = Image.open(io.BytesIO(img_data))
                        
                        # Save page image
                        page_filename = f"page_{page_num + 1:03d}.{output_format.lower()}"
                        page_path = temp_dir / page_filename
                        
                        if output_format == 'PNG':
                            img.save(str(page_path), 'PNG')
                        elif output_format in ['JPG', 'JPEG']:
                            if img.mode == 'RGBA':
                                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                                rgb_img.paste(img, mask=img.split()[3])
                                rgb_img.save(str(page_path), 'JPEG', quality=95)
                            else:
                                img.save(str(page_path), 'JPEG', quality=95)
                        else:
                            img.save(str(page_path), output_format)
                        
                        image_files.append(page_path)
                    
                    pdf_document.close()
                    
                    # Create ZIP file
                    zip_path = output_path.with_suffix('.zip')
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for img_file in image_files:
                            zipf.write(img_file, img_file.name)
                    
                    # Clean up temporary files
                    for img_file in image_files:
                        img_file.unlink()
                    temp_dir.rmdir()
                    
                    # Update output_path to point to ZIP
                    if zip_path != output_path:
                        if output_path.exists():
                            output_path.unlink()
                        # Note: We return zip_path info but keep the file as .zip
                    
                    if not zip_path.exists():
                        return False, "Conversion failed: ZIP file not created"
                    
                    return True, f"PDF converted to images successfully ({page_count} pages in ZIP)"
                
                except Exception as e:
                    # Clean up on error
                    pdf_document.close()
                    for img_file in image_files:
                        if img_file.exists():
                            img_file.unlink()
                    if temp_dir.exists():
                        temp_dir.rmdir()
                    raise e
            
        except Exception as e:
            return False, f"PDF to image conversion failed: {str(e)}"


