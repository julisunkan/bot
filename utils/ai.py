import os
import google.generativeai as genai

class AIAssistant:
    def __init__(self):
        self.api_key = os.environ.get('GEMINI_API_KEY')
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
    
    def is_available(self):
        return self.model is not None
    
    def generate_bot_response(self, user_message, context=""):
        if not self.is_available():
            return "AI features require a Gemini API key. Please configure it in settings."
        
        try:
            prompt = f"""You are a helpful Telegram bot assistant. 
Context: {context}
User message: {user_message}

Generate a friendly, concise response (max 2-3 sentences):"""
            
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"AI generation failed: {str(e)}"
    
    def suggest_command_response(self, command_name, command_description=""):
        if not self.is_available():
            return self._get_default_response(command_name)
        
        try:
            prompt = f"""Create a friendly Telegram bot response for the command /{command_name}.
Description: {command_description if command_description else 'No description provided'}

Generate a helpful response message (2-3 sentences max):"""
            
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return self._get_default_response(command_name)
    
    def _get_default_response(self, command_name):
        defaults = {
            'start': 'Welcome! I\'m here to help you. Use /help to see available commands.',
            'help': 'Here are the available commands: /start - Get started, /help - Show this message',
            'claim': 'You have successfully claimed your reward!',
            'price': 'Current price information is being fetched...',
            'balance': 'Your current balance is being calculated...',
            'airdrop': 'Airdrop participation recorded! Stay tuned for updates.',
            'verify': 'Verification process initiated. Please follow the instructions.'
        }
        return defaults.get(command_name.lower(), f'Command /{command_name} executed successfully!')
    
    def detect_intent(self, message):
        intents = {
            'price': ['price', 'cost', 'how much', 'value', 'worth'],
            'buy': ['buy', 'purchase', 'get', 'acquire'],
            'claim': ['claim', 'reward', 'airdrop', 'free'],
            'help': ['help', 'support', 'how to', 'guide'],
            'balance': ['balance', 'wallet', 'funds', 'money']
        }
        
        message_lower = message.lower()
        for intent, keywords in intents.items():
            if any(keyword in message_lower for keyword in keywords):
                return intent
        
        return 'general'
    
    def generate_bot_config(self, bot_type, bot_description=""):
        if not self.is_available():
            return self._get_default_config(bot_type)
        
        try:
            prompt = f"""Generate a JSON configuration for a {bot_type} Telegram bot.
Description: {bot_description}

Include commands, responses, and basic settings. Return valid JSON only:"""
            
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return self._get_default_config(bot_type)
    
    def _get_default_config(self, bot_type):
        configs = {
            'airdrop': {
                'commands': [
                    {'command': 'start', 'response': 'Welcome to the Airdrop Bot!'},
                    {'command': 'claim', 'response': 'Airdrop claimed successfully!'},
                    {'command': 'balance', 'response': 'Your token balance: 0'}
                ]
            },
            'payment': {
                'commands': [
                    {'command': 'start', 'response': 'Welcome to the Payment Bot!'},
                    {'command': 'pay', 'response': 'Payment initiated. Please confirm.'},
                    {'command': 'status', 'response': 'Checking payment status...'}
                ]
            }
        }
        return configs.get(bot_type, {'commands': []})
