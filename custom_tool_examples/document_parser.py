import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

import PyPDF2
import pdfplumber # Preferred for text extraction

# For future OCR (placeholders for now)
# import pytesseract 
# from pdf2image import convert_from_path
# from PIL import Image # Pillow is a dependency for pytesseract & pdf2image

log = logging.getLogger(__name__)

class DocumentReadError(Exception):
    """Custom exception for errors during document reading/parsing."""
    pass

async def extract_text_from_pdf_with_libs(file_path: Path) -> str:
    """Extracts text from PDF using pdfplumber and PyPDF2."""
    text_content = ""
    # Try with pdfplumber
    try:
        with pdfplumber.open(file_path) as pdf:
            all_text_pages = [page.extract_text() for page in pdf.pages if page.extract_text()]
            text_content = "\n".join(filter(None, all_text_pages))
        if text_content.strip():
            log.info(f"Successfully extracted text using pdfplumber from {file_path} (Length: {len(text_content)}).")
            return text_content
        log.warning(f"pdfplumber extracted no significant text from {file_path}. Will try PyPDF2.")
    except Exception as e_plumber:
        log.warning(f"pdfplumber failed for {file_path}: {e_plumber}. Will try PyPDF2.")

    # Fallback to PyPDF2
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            all_text_pages = [page.extract_text() for page in reader.pages if page.extract_text()]
            text_content = "\n".join(filter(None, all_text_pages))
        if text_content.strip():
            log.info(f"Successfully extracted text using PyPDF2 from {file_path} (Length: {len(text_content)}).")
            return text_content
        log.warning(f"PyPDF2 also extracted no significant text from {file_path}.")
        return "" # Return empty if no text, smart_extract can decide to OCR
    except PyPDF2.errors.PdfReadError as e_core:
        log.error(f"PyPDF2 core PDF reading error for {file_path}: {e_core}. This might be a corrupted or non-standard PDF.")
        raise DocumentReadError(f"PyPDF2 could not read PDF structure: {e_core}") from e_core
    except Exception as e_pypdf2:
        log.error(f"Error extracting text with PyPDF2 from {file_path}: {e_pypdf2}", exc_info=True)
        raise DocumentReadError(f"Failed to extract text with PyPDF2: {e_pypdf2}") from e_pypdf2

async def ocr_pdf_placeholder(file_path: Path) -> str:
    """Placeholder for OCR logic."""
    log.warning(f"OCR PLACEHOLDER: OCR would be attempted for {file_path}. Returning empty string for now.")
    # TODO: Implement actual OCR logic here
    # 1. Convert PDF pages to images (e.g., using pdf2image)
    # try:
    #     images = convert_from_path(file_path)
    # except Exception as e_conv:
    #     log.error(f"pdf2image conversion failed for {file_path}: {e_conv}")
    #     return ""
    # 2. For each image, use pytesseract to OCR
    # all_ocr_text = []
    # for i, image in enumerate(images):
    #     try:
    #         page_text = pytesseract.image_to_string(image)
    #         if page_text:
    #             all_ocr_text.append(page_text)
    #     except Exception as e_ocr:
    #         log.error(f"pytesseract OCR failed for page {i} of {file_path}: {e_ocr}")
    # return "\n".join(all_ocr_text)
    return ""

async def smart_extract_text_from_pdf(file_path: Path) -> str:
    """
    Attempts to extract text from a PDF, first using direct text extraction libraries,
    then falling back to an OCR placeholder if direct extraction yields little text.
    """
    log.info(f"Smart extracting text from PDF: {file_path}")
    extracted_text = ""
    try:
        extracted_text = await extract_text_from_pdf_with_libs(file_path)
    except DocumentReadError as dre:
        log.warning(f"Library-based text extraction failed for {file_path}: {dre}. OCR might be needed or file is problematic.")
        # Proceed to OCR placeholder or re-raise depending on desired strictness

    # If direct extraction yields very little text, it might be an image-based PDF
    # Threshold for "very little text" can be adjusted
    if not extracted_text.strip() or len(extracted_text.strip()) < 50: # Example threshold
        log.info(f"Direct text extraction yielded minimal/no text from {file_path} (length: {len(extracted_text.strip())}). Attempting OCR (placeholder).")
        ocr_text = await ocr_pdf_placeholder(file_path)
        if ocr_text.strip():
            log.info(f"OCR placeholder for {file_path} returned text content.")
            return ocr_text # In future, this would be the actual OCRed text
        elif extracted_text.strip(): # OCR failed/placeholder, but some lib text existed
             log.info(f"OCR placeholder yielded no text for {file_path}, returning minimal text from libraries.")
             return extracted_text
        else: # Both failed
            raise DocumentReadError(f"All text extraction methods (libs and OCR placeholder) failed for {file_path}.")
    
    return extracted_text

