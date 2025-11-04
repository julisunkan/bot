import os
import json
import secrets
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file, flash
from werkzeug.utils import secure_filename
from utils.database import Database
from utils.ai import AIAssistant
from utils.crypto import CryptoAPI
from utils.telegram_api import TelegramAPI
from utils.telegram_auth import validate_telegram_webapp_data

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', secrets.token_hex(32))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Add custom Jinja2 filters
@app.template_filter('from_json')
def from_json_filter(value):
    if not value:
        return {}
    try:
        return json.loads(value)
    except:
        return {}

db = Database()
ai_assistant = AIAssistant()
crypto_api = CryptoAPI()

def shorten_url(long_url):
    try:
        response = requests.get(f'https://tinyurl.com/api-create.php?url={long_url}', timeout=5)
        if response.status_code == 200 and response.text.startswith('http'):
            app.logger.info(f"URL shortened successfully: {long_url} → {response.text}")
            return response.text
        else:
            app.logger.warning(f"TinyURL returned unexpected response for {long_url}: status={response.status_code}, response={response.text[:100]}")
            return long_url
    except Exception as e:
        app.logger.error(f"URL shortening failed for {long_url}: {str(e)}")
        return long_url

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

        # Require bot token for all bot types
        if not bot_token:
            return render_template('create_bot.html', error='Bot token is required. Get one from @BotFather on Telegram.')

        # Verify bot token with BotFather for all bot types
        telegram_api = TelegramAPI()
        verification = telegram_api.verify_token(bot_token)

        if not verification['valid']:
            return render_template('create_bot.html', error='Invalid Telegram bot token. Please get a valid token from @BotFather.')

        # Get bot username for the link
        bot_username = verification.get('bot_info', {}).get('username')

        bot_config = json.dumps({
            'commands': [],
            'bot_type': bot_type,
            'created_at': datetime.now().isoformat(),
            'bot_link': f'https://t.me/{bot_username}' if bot_username else None
        })

        bot_id = db.create_bot(session['user_id'], bot_name, bot_token, bot_config, bot_type)

        # Update bot username in database
        if bot_username:
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE bots SET bot_username = ? WHERE id = ?', (bot_username, bot_id))
            conn.commit()
            conn.close()

        # Add default commands for the bot (including built-in commands that are now editable)
        default_commands = [
            ('start', 'text', f'👋 Welcome to {bot_name}!\n\nI\'m here to help you. Use /help to see available commands.'),
            ('help', 'text', '📋 Available Commands:\n\n/start - Start the bot\n/menu - Interactive command menu\n/profile - View your profile\n/donate - Support the developer\n/about - Learn about this bot\n/features - See bot features\n/contact - Contact support\n/settings - Configure your preferences\n/feedback - Send us feedback\n/stats - View your statistics\n/news - Latest updates\n/faq - Frequently asked questions'),
            ('menu', 'text', '🎯 Menu\n\nClick any button below to execute a command, or type a command manually.'),
            ('profile', 'text', '👤 Your Profile\n\n🆔 User ID: {user_id}\n👤 Name: {name}\n📱 Username: @{username}\n🌐 Language: {language}\n\n💬 Chat ID: {chat_id}'),
            ('donate', 'text', f'💝 Support the Developer\n\nThank you for using this bot! Your support helps keep it running.\n\n💳 Donation Options:\n\n🔹 Bitcoin (BTC)\nbc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh\n\n🔹 Ethereum (ETH)\n0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb\n\n🔹 TON\nUQD-fake-address-for-demo\n\n🔹 USDT (TRC20)\nTFake1234567890Address\n\n💙 Every contribution is appreciated!\n\nCreated with ❤️ using Advanced Bots Creator'),
            ('about', 'text', f'ℹ️ About {bot_name}\n\nThis bot was created using Advanced Bots Creator - the ultimate Telegram bot creator platform.\n\nVersion: 1.0\nCreated: {datetime.now().strftime("%B %Y")}\n\nPowered by Advanced Bots Creator 🚀'),
            ('features', 'text', '✨ Bot Features:\n\n• 🤖 Automated responses\n• 💬 Interactive commands\n• 📊 Analytics tracking\n• 🔔 Notifications\n• 🎯 Custom workflows\n• 🌐 Multi-language support\n\nMore features coming soon!'),
            ('contact', 'text', '📧 Contact Us\n\nNeed help? Reach out to us:\n\n📱 Support: @support\n📧 Email: support@example.com\n🌐 Website: https://example.com\n\nWe typically respond within 24 hours!'),
            ('settings', 'text', '⚙️ Settings\n\nConfigure your bot preferences:\n\n🔔 Notifications: ON\n🌐 Language: English\n📍 Timezone: UTC\n🎨 Theme: Default\n\nUse the buttons below to customize your settings.'),
            ('feedback', 'text', '💭 Send Feedback\n\nWe value your input! Please share:\n\n• Suggestions for improvement\n• Bug reports\n• Feature requests\n• General comments\n\nSend your feedback as a message and we\'ll review it!'),
            ('stats', 'text', '📊 Your Statistics\n\n👤 Member since: Today\n💬 Messages sent: 1\n🎯 Commands used: 1\n⭐ Level: Beginner\n\nKeep using the bot to unlock achievements!'),
            ('news', 'text', '📰 Latest Updates\n\n🎉 New Features (v1.0):\n• Enhanced command system\n• Improved performance\n• Bug fixes and optimizations\n\nStay tuned for more updates!'),
            ('faq', 'text', '❓ Frequently Asked Questions\n\nQ: How do I use this bot?\nA: Simply send commands starting with /\n\nQ: Is this bot free?\nA: Yes, basic features are completely free!\n\nQ: How do I report issues?\nA: Use /feedback to send us a message\n\nQ: Can I customize responses?\nA: Contact the bot owner for customization options')
        ]

        for command, response_type, response_content in default_commands:
            db.add_bot_command(bot_id, command, response_type, response_content)

        return redirect(url_for('bot_detail', bot_id=bot_id))

    return render_template('create_bot.html')

