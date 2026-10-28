def is_palindrome(text):
    cleaned = ''.join(c.lower() for c in text if c.isalnum())
    return cleaned == cleaned[::-1]

def calculate_cart_total(cart_items):
    total = 0
    for item in cart_items:
        price = item.get("price", 0)
        qty = item.get("qty", 1)
        if price >= 0:
            total += price * qty
    return total

def is_valid_password(password):
    return len(password) >= 8 and any(c.isdigit() for c in password)