import urllib.parse

def string_to_url(text):
    """
    Convert a string to URL-safe format.
    
    Args:
        text (str): The text to convert
        
    Returns:
        str: URL-safe string
    """
    if not text:
        return ""
    
    # Clean and encode the text properly
    text = text.strip().lower()
    # Replace spaces with hyphens for Internshala URL format
    text = text.replace(' ', '-')
    # URL encode any special characters
    text = urllib.parse.quote(text, safe='-')
    
    return text