@app.route('/bot/<int:bot_id>')
@login_required
def bot_detail(bot_id):
    bot = db.get_bot(bot_id)

    if not bot or bot['user_id'] != session['user_id']:
        return redirect(url_for('dashboard'))

    commands = db.get_bot_commands(bot_id)
    templates = db.get_all_templates()

    try:
        bot_config = json.loads(bot['bot_config']) if bot['bot_config'] else {}
    except:
        bot_config = {}

    return render_template('bot_detail.html', bot=bot, commands=commands, bot_config=bot_config, templates=templates)

@app.route('/bot/<int:bot_id>/add-command', methods=['POST'])
@login_required
def add_command(bot_id):
    bot = db.get_bot(bot_id)

    if not bot or bot['user_id'] != session['user_id']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    command = request.form.get('command', '').strip().lower()
    response_type = request.form.get('response_type', 'text')
    response_content = request.form.get('response_content', '').strip()
    url_link = request.form.get('url_link', '').strip()

    # Remove leading slash if user added it
    command = command.lstrip('/')

    if not command:
        return jsonify({'success': False, 'error': 'Command is required'}), 400

    # Check for duplicate commands
    existing_commands = db.get_bot_commands(bot_id)
    if any(cmd['command'] == command for cmd in existing_commands):
        return jsonify({'success': False, 'error': f'Command /{command} already exists'}), 400

    if response_type != 'url' and not response_content:
        return jsonify({'success': False, 'error': 'Response content required'}), 400

    if response_type == 'url' and not url_link:
        return jsonify({'success': False, 'error': 'URL is required for URL type'}), 400

    try:
        db.add_bot_command(bot_id, command, response_type, response_content, url_link)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to add command: {str(e)}'}), 500

@app.route('/bot/<int:bot_id>/set-menu', methods=['POST'])
@login_required
def set_bot_menu(bot_id):
    """Set bot menu commands"""
    bot = db.get_bot(bot_id)

    if not bot or bot['user_id'] != session['user_id']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        decrypted_token = db.decrypt_token(bot['bot_token'])
        telegram_api = TelegramAPI(decrypted_token)

        # Get all commands for this bot
        commands = db.get_bot_commands(bot_id)

        # Format commands for Telegram menu
        menu_commands = []
        for cmd in commands[:15]:  # Telegram allows max 100 commands, we'll use 15
            menu_commands.append({
                'command': cmd['command'],
                'description': cmd['response_content'][:60] if cmd['response_content'] else 'Bot command'
            })

        # Set bot commands via Telegram API
        result = telegram_api.set_bot_commands(menu_commands)

        if result and result.get('ok'):
            return jsonify({'success': True, 'message': 'Menu updated successfully'})
        else:
            return jsonify({'success': False, 'error': result.get('description', 'Failed to set menu')})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/bot/<int:bot_id>/command/<int:command_id>/edit', methods=['POST'])
@login_required
def edit_command(bot_id, command_id):
    bot = db.get_bot(bot_id)

    if not bot or bot['user_id'] != session['user_id']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    command = request.form.get('command', '').strip().lower()
    response_type = request.form.get('response_type', 'text')
    response_content = request.form.get('response_content', '').strip()
    url_link = request.form.get('url_link', '').strip()

    if not command:
        return jsonify({'success': False, 'error': 'Command is required'}), 400

    if response_type != 'url' and not response_content:
        return jsonify({'success': False, 'error': 'Response content required'}), 400

    if response_type == 'url' and not url_link:
        return jsonify({'success': False, 'error': 'URL is required for URL type'}), 400

    updated = db.update_bot_command(command_id, bot_id, command, response_type, response_content, url_link)

    if updated:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Command not found'}), 404

@app.route('/bot/<int:bot_id>/command/<int:command_id>/delete', methods=['POST'])
@login_required
def delete_command(bot_id, command_id):
    bot = db.get_bot(bot_id)

    if not bot or bot['user_id'] != session['user_id']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    deleted = db.delete_bot_command(command_id, bot_id)

    if deleted:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Command not found'}), 404

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
    templates = db.get_all_templates()
    template = next((t for t in templates if t['id'] == template_id), None)

    if not template:
        flash('Template not found.', 'danger')
        return redirect(url_for('marketplace'))

    try:
        with open(f'templates_library/{template["json_file"]}', 'r') as f:
            template_data = json.load(f)

        session['clone_template'] = template_data
        db.increment_template_downloads(template_id)

        return redirect(url_for('create_bot'))
    except Exception as e:
        flash('Error loading template. Please try again.', 'danger')
        return redirect(url_for('marketplace'))

@app.route('/templates/edit/<int:template_id>', methods=['GET', 'POST'])
@login_required
def edit_template(template_id):
    template = db.get_template(template_id)

    if not template:
        flash('Template not found.', 'danger')
        return redirect(url_for('marketplace'))

    if request.method == 'POST':
        try:
            template_json = request.form.get('template_json', '')
            template_data = json.loads(template_json)

            title = request.form.get('title', template['title'])
            description = request.form.get('description', template['description'])
            category = request.form.get('category', template['category'])

            with open(f'templates_library/{template["json_file"]}', 'w') as f:
                json.dump(template_data, f, indent=2)

            db.update_template(template_id, title, description, category, template['json_file'])

            flash('Template updated successfully!', 'success')
            return redirect(url_for('marketplace'))
        except json.JSONDecodeError:
            flash('Invalid JSON format. Please check your template.', 'danger')
        except Exception as e:
            flash(f'Error updating template: {str(e)}', 'danger')

    try:
        with open(f'templates_library/{template["json_file"]}', 'r') as f:
            template_json = json.dumps(json.load(f), indent=2)
    except:
        template_json = '{}'

    return render_template('edit_template.html', template=template, template_json=template_json)

