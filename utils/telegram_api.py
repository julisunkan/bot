import requests
import json

class TelegramAPI:
    def __init__(self, bot_token=None):
        self.bot_token = bot_token
        self.base_url = f'https://api.telegram.org/bot{bot_token}' if bot_token else None

    def set_token(self, bot_token):
        self.bot_token = bot_token
        self.base_url = f'https://api.telegram.org/bot{bot_token}'

    def verify_token(self, bot_token):
        try:
            url = f'https://api.telegram.org/bot{bot_token}/getMe'
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return {
                        'valid': True,
                        'bot_info': data.get('result', {})
                    }
            return {'valid': False, 'error': 'Invalid token'}
        except Exception as e:
            return {'valid': False, 'error': str(e)}

    def get_bot_info(self):
        if not self.base_url:
            return None

        try:
            response = requests.get(f'{self.base_url}/getMe', timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return data.get('result')
            return None
        except Exception as e:
            print(f"Error getting bot info: {e}")
            return None

    def send_message(self, chat_id, text, parse_mode=None, reply_markup=None):
        url = f"{self.base_url}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': text
        }

        if parse_mode:
            data['parse_mode'] = parse_mode

        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)

        try:
            response = requests.post(url, json=data, timeout=10)
            return response.json()
        except Exception as e:
            print(f"Error sending message: {e}")
            return None

    def set_webhook(self, webhook_url):
        """Set webhook for the bot"""
        url = f"{self.base_url}/setWebhook"
        data = {'url': webhook_url}

        try:
            response = requests.post(url, json=data, timeout=10)
            return response.json()
        except Exception as e:
            print(f"Error setting webhook: {e}")
            return None

    def get_me(self):
        """Get bot information"""
        url = f"{self.base_url}/getMe"

        try:
            response = requests.get(url, timeout=10)
            return response.json()
        except Exception as e:
            print(f"Error getting bot info: {e}")
            return None

    def delete_webhook(self):
        if not self.base_url:
            return None

        try:
            response = requests.post(f'{self.base_url}/deleteWebhook', timeout=10)
            return response.json()
        except Exception as e:
            print(f"Error deleting webhook: {e}")
            return None

    def get_updates(self, offset=None, limit=100):
        if not self.base_url:
            return None

        try:
            params = {'limit': limit}
            if offset:
                params['offset'] = offset

            response = requests.get(f'{self.base_url}/getUpdates', params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return data.get('result', [])
            return []
        except Exception as e:
            print(f"Error getting updates: {e}")
            return []

    def set_bot_commands(self, commands):
        """Set bot menu commands"""
        if not self.base_url:
            return None

        try:
            url = f"{self.base_url}/setMyCommands"
            data = {'commands': commands}
            response = requests.post(url, json=data, timeout=10)
            return response.json()
        except Exception as e:
            print(f"Error setting bot commands: {e}")
            return None

    def answer_callback_query(self, callback_query_id, text=None):
        """Answer callback query from inline buttons"""
        if not self.base_url:
            return None

        try:
            url = f"{self.base_url}/answerCallbackQuery"
            data = {'callback_query_id': callback_query_id}
            if text:
                data['text'] = text
            response = requests.post(url, json=data, timeout=10)
            return response.json()
        except Exception as e:
            print(f"Error answering callback: {e}")
            return None