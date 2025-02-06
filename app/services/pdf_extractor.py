from pdfminer.high_level import extract_text
from pathlib import Path
from typing import Optional

class PDFExtractor:
    @staticmethod
    def extract_text(pdf_path: str, max_chars: Optional[int] = None) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            max_chars: Maximum number of characters to extract (None for all)
            
        Returns:
            Extracted text from the PDF
        """
        try:
            if not Path(pdf_path).exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            text = extract_text(pdf_path)
            
            if max_chars is not None:
                text = text[:max_chars]
                
            return text.strip()
            
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