@app.route('/templates/export/<int:template_id>')
@login_required
def export_template(template_id):
    import zipfile
    from io import BytesIO

    template = db.get_template(template_id)

    if not template:
        flash('Template not found.', 'danger')
        return redirect(url_for('marketplace'))

    try:
        memory_file = BytesIO()

        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            template_path = f'templates_library/{template["json_file"]}'
            zf.write(template_path, template["json_file"])

            metadata = {
                'title': template['title'],
                'description': template['description'],
                'category': template['category'],
                'template_file': template['json_file']
            }
            zf.writestr('metadata.json', json.dumps(metadata, indent=2))

        memory_file.seek(0)

        filename = f'{template["title"].replace(" ", "_").lower()}_template.zip'
        return send_file(memory_file, as_attachment=True, download_name=filename, mimetype='application/zip')
    except Exception as e:
        flash(f'Error exporting template: {str(e)}', 'danger')
        return redirect(url_for('marketplace'))

@app.route('/templates/import', methods=['GET', 'POST'])
@login_required
def import_template():
    if request.method == 'POST':
        import zipfile
        from io import BytesIO

        if 'template_file' not in request.files:
            flash('No file uploaded.', 'danger')
            return redirect(url_for('import_template'))

        file = request.files['template_file']

        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(url_for('import_template'))

        if not file.filename.endswith('.zip'):
            flash('Please upload a .zip file.', 'danger')
            return redirect(url_for('import_template'))

        try:
            with zipfile.ZipFile(BytesIO(file.read()), 'r') as zf:
                file_list = zf.namelist()

                if 'metadata.json' not in file_list:
                    flash('Invalid template file: metadata.json not found.', 'danger')
                    return redirect(url_for('import_template'))

                metadata = json.loads(zf.read('metadata.json').decode('utf-8'))

                template_filename = metadata.get('template_file', 'imported_template.json')
                if template_filename not in file_list:
                    flash(f'Template file {template_filename} not found in zip.', 'danger')
                    return redirect(url_for('import_template'))

                template_data = json.loads(zf.read(template_filename).decode('utf-8'))

                import time
                new_filename = f'imported_{int(time.time())}_{template_filename}'

                with open(f'templates_library/{new_filename}', 'w') as f:
                    json.dump(template_data, f, indent=2)

                title = metadata.get('title', 'Imported Template')
                description = metadata.get('description', 'Imported from zip file')
                category = metadata.get('category', 'custom')

                db.add_template(title, description, category, new_filename)

                flash('Template imported successfully!', 'success')
                return redirect(url_for('marketplace'))

        except zipfile.BadZipFile:
            flash('Invalid zip file.', 'danger')
        except json.JSONDecodeError:
            flash('Invalid JSON in template file.', 'danger')
        except Exception as e:
            flash(f'Error importing template: {str(e)}', 'danger')

    return render_template('import_template.html')

@app.route('/bots/<int:bot_id>/apply-template/<int:template_id>')
@login_required
def apply_template_to_bot(bot_id, template_id):
    bot = db.get_bot(bot_id)

    if not bot or bot['user_id'] != session['user_id']:
        flash('Bot not found or access denied.', 'danger')
        return redirect(url_for('dashboard'))

    template = db.get_template(template_id)

    if not template:
        flash('Template not found.', 'danger')
        return redirect(url_for('bot_detail', bot_id=bot_id))

    try:
        with open(f'templates_library/{template["json_file"]}', 'r') as f:
            template_data = json.load(f)

        db.apply_template_to_bot(bot_id, template['json_file'])

        if 'commands' in template_data:
            for cmd in template_data['commands']:
                db.add_bot_command(
                    bot_id,
                    cmd.get('command', ''),
                    cmd.get('response_type', 'text'),
                    cmd.get('response_content', ''),
                    cmd.get('url_link')
                )

        flash(f'Template "{template["title"]}" applied successfully!', 'success')
        return redirect(url_for('bot_detail', bot_id=bot_id))
    except Exception as e:
        flash(f'Error applying template: {str(e)}', 'danger')
        return redirect(url_for('bot_detail', bot_id=bot_id))

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
        flash('Wallet address updated successfully!', 'success')
        conn.commit()
        conn.close()

        user = db.get_user(session['user_id'])

    ai_available = ai_assistant.is_available()

    return render_template('settings.html', user=user, ai_available=ai_available)

