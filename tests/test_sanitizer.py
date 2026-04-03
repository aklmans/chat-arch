from chatarch.core.sanitizer import sanitize_text

def test_sanitize_email():
    text = "My email is test@example.com, please contact me."
    sanitized = sanitize_text(text)
    assert "test@example.com" not in sanitized
    assert "[EMAIL]" in sanitized

def test_sanitize_phone():
    text = "Call me at 13812345678."
    sanitized = sanitize_text(text)
    assert "13812345678" not in sanitized
    assert "[PHONE]" in sanitized

def test_sanitize_ipv4():
    text = "The server is at 192.168.1.1."
    sanitized = sanitize_text(text)
    assert "192.168.1.1" not in sanitized
    assert "[IPV4]" in sanitized

def test_sanitize_api_key():
    text = "Here is my key: sk-abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKL"
    sanitized = sanitize_text(text)
    assert "sk-" not in sanitized
    assert "[API_KEY]" in sanitized
