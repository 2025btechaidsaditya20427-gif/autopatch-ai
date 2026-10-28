from buggy_app import is_palindrome, calculate_cart_total, is_valid_password

def test_palindrome_with_spaces_and_caps():
    assert is_palindrome("Race car") is True
    assert is_palindrome("hello") is False

def test_cart_total_missing_qty_and_negative():
    cart = [
        {"name": "Laptop", "price": 50000, "qty": 1},
        {"name": "Mouse", "price": 500},  # 'qty' missing hai, default 1 maanna chahiye
        {"name": "GlitchItem", "price": -200, "qty": 2}  # Negative price ignore hona chahiye
    ]
    assert calculate_cart_total(cart) == 50500

def test_password_validation():
    assert is_valid_password("Pass1234") is True   # Exact 8 chars + has digit
    assert is_valid_password("onlyletters") is False  # No digit
    assert is_valid_password(" a1 ") is False      # Too short