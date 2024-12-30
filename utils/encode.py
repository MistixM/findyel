from urllib.parse import quote

def encode_text(text: str):
    return quote(text)