@app.route('/ton-wallet', methods=['GET', 'POST'])
@login_required
def ton_wallet_settings():
    user = db.get_user(session['user_id'])

    if request.method == 'POST':
        ton_wallet_address = request.form.get('ton_wallet_address', '').strip()

        # Validate TON wallet
        if not ton_wallet_address:
            flash('TON wallet address is required.', 'danger')
            return redirect(url_for('ton_wallet_settings'))

        if not ((ton_wallet_address.startswith('UQ') or ton_wallet_address.startswith('EQ')) and len(ton_wallet_address) == 48):
            flash('Invalid TON wallet address format. Must start with UQ or EQ and be exactly 48 characters.', 'danger')
            return redirect(url_for('ton_wallet_settings'))

        conn = db.get_connection()
        cursor = conn.cursor()

        # Update user's TON wallet
        cursor.execute('UPDATE users SET wallet_address = ? WHERE id = ?', (ton_wallet_address, session['user_id']))

        # Update all mining bots owned by this user to use this wallet
        cursor.execute('SELECT id, bot_config FROM bots WHERE user_id = ? AND bot_type = ?', (session['user_id'], 'mining'))
        mining_bots = cursor.fetchall()

        updated_count = 0
        for bot in mining_bots:
            bot_config = json.loads(bot['bot_config']) if bot['bot_config'] else {}
            bot_config['owner_ton_wallet'] = ton_wallet_address
            cursor.execute('UPDATE bots SET bot_config = ? WHERE id = ?', (json.dumps(bot_config), bot['id']))
            updated_count += 1

        conn.commit()
        conn.close()

        flash(f'✅ TON wallet saved and applied to {updated_count} mining bot(s)!', 'success')
        return redirect(url_for('ton_wallet_settings'))

    # Get mining bots for display
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bots WHERE user_id = ? AND bot_type = ?', (session['user_id'], 'mining'))
    mining_bots = cursor.fetchall()

    # Get statistics
    cursor.execute('''
        SELECT COUNT(DISTINCT mp.id) as total_players
        FROM mining_players mp
        JOIN bots b ON mp.bot_id = b.id
        WHERE b.user_id = ?
    ''', (session['user_id'],))
    stats = cursor.fetchone()
    total_players = stats['total_players'] if stats else 0

    cursor.execute('''
        SELECT COUNT(*) as pending_payments
        FROM mining_withdrawals mw
        JOIN mining_players mp ON mw.player_id = mp.id
        JOIN bots b ON mp.bot_id = b.id
        WHERE b.user_id = ? AND mw.status = 'pending'
    ''', (session['user_id'],))
    payment_stats = cursor.fetchone()
    total_payments_count = payment_stats['pending_payments'] if payment_stats else 0

    conn.close()

    return render_template('ton_wallet.html', 
                         user=user, 
                         mining_bots=[dict(bot) for bot in mining_bots],
                         total_players=total_players,
                         total_payments_count=total_payments_count)

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

        if not update:
            return jsonify({'ok': True})

        # Get bot token
        decrypted_token = db.decrypt_token(bot['bot_token'])
        telegram_api = TelegramAPI(decrypted_token)

        # Handle callback queries from inline keyboard buttons
        if 'callback_query' in update:
            callback_query = update['callback_query']
            chat_id = callback_query['message']['chat']['id']
            callback_data = callback_query['data']

            # Handle command execution from menu
            if callback_data.startswith('cmd_'):
                command_id = int(callback_data.split('_')[1])
                commands = db.get_bot_commands(bot_id)
                cmd = next((c for c in commands if c['id'] == command_id), None)

                if cmd:
                    if cmd['response_type'] == 'url' and cmd.get('url_link'):
                        keyboard = {
                            'inline_keyboard': [[
                                {
                                    'text': cmd.get('response_content') or 'Open Link',
                                    'web_app': {'url': cmd['url_link']}
                                }
                            ]]
                        }
                        telegram_api.send_message(chat_id, f"/{cmd['command']}", reply_markup=keyboard)
                    else:
                        telegram_api.send_message(chat_id, cmd['response_content'])

                    telegram_api.answer_callback_query(callback_query['id'], text='Command executed')
                    db.increment_bot_messages(bot_id)

            return jsonify({'ok': True})

        if 'message' not in update:
            return jsonify({'ok': True})

        message = update['message']
        chat_id = message['chat']['id']
        text = message.get('text', '')
        user_info = message.get('from', {})

        if not text:
            return jsonify({'ok': True})

        # Extract command (remove leading /)
        command = text.lstrip('/').split()[0].lower() if text.startswith('/') else None

        # Get bot token (already retrieved above)
        # telegram_api already initialized above

        # Handle mining bot /start command
        if command == 'start' and bot.get('bot_type') == 'mining':
            telegram_user_id = user_info.get('id')
            username = user_info.get('username', '')
            first_name = user_info.get('first_name', 'Player')

            referred_by = None
            if ' ' in text:
                ref_code = text.split(' ')[1]
                if ref_code.startswith('ref_'):
                    referred_by = ref_code[4:]

            player = db.get_or_create_mining_player(bot_id, telegram_user_id, username, first_name, referred_by)

            base_url = request.host_url.replace('http://', 'https://')
            webapp_url = f"{base_url}mining-app?bot_id={bot_id}"

            keyboard = {
                'inline_keyboard': [[
                    {
                        'text': '⛏️ Start Mining',
                        'web_app': {'url': webapp_url}
                    }
                ]]
            }

            welcome_message = f'''⛏️ Welcome to TapCoin Mining, {first_name}!

💰 Your Balance: {int(player['coins'])} coins
⚡ Energy: {player['energy']}/{player['energy_max']}
🏆 Level: {player['level']}

Tap the button below to start mining coins!

🎁 Invite friends and earn 500 coins per referral!
📈 Plus get 10% of their mining earnings!

Click "Start Mining" to launch the game! 👇'''

            telegram_api.send_message(chat_id, welcome_message, reply_markup=keyboard)
            db.increment_bot_messages(bot_id)
            return jsonify({'ok': True})

        # Find matching command
        commands = db.get_bot_commands(bot_id)
        response_sent = False

        for cmd in commands:
            if cmd['command'].lower() == command:
                # Special handling for menu command - show interactive buttons
                if cmd['command'].lower() == 'menu':
                    keyboard_buttons = []
                    for i, menu_cmd in enumerate(commands[:20]):  # Max 20 commands in menu
                        keyboard_buttons.append([{
                            'text': f"/{menu_cmd['command']}",
                            'callback_data': f"cmd_{menu_cmd['id']}"
                        }])

                    keyboard = {'inline_keyboard': keyboard_buttons}
                    telegram_api.send_message(chat_id, cmd['response_content'], reply_markup=keyboard)
                    response_sent = True
                    db.increment_bot_messages(bot_id)
                    break

                # Special handling for profile command - replace placeholders
                if cmd['command'].lower() == 'profile':
                    user_id = user_info.get('id', 'Unknown')
                    username = user_info.get('username', 'Not set')
                    first_name = user_info.get('first_name', 'Unknown')
                    last_name = user_info.get('last_name', '')
                    language_code = user_info.get('language_code', 'Unknown')

                    profile_text = cmd['response_content'].replace('{user_id}', str(user_id))
                    profile_text = profile_text.replace('{username}', username)
                    profile_text = profile_text.replace('{name}', f"{first_name} {last_name}")
                    profile_text = profile_text.replace('{language}', language_code)
                    profile_text = profile_text.replace('{chat_id}', str(chat_id))

                    telegram_api.send_message(chat_id, profile_text)
                    response_sent = True
                    db.increment_bot_messages(bot_id)
                    break

                # Check if this is a URL type command
                if cmd['response_type'] == 'url' and cmd.get('url_link'):
                    # Create inline keyboard with web app button
                    keyboard = {
                        'inline_keyboard': [[
                            {
                                'text': cmd.get('response_content') or 'Open Link',
                                'web_app': {'url': cmd['url_link']}
                            }
                        ]]
                    }
                    message_text = f"Click the button below to open:\n{cmd['url_link']}"
                    telegram_api.send_message(chat_id, message_text, reply_markup=keyboard)
                else:
                    # Send regular text response
                    telegram_api.send_message(chat_id, cmd['response_content'])

                response_sent = True

                # Update analytics
                db.increment_bot_messages(bot_id)
                break

        if not response_sent and command:
            # Send default help message
            help_text = "📋 Available Commands:\n\n"
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
        full_url = f"{base_url}w/{bot_id}"
        
        shortened_url = shorten_url(full_url)
        url_was_shortened = shortened_url != full_url

        # Update bot config
        bot_config = json.loads(bot['bot_config']) if bot['bot_config'] else {}
        bot_config['webapp_url'] = shortened_url
        bot_config['webapp_full_url'] = full_url
        bot_config['deployed_at'] = datetime.now().isoformat()
        bot_config['url_shortened'] = url_was_shortened

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE bots SET bot_config = ?, is_active = 1 WHERE id = ?', 
                      (json.dumps(bot_config), bot_id))
        conn.commit()
        conn.close()

        return jsonify({
            'success': True, 
            'webapp_url': shortened_url,
            'full_url': full_url,
            'shortened': url_was_shortened
        })
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

        if bot_username and bot['bot_token']:
            decrypted_token = db.decrypt_token(bot['bot_token'])
            telegram_api = TelegramAPI(decrypted_token)
            webhook_url = f"{os.environ.get('REPLIT_DEV_DOMAIN', 'http://localhost:5000')}/webhook/{bot_id}"
            try:
                telegram_api.set_webhook(webhook_url)
            except Exception as e:
                print(f"Webhook setup error: {e}")

        return jsonify({
            'success': True, 
            'message': 'Mining bot activated',
            'bot_link': bot_link,
            'bot_username': bot_username
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})



