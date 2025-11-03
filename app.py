import os
import json
import secrets
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from werkzeug.utils import secure_filename
from utils.database import Database
from utils.ai import AIAssistant
from utils.crypto import CryptoAPI
from utils.telegram_api import TelegramAPI

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', secrets.token_hex(32))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db = Database()
ai_assistant = AIAssistant()
crypto_api = CryptoAPI()

def init_templates():
    templates_dir = 'templates_library'
    template_files = {
        'airdrop.json': ('Airdrop Bot', 'Crypto airdrop distribution bot with claim and referral system', 'crypto'),
        'payment.json': ('Payment Bot', 'Cryptocurrency payment processing bot with transaction tracking', 'crypto'),
        'referral.json': ('Referral Bot', 'Referral tracking system with rewards and leaderboard', 'marketing'),
        'nft_verification.json': ('NFT Verification Bot', 'Verify NFT ownership and grant access to exclusive communities', 'web3'),
        'ai_chatbot.json': ('AI Chat Bot', 'Intelligent AI-powered chatbot for customer support and conversations', 'ai'),
        'webapp_creator.json': ('Web App Creator Bot', 'Create and deploy interactive web applications directly from Telegram', 'webapp'),
        'game_creator.json': ('Game Creator Bot', 'Build and play interactive games directly in Telegram', 'game'),
        'coin_mining.json': ('Tap-to-Earn Mining Bot', 'Create viral tap-to-earn coin mining games like Notcoin, Hamster Kombat', 'mining')
    }
    
    existing_templates = db.get_all_templates()
    if len(existing_templates) == 0:
        for filename, (title, description, category) in template_files.items():
            db.add_template(title, description, category, filename)

