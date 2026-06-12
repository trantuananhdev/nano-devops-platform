"""PDF text extraction service using PyMuPDF (fitz)."""

import os
from pathlib import Path
from typing import List, Tuple

import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_path: str | Path) -> Tuple[str, int]:
    """
    Extract text from a PDF file.
    
    Returns:
        Tuple of (extracted_text, page_count)
    """
    doc = fitz.open(pdf_path)
    text_parts = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text_parts.append(f"--- Page {page_num + 1} ---\n")
        text_parts.append(page.get_text())
    
    full_text = "\n".join(text_parts)
    doc.close()
    
    return full_text, len(doc)


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> List[str]:
    """
    Split text into overlapping chunks for vector embedding.
    
    Args:
        text: Full text to chunk
        chunk_size: Maximum tokens per chunk (approximate by chars)
        overlap: Overlap between chunks
    
    Returns:
        List of text chunks
    """
    # Simple chunking by character count
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + chunk_size, text_len)
        
        # Try to find a natural break (newline, period) near the end
        if end < text_len:
            # Look for break points in the last 100 chars
            look_back = min(100, end - start)
            break_pos = text.rfind('\n', start, end)
            if break_pos == -1:
                break_pos = text.rfind('. ', start, end)
            if break_pos != -1 and break_pos > start:
                end = break_pos + 1
        
        chunks.append(text[start:end].strip())
        start = end - overlap if (end - overlap) > start else end
    
    # Filter out empty chunks
    return [chunk for chunk in chunks if chunk.strip()]