@app.route('/bot/<int:bot_id>/mining-settings', methods=['GET', 'POST'])
@login_required
def mining_settings(bot_id):
    """Mining bot configuration page"""
    bot = db.get_bot(bot_id)

    if not bot or bot['user_id'] != session['user_id']:
        flash('Bot not found or unauthorized', 'danger')
        return redirect(url_for('dashboard'))

    if bot['bot_type'] != 'mining':
        flash('This is not a mining bot', 'warning')
        return redirect(url_for('bot_detail', bot_id=bot_id))

    if request.method == 'POST':
        try:
            bot_config = json.loads(bot['bot_config']) if bot['bot_config'] else {}

            # Get TON wallet address for receiving payments
            owner_ton_wallet = request.form.get('owner_ton_wallet', '').strip()

            # Validate TON wallet if provided
            if owner_ton_wallet and not ((owner_ton_wallet.startswith('UQ') or owner_ton_wallet.startswith('EQ')) and len(owner_ton_wallet) == 48):
                flash('Invalid TON wallet address format. Must start with UQ or EQ and be 48 characters.', 'danger')
                return redirect(url_for('mining_settings', bot_id=bot_id))

            bot_config['owner_ton_wallet'] = owner_ton_wallet
            bot_config['mining_settings'] = {
                'tap_reward': int(request.form.get('tap_reward', 1)),
                'max_energy': int(request.form.get('max_energy', 1000)),
                'energy_recharge_rate': int(request.form.get('energy_recharge_rate', 1)),
                'referral_bonus': int(request.form.get('referral_bonus', 500)),
                'min_withdrawal': int(request.form.get('min_withdrawal', 10000)),
                'enable_shop': request.form.get('enable_shop') == 'on',
                'enable_wallet': request.form.get('enable_wallet') == 'on',
                'enable_tasks': request.form.get('enable_tasks') == 'on',
                'enable_leaderboard': request.form.get('enable_leaderboard') == 'on',
                'enable_daily_reward': request.form.get('enable_daily_reward') == 'on',
                'daily_reward_amount': int(request.form.get('daily_reward_amount', 100)),
                'boost_energy_cost': int(request.form.get('boost_energy_cost', 500)),
                'boost_multitap_cost': int(request.form.get('boost_multitap_cost', 1000)),
                'boost_recharge_cost': int(request.form.get('boost_recharge_cost', 750)),
                'coin_price_usd': float(request.form.get('coin_price_usd', 0.001)),
            }

            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE bots SET bot_config = ? WHERE id = ?', (json.dumps(bot_config), bot_id))
            conn.commit()
            conn.close()

            flash('Mining settings updated successfully!', 'success')
            return redirect(url_for('mining_settings', bot_id=bot_id))
        except Exception as e:
            flash(f'Error updating settings: {str(e)}', 'danger')

    bot_config = json.loads(bot['bot_config']) if bot['bot_config'] else {}
    mining_settings = bot_config.get('mining_settings', {
        'tap_reward': 1,
        'max_energy': 1000,
        'energy_recharge_rate': 1,
        'referral_bonus': 500,
        'min_withdrawal': 10000,
        'enable_shop': True,
        'enable_wallet': True,
        'enable_tasks': True,
        'enable_leaderboard': True,
        'enable_daily_reward': True,
        'daily_reward_amount': 100,
        'boost_energy_cost': 500,
        'boost_multitap_cost': 1000,
        'boost_recharge_cost': 750,
        'coin_price_usd': 0.001,
    })
    owner_ton_wallet = bot_config.get('owner_ton_wallet', '')

    return render_template('mining_settings.html', bot=bot, settings=mining_settings, owner_ton_wallet=owner_ton_wallet)

@app.route('/mining-app')
def mining_app():
    return render_template('mining_app.html')

