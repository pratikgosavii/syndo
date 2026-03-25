import os
from playwright.sync_api import sync_playwright
from django.conf import settings

def html_to_pdf_local(html_content, options=None):
    """
    Converts HTML content to a PDF buffer using a local headless Chromium browser (Playwright).
    This ensures an exact match to browser rendering.
    """
    if options is None:
        options = {}

    # Standard A4/Margins or Thermal width (matching html2pdf.app logic)
    # Note: options['pageSize'] -> playwright format 'A4', 'Letter', etc.
    # options['margin'] -> playwright {'top': '1cm', 'bottom': '1cm', etc.}
    
    # Defaults
    format_type = options.get('pageSize', 'A4')
    margin = options.get('margin', '1cm')
    if isinstance(margin, str):
        margin = {'top': margin, 'bottom': margin, 'left': margin, 'right': margin}

    # Handle thermal (width/height in pixels)
    width = options.get('width')
    height = options.get('height')

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            
            # Use 'wait_until' load/networkidle to ensure images (base64) are ready
            page.set_content(html_content, wait_until="load")
            
            # Add printBackground to ensure colors/images render correctly
            pdf_bytes = page.pdf(
                print_background=True,
                format=format_type if not width else None,
                width=f"{width}px" if width else None,
                height=f"{height}px" if height else None,
                margin=margin,
            )
            return pdf_bytes
        finally:
            browser.close()
