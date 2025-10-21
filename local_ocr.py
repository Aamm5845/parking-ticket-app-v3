#!/usr/bin/env python3
"""
Local OCR solution as fallback for Google Cloud Vision issues
"""

def extract_ticket_info_local(image_content):
    """
    Local OCR extraction using pytesseract (if available)
    """
    try:
        import pytesseract
        from PIL import Image
        import io
        import re
        
        # Convert image content to PIL Image
        image = Image.open(io.BytesIO(image_content))
        
        # Extract text using Tesseract
        raw_text = pytesseract.image_to_string(image)
        
        # Parse the text for ticket info
        return parse_ticket_text(raw_text)
        
    except ImportError:
        return {"error": "pytesseract not installed"}
    except Exception as e:
        return {"error": str(e)}

def parse_ticket_text(raw_text):
    """
    Parse extracted text for ticket information
    """
    ticket_number, space_number, extracted_date, extracted_time = "", "", "", ""
    
    # Look for ticket number (9 digits)
    ticket_match = re.search(r'\b(\d{3})\s*(\d{3})\s*(\d{3})\b', raw_text)
    if ticket_match:
        ticket_number = "".join(ticket_match.groups())
    
    # Look for space number (PL followed by digits)
    space_match = re.search(r'(PL\d+)', raw_text, re.IGNORECASE)
    if space_match:
        space_number = space_match.group(1).upper()
    
    # Look for date and time
    date_time_match = (
        re.search(r'au\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})', raw_text, re.IGNORECASE)
        or re.search(r'Date\s+de\s+signification:\s*(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})', raw_text, re.IGNORECASE)
        or re.search(r'\b(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\b', raw_text)
    )
    if date_time_match:
        extracted_date, extracted_time = date_time_match.groups()
    
    return {
        "success": True,
        "ticket_number": ticket_number,
        "space": space_number,
        "date": extracted_date,
        "start_time": extracted_time,
        "raw_text": raw_text
    }

def simple_ocr_fallback(image_content):
    """
    Simple pattern-based OCR fallback
    Returns mock data for development
    """
    import random
    
    # Return mock data for development/testing
    return {
        "success": True,
        "ticket_number": f"{random.randint(100000000, 999999999)}",
        "space": f"PL{random.randint(100, 999)}",
        "date": "2024-01-15",
        "start_time": "10:30",
        "message": "Mock data - OCR unavailable"
    }