async def get_file_content_as_text(file_id_or_path: str) -> Dict[str, Any]:
    """
    Main function for the COR engine to get text from a file.
    Currently assumes file_id_or_path is a direct file path.
    Future: Resolve file_id from a DB or object store.
    Future: Add support for other file types (DOCX, TXT, images with OCR).
    """
    log.info(f"COR Engine: Processing file_id_or_path: {file_id_or_path}")
    
    try:
        # For now, assume file_id_or_path is a resolvable file path string
        file_path = Path(file_id_or_path)

        if not file_path.exists():
            log.error(f"COR Engine: File not found at path: {file_path}")
            return {"status": "error", "message": f"File not found: {file_id_or_path}"}

        file_suffix = file_path.suffix.lower()

        if file_suffix == ".pdf":
            # Use the smart extractor that includes OCR placeholder
            text_content = await smart_extract_text_from_pdf(file_path)
            return {"status": "success", "text_content": text_content, "file_type": "pdf"}
        elif file_suffix in [".txt", ".md"]:
            try:
                text_content = file_path.read_text(encoding='utf-8')
                return {"status": "success", "text_content": text_content, "file_type": file_suffix}
            except Exception as e_txt:
                log.error(f"COR Engine: Error reading text file {file_path}: {e_txt}")
                return {"status": "error", "message": f"Could not read text file: {e_txt}"}
        # elif file_suffix in [".txt", ".md"]:
        #     text_content = file_path.read_text(encoding='utf-8')
        #     return {"status": "success", "text_content": text_content, "file_type": file_suffix}
        # TODO: Add DOCX support (e.g., using python-docx library)
        # TODO: Add image support with OCR (e.g., using pytesseract)
        else:
            log.warning(f"COR Engine: Unsupported file type '{file_suffix}' for: {file_id_or_path}")
            return {"status": "error", "message": f"Unsupported file type: {file_suffix}"}

    except DocumentReadError as dre:
        log.error(f"COR Engine: DocumentReadError for {file_id_or_path}: {dre}")
        return {"status": "error", "message": str(dre)}
    except Exception as e:
        log.exception(f"COR Engine: Unexpected error processing {file_id_or_path}: {e}")
        return {"status": "error", "message": f"Unexpected error processing file: {e}"}

# Example Usage (for testing this module directly)
# async def test_cor_engine():
#     # Create a dummy PDF file for testing (you'll need to create one manually or via code)
#     # dummy_pdf_path = Path("./dummy_invoice.pdf") 
#     # if not dummy_pdf_path.exists():
#     #     print(f"Please create a dummy PDF file at {dummy_pdf_path} for testing.")
#     #     return

#     # print(f"--- Testing PDF text extraction for: {dummy_pdf_path} ---")
#     # result = await get_file_content_as_text(str(dummy_pdf_path))
#     # print(f"Result: {result.get('status')}")
#     # if result.get('status') == 'success':
#     #     print(f"Extracted Text (first 500 chars):\n{result.get('text_content', '')[:500]}...")
#     # else:
#     #     print(f"Error: {result.get('message')}")
#     pass

# if __name__ == "__main__":
#     logging.basicConfig(level=logging.DEBUG) # Set to DEBUG to see page-level extraction logs
#     # asyncio.run(test_cor_engine()) 