init_templates()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            return render_template('login.html', error='Username and password required', mode='register')
        
        if len(password) < 6:
            return render_template('login.html', error='Password must be at least 6 characters', mode='register')
        
        user_id, referral_code = db.create_user(username, password)
        
        if user_id:
            session['user_id'] = user_id
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Username already exists', mode='register')
    
    return render_template('login.html', mode='register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        user = db.verify_user(username, password)
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials', mode='login')
    
    return render_template('login.html', mode='login')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/generate-account')
def generate_account():
    username = f'user_{secrets.token_hex(4)}'
    password = secrets.token_urlsafe(12)
    
    user_id, referral_code = db.create_user(username, password)
    
    if user_id:
        session['user_id'] = user_id
        session['username'] = username
        session['temp_password'] = password
        return redirect(url_for('dashboard'))
    
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = db.get_user(session['user_id'])
    bots = db.get_user_bots(session['user_id'])
    analytics = db.get_analytics_summary(session['user_id'])
    
    crypto_prices = crypto_api.get_multiple_prices(['bitcoin', 'ethereum', 'binancecoin'])
    
    temp_password = session.pop('temp_password', None)
    
    return render_template('dashboard.html',
                         user=user,
                         bots=bots,
                         analytics=analytics,
                         crypto_prices=crypto_prices,
                         temp_password=temp_password)

@app.route('/create-bot', methods=['GET', 'POST'])
@login_required
def create_bot():
    if request.method == 'POST':
        bot_name = request.form.get('bot_name', '').strip()
        bot_token = request.form.get('bot_token', '').strip()
        bot_type = request.form.get('bot_type', 'telegram')
        
        if not bot_name:
            return render_template('create_bot.html', error='Bot name is required')
        
        # Only require token for telegram bots
        if bot_type == 'telegram' and not bot_token:
            return render_template('create_bot.html', error='Bot token is required for Telegram bots')
        
        user = db.get_user(session['user_id'])
        user_bots = db.get_user_bots(session['user_id'])
        
        if user['plan'] == 'free' and len(user_bots) >= 1:
            return render_template('create_bot.html', error='Free plan allows only 1 bot. Upgrade to Pro for unlimited bots.')
        
        # Verify telegram bot token if provided
        if bot_type == 'telegram':
            telegram_api = TelegramAPI()
            verification = telegram_api.verify_token(bot_token)
            
            if not verification['valid']:
                return render_template('create_bot.html', error='Invalid Telegram bot token')
        
        bot_config = json.dumps({
            'commands': [],
            'bot_type': bot_type,
            'created_at': datetime.now().isoformat()
        })
        
        bot_id = db.create_bot(session['user_id'], bot_name, bot_token, bot_config, bot_type)
        
        return redirect(url_for('bot_detail', bot_id=bot_id))
    
    return render_template('create_bot.html')

@app.route('/bot/<int:bot_id>')
@login_required
def bot_detail(bot_id):
    bot = db.get_bot(bot_id)
    
    if not bot or bot['user_id'] != session['user_id']:
        return redirect(url_for('dashboard'))
    
    commands = db.get_bot_commands(bot_id)
    
    try:
        bot_config = json.loads(bot['bot_config']) if bot['bot_config'] else {}
    except:
        bot_config = {}
    
    return render_template('bot_detail.html', bot=bot, commands=commands, bot_config=bot_config)

@app.route('/bot/<int:bot_id>/add-command', methods=['POST'])
@login_required
def add_command(bot_id):
    bot = db.get_bot(bot_id)
    
    if not bot or bot['user_id'] != session['user_id']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    command = request.form.get('command', '').strip().lower()
    response_type = request.form.get('response_type', 'text')
    response_content = request.form.get('response_content', '').strip()
    
    if not command or not response_content:
        return jsonify({'success': False, 'error': 'Command and response required'}), 400
    
    db.add_bot_command(bot_id, command, response_type, response_content)
    
    return jsonify({'success': True})

@app.route('/bot/<int:bot_id>/delete', methods=['POST'])
@login_required
def delete_bot(bot_id):
    deleted = db.delete_bot(bot_id, session['user_id'])
    
    if deleted:
        return redirect(url_for('dashboard'))
    
    return redirect(url_for('dashboard'))

@app.route('/bot/<int:bot_id>/export')
@login_required
def export_bot(bot_id):
    bot = db.get_bot(bot_id)
    
    if not bot or bot['user_id'] != session['user_id']:
        return redirect(url_for('dashboard'))
    
    commands = db.get_bot_commands(bot_id)
    
    export_data = {
        'bot_name': bot['bot_name'],
        'commands': [
            {
                'command': cmd['command'],
                'response_type': cmd['response_type'],
                'response_content': cmd['response_content']
            }
            for cmd in commands
        ],
        'config': json.loads(bot['bot_config']) if bot['bot_config'] else {},
        'exported_at': datetime.now().isoformat()
    }
    
    filename = f'bot_config_{bot_id}.json'
    filepath = f'/tmp/{filename}'
    
    with open(filepath, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    return send_file(filepath, as_attachment=True, download_name=filename)

@app.route('/marketplace')
@login_required
def marketplace():
    templates = db.get_all_templates()
    
    for template in templates:
        try:
            with open(f'templates_library/{template["json_file"]}', 'r') as f:
                template_data = json.load(f)
                template['preview'] = template_data
        except:
            template['preview'] = {}
    
    return render_template('marketplace.html', templates=templates)

@app.route('/marketplace/clone/<int:template_id>')
@login_required
def clone_template(template_id):
    user = db.get_user(session['user_id'])
    user_bots = db.get_user_bots(session['user_id'])
    
    if user['plan'] == 'free' and len(user_bots) >= 1:
        return redirect(url_for('marketplace'))
    
    templates = db.get_all_templates()
    template = next((t for t in templates if t['id'] == template_id), None)
    
    if not template:
        return redirect(url_for('marketplace'))
    
    try:
        with open(f'templates_library/{template["json_file"]}', 'r') as f:
            template_data = json.load(f)
        
        session['clone_template'] = template_data
        db.increment_template_downloads(template_id)
        
        return redirect(url_for('create_bot'))
    except:
        return redirect(url_for('marketplace'))

@app.route('/analytics')
@login_required
def analytics():
    user = db.get_user(session['user_id'])
    bots = db.get_user_bots(session['user_id'])
    analytics_data = db.get_analytics_summary(session['user_id'])
    
    crypto_prices = crypto_api.get_multiple_prices(['bitcoin', 'ethereum', 'binancecoin'])
    trending = crypto_api.get_trending_coins()
    global_stats = crypto_api.get_global_stats()
    
    return render_template('analytics.html',
                         user=user,
                         bots=bots,
                         analytics=analytics_data,
                         crypto_prices=crypto_prices,
                         trending=trending,
                         global_stats=global_stats)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    user = db.get_user(session['user_id'])
    
    if request.method == 'POST':
        wallet_address = request.form.get('wallet_address', '').strip()
        
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET wallet_address = ? WHERE id = ?', (wallet_address, session['user_id']))
        conn.commit()
        conn.close()
        
        user = db.get_user(session['user_id'])
    
    ai_available = ai_assistant.is_available()
    
    return render_template('settings.html', user=user, ai_available=ai_available)

@app.route('/api/ai/generate-response', methods=['POST'])
@login_required
def api_ai_generate():
    data = request.get_json()
    command = data.get('command', '')
    description = data.get('description', '')
    
    if not ai_assistant.is_available():
        return jsonify({'success': False, 'error': 'AI features require Gemini API key'})
    
    response = ai_assistant.suggest_command_response(command, description)
    
    return jsonify({'success': True, 'response': response})

@app.route('/api/crypto/price/<coin_id>')
def api_crypto_price(coin_id):
    price_data = crypto_api.get_crypto_price(coin_id)
    
    if price_data:
        return jsonify(price_data)
    
    return jsonify({'error': 'Failed to fetch price'}), 404

@app.route('/api/templates')
def api_templates():
    templates = db.get_all_templates()
    return jsonify(templates)

@app.route('/api/bots')
@login_required
def api_bots():
    bots = db.get_user_bots(session['user_id'])
    return jsonify(bots)

@app.route('/webhook/<int:bot_id>', methods=['POST'])
def webhook(bot_id):
    """Handle incoming Telegram updates for a specific bot"""
    bot = db.get_bot(bot_id)
    
    if not bot:
        return jsonify({'error': 'Bot not found'}), 404
    
    try:
        update = request.get_json()
        
        if not update or 'message' not in update:
            return jsonify({'ok': True})
        
        message = update['message']
        chat_id = message['chat']['id']
        text = message.get('text', '')
        
        if not text:
            return jsonify({'ok': True})
        
        # Extract command (remove leading /)
        command = text.lstrip('/').split()[0].lower() if text.startswith('/') else None
        
        # Get bot token
        decrypted_token = db.decrypt_token(bot['bot_token'])
        telegram_api = TelegramAPI(decrypted_token)
        
        # Find matching command
        commands = db.get_bot_commands(bot_id)
        response_sent = False
        
        for cmd in commands:
            if cmd['command'].lower() == command:
                # Send the response
                telegram_api.send_message(chat_id, cmd['response_content'])
                response_sent = True
                
                # Update analytics
                db.increment_bot_messages(bot_id)
                break
        
        if not response_sent and command:
            # Send default help message
            help_text = "Available commands:\n"
            for cmd in commands:
                help_text += f"/{cmd['command']}\n"
            telegram_api.send_message(chat_id, help_text or "No commands configured yet.")
        
        return jsonify({'ok': True})
    
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({'ok': True})

@app.route('/bot/<int:bot_id>/setup-webhook', methods=['POST'])
@login_required
def setup_webhook(bot_id):
    """Set up webhook for a bot"""
    bot = db.get_bot(bot_id)
    
    if not bot or bot['user_id'] != session['user_id']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        decrypted_token = db.decrypt_token(bot['bot_token'])
        telegram_api = TelegramAPI(decrypted_token)
        
        # Get the HTTPS URL for the webhook
        # Replace http:// with https:// for Replit production URL
        base_url = request.host_url.replace('http://', 'https://')
        webhook_url = f"{base_url}webhook/{bot_id}"
        
        result = telegram_api.set_webhook(webhook_url)
        
        if result and result.get('ok'):
            return jsonify({'success': True, 'webhook_url': webhook_url})
        else:
            return jsonify({'success': False, 'error': result.get('description', 'Failed to set webhook')})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/bot/<int:bot_id>/deploy-webapp', methods=['POST'])
@login_required
def deploy_webapp(bot_id):
    """Deploy web app bot"""
    bot = db.get_bot(bot_id)
    
    if not bot or bot['user_id'] != session['user_id']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        base_url = request.host_url.replace('http://', 'https://')
        webapp_url = f"{base_url}webapp/{bot_id}"
        
        # Update bot config
        bot_config = json.loads(bot['bot_config']) if bot['bot_config'] else {}
        bot_config['webapp_url'] = webapp_url
        bot_config['deployed_at'] = datetime.now().isoformat()
        
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE bots SET bot_config = ?, is_active = 1 WHERE id = ?', 
                      (json.dumps(bot_config), bot_id))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'webapp_url': webapp_url})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/bot/<int:bot_id>/setup-game', methods=['POST'])
