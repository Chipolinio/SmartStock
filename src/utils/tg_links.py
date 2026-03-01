import base64

def generate_tg_auth_link(email: str, bot_username: str) -> str:
    token = base64.b64encode(email.encode('utf-8')).decode('utf-8')
    return f"https://t.me/{bot_username}?start={token}"