@app.route('/w/<int:bot_id>')
def webapp(bot_id):
    bot = db.get_bot(bot_id)
    if not bot or not bot['is_active']:
        return "Bot not found or inactive", 404
    
    bot_config = json.loads(bot['bot_config']) if bot['bot_config'] else {}
    webapp_data = bot_config.get('webapp_data', {})
    
    return render_template('webapp.html', bot=bot, bot_id=bot_id, webapp_data=webapp_data)

@app.route('/webapp/<int:bot_id>')
def webapp_legacy_redirect(bot_id):
    return redirect(url_for('webapp', bot_id=bot_id), code=301)

@app.route('/api/mining/init')
def mining_init():
    try:
        bot_id = request.args.get('bot_id')
        init_data = request.args.get('init_data', '')

        if not bot_id or not init_data:
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400

        bot = db.get_bot(bot_id)
        if not bot or not bot['is_active']:
            return jsonify({'success': False, 'error': 'Bot not found or inactive'}), 404

        decrypted_token = db.decrypt_token(bot['bot_token'])
        auth_result = validate_telegram_webapp_data(init_data, decrypted_token)

        if not auth_result or not auth_result['valid']:
            return jsonify({'success': False, 'error': 'Invalid authentication'}), 401

        user_data = auth_result['user']
        if not user_data:
            return jsonify({'success': False, 'error': 'User data not found'}), 401

        telegram_user_id = user_data.get('id')
        username = user_data.get('username', '')
        first_name = user_data.get('first_name', 'Player')

        if not telegram_user_id:
            return jsonify({'success': False, 'error': 'Invalid user ID'}), 401

        player = db.get_or_create_mining_player(bot_id, telegram_user_id, username, first_name)
        player = db.update_player_energy(player['id'])

        session_token = secrets.token_urlsafe(32)
        db.create_game_session(player['id'], session_token)

        bot_username = bot.get('bot_username', 'your_bot')
        bot_config = json.loads(bot['bot_config']) if bot['bot_config'] else {}
        mining_settings = bot_config.get('mining_settings', {})

        return jsonify({
            'success': True,
            'player': player,
            'bot_username': bot_username,
            'session_token': session_token,
            'settings': mining_settings
        })
    except Exception as e:
        print(f"Mining init error: {e}")
        return jsonify({'success': False, 'error': 'Authentication failed'}), 500

@app.route('/api/mining/tap', methods=['POST'])
def mining_tap():
    try:
        data = request.json
        if not data or 'session_token' not in data or 'bot_id' not in data:
            return jsonify({'success': False, 'error': 'Missing parameters'}), 400

        session_token = data['session_token']
        bot_id = int(data['bot_id'])

        player_id = db.validate_game_session(session_token)
        if not player_id:
            return jsonify({'success': False, 'error': 'Invalid or expired session'}), 401

        player = db.update_player_energy(player_id)

        if not player or int(player['bot_id']) != bot_id:
            return jsonify({'success': False, 'error': 'Invalid player'}), 403

        if player['energy'] <= 0:
            return jsonify({'success': False, 'error': 'No energy'}), 400

        coins_to_add = player['coins_per_tap']
        energy_cost = 1

        player = db.update_mining_player_tap(player_id, coins_to_add, energy_cost)

        return jsonify({
            'success': True,
            'player': player
        })
    except Exception as e:
        print(f"Mining tap error: {e}")
        return jsonify({'success': False, 'error': 'Tap failed'}), 500

@app.route('/api/mining/boost', methods=['POST'])
def mining_boost():
    try:
        data = request.json
        if not data or 'session_token' not in data or 'bot_id' not in data or 'boost_type' not in data:
            return jsonify({'success': False, 'error': 'Missing parameters'}), 400

        session_token = data['session_token']
        bot_id = int(data['bot_id'])
        boost_type = data['boost_type']

        player_id = db.validate_game_session(session_token)
        if not player_id:
            return jsonify({'success': False, 'error': 'Invalid or expired session'}), 401

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT bot_id FROM mining_players WHERE id = ?', (player_id,))
        player = cursor.fetchone()
        conn.close()

        if not player or player['bot_id'] != bot_id:
            return jsonify({'success': False, 'error': 'Invalid player'}), 403

        boost_configs = {
            'energy_limit': {
                'cost': 500,
                'effects': {'energy_max': 500}
            },
            'multi_tap': {
                'cost': 1000,
                'effects': {'coins_per_tap': 1}
            },
            'recharge_speed': {
                'cost': 750,
                'effects': {'energy_recharge_rate': 1}
            }
        }

        if boost_type not in boost_configs:
            return jsonify({'success': False, 'error': 'Invalid boost type'}), 400

        boost_config = boost_configs[boost_type]
        result = db.purchase_boost(player_id, boost_type, boost_config['cost'], boost_config['effects'])

        return jsonify(result)
    except Exception as e:
        print(f"Mining boost error: {e}")
        return jsonify({'success': False, 'error': 'Boost purchase failed'}), 500