@login_required
def setup_game(bot_id):
    """Setup game bot"""
    bot = db.get_bot(bot_id)
    
    if not bot or bot['user_id'] != session['user_id']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        # Update bot config with game settings
        bot_config = json.loads(bot['bot_config']) if bot['bot_config'] else {}
        bot_config['game_active'] = True
        bot_config['game_settings'] = {
            'max_players': 100,
            'rounds': 5,
            'start_command': '/play'
        }
        
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE bots SET bot_config = ?, is_active = 1 WHERE id = ?', 
                      (json.dumps(bot_config), bot_id))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Game bot activated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/bot/<int:bot_id>/setup-mining', methods=['POST'])
@login_required
def setup_mining(bot_id):
    """Setup mining bot"""
    bot = db.get_bot(bot_id)
    
    if not bot or bot['user_id'] != session['user_id']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        # Get bot username from Telegram API
        bot_username = None
        bot_link = None
        
        if bot['bot_token']:
            try:
                decrypted_token = db.decrypt_token(bot['bot_token'])
                telegram_api = TelegramAPI(decrypted_token)
                bot_info = telegram_api.get_me()
                
                if bot_info and bot_info.get('ok'):
                    bot_username = bot_info['result'].get('username')
                    if bot_username:
                        bot_link = f"https://t.me/{bot_username}"
            except Exception as e:
                print(f"Error getting bot info: {e}")
        
        # Update bot config with mining settings
        bot_config = json.loads(bot['bot_config']) if bot['bot_config'] else {}
        bot_config['mining_active'] = True
        bot_config['mining_settings'] = {
            'tap_reward': 1,
            'max_energy': 1000,
            'referral_bonus': 500,
            'energy_recharge_rate': 1
        }
        
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE bots SET bot_config = ?, is_active = 1, bot_username = ? WHERE id = ?', 
                      (json.dumps(bot_config), bot_username, bot_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'Mining bot activated',
            'bot_link': bot_link,
            'bot_username': bot_username
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
