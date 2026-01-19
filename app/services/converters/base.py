"""
Base Converter Interface
Abstract base class for all file converters
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple


class BaseConverter(ABC):
    """Abstract base class for file converters"""
    
    @abstractmethod
    async def convert(self, input_path: Path, output_path: Path) -> Tuple[bool, str]:
        """
        Convert file from input format to output format
        
        Args:
            input_path: Path to input file
            output_path: Path to output file
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        pass
    
    def validate_input(self, input_path: Path) -> bool:
        """
        Validate input file exists and is readable
        
        Args:
            input_path: Path to input file
            
        Returns:
            True if valid, False otherwise
        """
        if not input_path.exists():
            return False
        
        if not input_path.is_file():
            return False
        
        return True