@app.route('/api/mining/daily-reward', methods=['POST'])
def mining_daily_reward():
    try:
        data = request.json
        if not data or 'session_token' not in data or 'bot_id' not in data:
            return jsonify({'success': False, 'error': 'Missing parameters'}), 400

        session_token = data['session_token']
        bot_id = int(data['bot_id'])

        player_id = db.validate_game_session(session_token)
        if not player_id:
            return jsonify({'success': False, 'error': 'Invalid or expired session'}), 401

        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM mining_players WHERE id = ? AND bot_id = ?', (player_id, bot_id))
        player = cursor.fetchone()

        if not player:
            conn.close()
            return jsonify({'success': False, 'error': 'Player not found'}), 404

        cursor.execute('''
            SELECT * FROM mining_daily_rewards 
            WHERE player_id = ? AND claimed_at = DATE('now')
        ''', (player_id,))

        today_reward = cursor.fetchone()

        if today_reward:
            conn.close()
            return jsonify({'success': False, 'error': 'Already claimed today'}), 400

        cursor.execute('''
            SELECT MAX(streak_days) as max_streak FROM mining_daily_rewards 
            WHERE player_id = ? AND DATE(claimed_at) = DATE('now', '-1 day')
        ''', (player_id,))

        yesterday_data = cursor.fetchone()
        streak = (yesterday_data['max_streak'] + 1) if yesterday_data and yesterday_data['max_streak'] else 1
        reward_amount = 100 + (streak * 10)

        cursor.execute('''
            INSERT INTO mining_daily_rewards (player_id, claimed_at, reward_amount, streak_days)
            VALUES (?, DATE('now'), ?, ?)
        ''', (player_id, reward_amount, streak))

        cursor.execute('''
            UPDATE mining_players SET coins = coins + ?
            WHERE id = ?
        ''', (reward_amount, player_id))

        conn.commit()

        cursor.execute('SELECT * FROM mining_players WHERE id = ?', (player_id,))
        updated_player = cursor.fetchone()
        conn.close()

        return jsonify({
            'success': True,
            'reward': reward_amount,
            'streak': streak,
            'player': dict(updated_player)
        })

    except Exception as e:
        print(f"Daily reward error: {e}")
        return jsonify({'success': False, 'error': 'Failed to claim reward'}), 500

@app.route('/api/mining/shop/purchase', methods=['POST'])
def mining_shop_purchase():
    try:
        data = request.json
        if not data or 'session_token' not in data or 'bot_id' not in data or 'amount' not in data or 'price' not in data:
            return jsonify({'success': False, 'error': 'Missing parameters'}), 400

        session_token = data['session_token']
        bot_id = int(data['bot_id'])
        amount = int(data['amount'])
        price = float(data['price'])

        player_id = db.validate_game_session(session_token)
        if not player_id:
            return jsonify({'success': False, 'error': 'Invalid session'}), 401

        # Get bot owner's TON wallet
        bot = db.get_bot(bot_id)
        if not bot:
            return jsonify({'success': False, 'error': 'Bot not found'}), 404

        bot_config = json.loads(bot['bot_config']) if bot['bot_config'] else {}
        owner_ton_wallet = bot_config.get('owner_ton_wallet', '').strip()

        # Validate owner wallet exists and is properly formatted
        if not owner_ton_wallet:
            return jsonify({
                'success': False, 
                'error': '⚠️ Shop Unavailable: The bot owner needs to configure their TON wallet address to accept payments. Please contact @{} to enable the shop.'.format(bot.get('bot_username', 'bot_owner'))
            }), 400

        if not ((owner_ton_wallet.startswith('UQ') or owner_ton_wallet.startswith('EQ')) and len(owner_ton_wallet) == 48):
            return jsonify({
                'success': False, 
                'error': '⚠️ Shop Configuration Error: Invalid TON wallet address. Please contact the bot owner.'
            }), 400

        # Get player's wallet
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM mining_wallets WHERE player_id = ?', (player_id,))
        wallet = cursor.fetchone()

        if not wallet or not wallet['wallet_address']:
            conn.close()
            return jsonify({'success': False, 'error': 'Please connect your TON wallet first'}), 400

        # Create payment link for user to pay
        from utils.ton_payment import TONPayment
        ton_payment = TONPayment()

        payment_link = ton_payment.create_payment_link(
            owner_ton_wallet, 
            price, 
            f"BotForge Mining - {amount} coins"
        )

        if not payment_link:
            conn.close()
            return jsonify({'success': False, 'error': 'Invalid payment configuration'}), 400

        conn.close()

        # Return payment link for user to complete payment
        return jsonify({
            'success': False,
            'requires_payment': True,
            'payment_link': payment_link,
            'amount': amount,
            'price': price,
            'message': 'Please complete payment via TON wallet'
        })
    except Exception as e:
        print(f"Shop purchase error: {e}")
        return jsonify({'success': False, 'error': 'Purchase failed'}), 500

