import hashlib
import hmac
import json
from urllib.parse import parse_qsl

def validate_telegram_webapp_data(init_data, bot_token):
    try:
        parsed_data = dict(parse_qsl(init_data))
        
        if 'hash' not in parsed_data:
            return None
        
        received_hash = parsed_data.pop('hash')
        
        data_check_string = '\n'.join(
            f"{k}={v}" for k, v in sorted(parsed_data.items())
        )
        
        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode(),
            hashlib.sha256
        ).digest()
        
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if calculated_hash != received_hash:
            return None
        
        user_data = None
        if 'user' in parsed_data:
            user_data = json.loads(parsed_data['user'])
        
        return {
            'valid': True,
            'user': user_data,
            'parsed_data': parsed_data
        }
    except Exception as e:
        print(f"Telegram auth validation error: {e}")
        return None
