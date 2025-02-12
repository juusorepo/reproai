from pdfminer.high_level import extract_text
from pathlib import Path
from typing import Optional

class PDFExtractor:
    # Map of problematic Unicode characters to their ASCII equivalents
    CHAR_REPLACEMENTS = {
        '\u2018': "'",  # Left single quote
        '\u2019': "'",  # Right single quote
        '\u201c': '"',  # Left double quote
        '\u201d': '"',  # Right double quote
        '\u2013': '-',  # En dash
        '\u2014': '--', # Em dash
        '\u2026': '...', # Ellipsis
        '\ufb01': 'fi', # fi ligature
        '\ufb02': 'fl', # fl ligature
        '\u00a0': ' ',  # Non-breaking space
    }

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
            
            # Extract text with PDFMiner
            text = extract_text(pdf_path)
            
            # Replace problematic characters with ASCII equivalents
            for unicode_char, ascii_char in PDFExtractor.CHAR_REPLACEMENTS.items():
                text = text.replace(unicode_char, ascii_char)
            
            # Handle any remaining non-ASCII characters by replacing them with '?'
            text = text.encode('ascii', errors='replace').decode('ascii')
            
            if max_chars is not None:
                text = text[:max_chars]
                
            return text.strip()
            
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