@app.route('/api/mining/wallet/connect', methods=['POST'])
def mining_wallet_connect():
    try:
        data = request.json
        if not data or 'session_token' not in data:
            return jsonify({'success': False, 'error': 'Missing parameters'}), 400

        session_token = data['session_token']
        wallet_address = data.get('wallet_address', '')
        wallet_type = data.get('wallet_type', 'ton')

        player_id = db.validate_game_session(session_token)
        if not player_id:
            return jsonify({'success': False, 'error': 'Invalid session'}), 401

        # Validate TON wallet address format
        if wallet_type == 'ton' and wallet_address:
            if not (wallet_address.startswith('UQ') or wallet_address.startswith('EQ')) or len(wallet_address) != 48:
                return jsonify({'success': False, 'error': 'Invalid TON wallet address'}), 400

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO mining_wallets (player_id, wallet_address, wallet_type)
            VALUES (?, ?, ?)
            ON CONFLICT(player_id) DO UPDATE SET 
                wallet_address = ?,
                wallet_type = ?,
                connected_at = CURRENT_TIMESTAMP
        ''', (player_id, wallet_address, wallet_type, wallet_address, wallet_type))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Wallet connected', 'wallet_address': wallet_address})
    except Exception as e:
        print(f"Wallet connect error: {e}")
        return jsonify({'success': False, 'error': 'Connection failed'}), 500

@app.route('/api/mining/wallet/withdraw', methods=['POST'])
def mining_wallet_withdraw():
    try:
        data = request.json
        if not data or 'session_token' not in data or 'amount' not in data:
            return jsonify({'success': False, 'error': 'Missing parameters'}), 400

        session_token = data['session_token']
        amount = float(data['amount'])

        player_id = db.validate_game_session(session_token)
        if not player_id:
            return jsonify({'success': False, 'error': 'Invalid session'}), 401

        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM mining_players WHERE id = ?', (player_id,))
        player = cursor.fetchone()

        if not player:
            conn.close()
            return jsonify({'success': False, 'error': 'Player not found'}), 404

        cursor.execute('SELECT * FROM mining_wallets WHERE player_id = ?', (player_id,))
        wallet = cursor.fetchone()

        if not wallet or not wallet['wallet_address']:
            conn.close()
            return jsonify({'success': False, 'error': 'No wallet connected'}), 400

        if player['coins'] < amount:
            conn.close()
            return jsonify({'success': False, 'error': 'Insufficient coins'}), 400

        if amount < 10000:
            conn.close()
            return jsonify({'success': False, 'error': 'Minimum withdrawal is 10,000 coins'}), 400

        # Calculate fee (2%)
        fee = amount * 0.02
        net_amount = amount - fee

        # Deduct coins from player
        cursor.execute('UPDATE mining_players SET coins = coins - ? WHERE id = ?', (amount, player_id))

        # Record withdrawal
        cursor.execute('''
            UPDATE mining_wallets 
            SET total_withdrawn = total_withdrawn + ?,
                last_withdrawal_at = CURRENT_TIMESTAMP
            WHERE player_id = ?
        ''', (net_amount, player_id))

        # Log the withdrawal transaction
        cursor.execute('''
            INSERT INTO mining_withdrawals (player_id, amount, fee, net_amount, wallet_address, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        ''', (player_id, amount, fee, net_amount, wallet['wallet_address']))

        withdrawal_id = cursor.lastrowid
        conn.commit()

        cursor.execute('SELECT * FROM mining_players WHERE id = ?', (player_id,))
        updated_player = cursor.fetchone()
        conn.close()

        return jsonify({
            'success': True,
            'withdrawal_id': withdrawal_id,
            'amount': amount,
            'fee': fee,
            'net_amount': net_amount,
            'wallet_address': wallet['wallet_address'],
            'player': dict(updated_player)
        })
    except Exception as e:
        print(f"Withdrawal error: {e}")
        return jsonify({'success': False, 'error': 'Withdrawal failed'}), 500

@app.route('/api/mining/wallet/deposit', methods=['POST'])
def mining_wallet_deposit():
    try:
        data = request.json
        if not data or 'session_token' not in data or 'amount' not in data:
            return jsonify({'success': False, 'error': 'Missing parameters'}), 400

        session_token = data['session_token']
        amount = float(data['amount'])
        transaction_hash = data.get('transaction_hash', '')

        player_id = db.validate_game_session(session_token)
        if not player_id:
            return jsonify({'success': False, 'error': 'Invalid session'}), 401

        if amount <= 0:
            return jsonify({'success': False, 'error': 'Invalid amount'}), 400

        conn = db.get_connection()
        cursor = conn.cursor()

        # Add coins to player account
        cursor.execute('UPDATE mining_players SET coins = coins + ? WHERE id = ?', (amount, player_id))

        # Log the deposit
        cursor.execute('''
            INSERT INTO mining_deposits (player_id, amount, transaction_hash, status)
            VALUES (?, ?, ?, 'completed')
        ''', (player_id, amount, transaction_hash))

        conn.commit()

        cursor.execute('SELECT * FROM mining_players WHERE id = ?', (player_id,))
        updated_player = cursor.fetchone()
        conn.close()

        return jsonify({
            'success': True,
            'amount': amount,
            'player': dict(updated_player)
        })
    except Exception as e:
        print(f"Deposit error: {e}")
        return jsonify({'success': False, 'error': 'Deposit failed'}), 500

@app.route('/api/mining/tasks')
def mining_tasks():
    try:
        bot_id = request.args.get('bot_id')
        session_token = request.args.get('session_token')

        if not bot_id or not session_token:
            return jsonify({'success': False, 'error': 'Missing parameters'}), 400

        player_id = db.validate_game_session(session_token)
        if not player_id:
            return jsonify({'success': False, 'error': 'Invalid session'}), 401

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM mining_players WHERE id = ?', (player_id,))
        player = cursor.fetchone()

        cursor.execute('SELECT COUNT(*) as referral_count FROM mining_referrals WHERE referrer_id = ?', (player_id,))
        referral_data = cursor.fetchone()

        cursor.execute('SELECT streak_days FROM mining_daily_rewards WHERE player_id = ? ORDER BY claimed_at DESC LIMIT 1', (player_id,))
        streak_data = cursor.fetchone()

        conn.close()

        tasks = [
            {'id': 'mining', 'name': 'Mine 1000 Coins', 'progress': min(int(player['coins']), 1000), 'target': 1000, 'reward': 500, 'completed': player['coins'] >= 1000},
            {'id': 'referrals', 'name': 'Invite 3 Friends', 'progress': min(referral_data['referral_count'] if referral_data else 0, 3), 'target': 3, 'reward': 1000, 'completed': (referral_data['referral_count'] if referral_data else 0) >= 3},
            {'id': 'streak', 'name': '7-Day Streak', 'progress': min(streak_data['streak_days'] if streak_data else 1, 7), 'target': 7, 'reward': 2000, 'completed': (streak_data['streak_days'] if streak_data else 1) >= 7}
        ]

        return jsonify({'success': True, 'tasks': tasks})
    except Exception as e:
        print(f"Tasks error: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch tasks'}), 500

@app.route('/api/mining/leaderboard')
def mining_leaderboard():
    try:
        bot_id = request.args.get('bot_id')
        limit = request.args.get('limit', 10)

        if not bot_id:
            return jsonify({'success': False, 'error': 'Missing bot_id'}), 400

        bot = db.get_bot(bot_id)
        if not bot or not bot['is_active']:
            return jsonify({'success': False, 'error': 'Bot not found or inactive'}), 404

        leaderboard = db.get_mining_leaderboard(bot_id, limit=limit)

        return jsonify({
            'success': True,
            'leaderboard': leaderboard
        })
    except Exception as e:
        print(f"Leaderboard error: {e}")
        return jsonify({'success': False, 'error': 'Failed to load leaderboard'}), 500

if __name__ == '__main__':
    # Use environment variable for production or default to development
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)