import sqlite3
import secrets
from datetime import datetime
from cryptography.fernet import Fernet
from werkzeug.security import generate_password_hash, check_password_hash

class Database:
    def __init__(self, db_path='database.db'):
        self.db_path = db_path
        self.encryption_key = self._get_or_create_key()
        self.cipher = Fernet(self.encryption_key)
        self.init_db()
    
    def _get_or_create_key(self):
        try:
            with open('.encryption_key', 'rb') as f:
                return f.read()
        except FileNotFoundError:
            key = Fernet.generate_key()
            with open('.encryption_key', 'wb') as f:
                f.write(key)
            return key
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        return conn
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                wallet_address TEXT,
                referral_code TEXT UNIQUE NOT NULL,
                referred_by TEXT,
                plan TEXT DEFAULT 'free',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                bot_name TEXT NOT NULL,
                bot_token TEXT NOT NULL,
                bot_username TEXT,
                bot_config TEXT,
                bot_type TEXT DEFAULT 'telegram',
                webhook_url TEXT,
                is_active INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Migration: Add bot_type column if it doesn't exist
        try:
            cursor.execute("SELECT bot_type FROM bots LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE bots ADD COLUMN bot_type TEXT DEFAULT 'telegram'")
            conn.commit()
        
        # Migration: Add is_active column if it doesn't exist
        try:
            cursor.execute("SELECT is_active FROM bots LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE bots ADD COLUMN is_active INTEGER DEFAULT 0")
            conn.commit()
        
        # Migration: Add webhook_url column if it doesn't exist
        try:
            cursor.execute("SELECT webhook_url FROM bots LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE bots ADD COLUMN webhook_url TEXT")
            conn.commit()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                json_file TEXT NOT NULL,
                rating REAL DEFAULT 0,
                downloads INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_id INTEGER NOT NULL,
                message_count INTEGER DEFAULT 0,
                active_users INTEGER DEFAULT 0,
                date DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE,
                UNIQUE(bot_id, date)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL,
                credits_earned INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users(id),
                FOREIGN KEY (referred_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_id INTEGER NOT NULL,
                command TEXT NOT NULL,
                response_type TEXT DEFAULT 'text',
                response_content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS template_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                review TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (template_id) REFERENCES templates(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(template_id, user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY (player_id) REFERENCES mining_players(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mining_players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_id INTEGER NOT NULL,
                telegram_user_id INTEGER NOT NULL,
                username TEXT,
                first_name TEXT,
                coins REAL DEFAULT 0,
                energy INTEGER DEFAULT 1000,
                energy_max INTEGER DEFAULT 1000,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                coins_per_tap INTEGER DEFAULT 1,
                energy_recharge_rate INTEGER DEFAULT 1,
                auto_miner_enabled INTEGER DEFAULT 0,
                total_taps INTEGER DEFAULT 0,
                combo_record INTEGER DEFAULT 1,
                streak_days INTEGER DEFAULT 1,
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                referral_earnings REAL DEFAULT 0,
                last_tap_time TIMESTAMP,
                last_energy_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE,
                UNIQUE(bot_id, telegram_user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mining_boosts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                boost_type TEXT NOT NULL,
                boost_level INTEGER DEFAULT 1,
                purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES mining_players(id) ON DELETE CASCADE,
                UNIQUE(player_id, boost_type)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mining_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                task_type TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                reward_claimed INTEGER DEFAULT 0,
                progress INTEGER DEFAULT 0,
                completed_at TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES mining_players(id) ON DELETE CASCADE,
                UNIQUE(player_id, task_type)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mining_referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL,
                bonus_earned REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES mining_players(id) ON DELETE CASCADE,
                FOREIGN KEY (referred_id) REFERENCES mining_players(id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def encrypt_token(self, token):
        return self.cipher.encrypt(token.encode()).decode()
    
    def decrypt_token(self, encrypted_token):
        return self.cipher.decrypt(encrypted_token.encode()).decode()
    
    def create_user(self, username, password):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        password_hash = generate_password_hash(password)
        referral_code = secrets.token_urlsafe(8)
        
        try:
            cursor.execute(
                'INSERT INTO users (username, password_hash, referral_code) VALUES (?, ?, ?)',
                (username, password_hash, referral_code)
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return user_id, referral_code
        except sqlite3.IntegrityError:
            conn.close()
            return None, None
    
    def verify_user(self, username, password):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            return dict(user)
        return None
    
    def get_user(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
    def create_bot(self, user_id, bot_name, bot_token, bot_config, bot_type='telegram'):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        encrypted_token = self.encrypt_token(bot_token) if bot_token else ''
        
        cursor.execute(
            'INSERT INTO bots (user_id, bot_name, bot_token, bot_config, bot_type) VALUES (?, ?, ?, ?, ?)',
            (user_id, bot_name, encrypted_token, bot_config, bot_type)
        )
        conn.commit()
        bot_id = cursor.lastrowid
        conn.close()
        return bot_id
    
    def get_user_bots(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM bots WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
        bots = cursor.fetchall()
        conn.close()
        return [dict(bot) for bot in bots]
    
    def get_bot(self, bot_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM bots WHERE id = ?', (bot_id,))
        bot = cursor.fetchone()
        conn.close()
        return dict(bot) if bot else None
    
    def delete_bot(self, bot_id, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM bots WHERE id = ? AND user_id = ?', (bot_id, user_id))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted
    
    def get_all_templates(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM templates ORDER BY downloads DESC, rating DESC')
        templates = cursor.fetchall()
        conn.close()
        return [dict(template) for template in templates]
    
    def add_template(self, title, description, category, json_file):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO templates (title, description, category, json_file) VALUES (?, ?, ?, ?)',
            (title, description, category, json_file)
        )
        conn.commit()
        template_id = cursor.lastrowid
        conn.close()
        return template_id
    
    def increment_template_downloads(self, template_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE templates SET downloads = downloads + 1 WHERE id = ?', (template_id,))
        conn.commit()
        conn.close()
    
    def add_bot_command(self, bot_id, command, response_type, response_content):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO bot_commands (bot_id, command, response_type, response_content) VALUES (?, ?, ?, ?)',
            (bot_id, command, response_type, response_content)
        )
        conn.commit()
        conn.close()
    
    def get_bot_commands(self, bot_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM bot_commands WHERE bot_id = ?', (bot_id,))
        commands = cursor.fetchall()
        conn.close()
        return [dict(cmd) for cmd in commands]
    
    def update_bot_command(self, command_id, bot_id, command, response_type, response_content):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE bot_commands 
            SET command = ?, response_type = ?, response_content = ?
            WHERE id = ? AND bot_id = ?
        ''', (command, response_type, response_content, command_id, bot_id))
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        return updated
    
    def delete_bot_command(self, command_id, bot_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM bot_commands WHERE id = ? AND bot_id = ?', (command_id, bot_id))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted
    
    def get_analytics_summary(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as total_bots FROM bots WHERE user_id = ?', (user_id,))
        total_bots = cursor.fetchone()['total_bots']
        
        cursor.execute('''
            SELECT SUM(a.message_count) as total_messages 
            FROM analytics a 
            JOIN bots b ON a.bot_id = b.id 
            WHERE b.user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        total_messages = result['total_messages'] or 0
        
        conn.close()
        return {
            'total_bots': total_bots,
            'total_messages': total_messages
        }
    
    def increment_bot_messages(self, bot_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().date()
        
        cursor.execute('''
            INSERT INTO analytics (bot_id, message_count, date) 
            VALUES (?, 1, ?)
            ON CONFLICT(bot_id, date) DO UPDATE SET 
            message_count = message_count + 1
        ''', (bot_id, today))
        
        conn.commit()
        conn.close()
    
    def get_or_create_mining_player(self, bot_id, telegram_user_id, username=None, first_name=None, referred_by=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM mining_players WHERE bot_id = ? AND telegram_user_id = ?', 
                      (bot_id, telegram_user_id))
        player = cursor.fetchone()
        
        if player:
            conn.close()
            return dict(player)
        
        referral_code = secrets.token_urlsafe(8)
        cursor.execute('''
            INSERT INTO mining_players (bot_id, telegram_user_id, username, first_name, referral_code, referred_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (bot_id, telegram_user_id, username, first_name, referral_code, referred_by))
        
        player_id = cursor.lastrowid
        conn.commit()
        
        cursor.execute('SELECT * FROM mining_players WHERE id = ?', (player_id,))
        player = cursor.fetchone()
        conn.close()
        return dict(player)
    
    def update_mining_player_tap(self, player_id, coins_to_add, energy_cost):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE mining_players 
            SET coins = coins + ?, 
                energy = MAX(0, energy - ?),
                total_taps = total_taps + 1,
                last_tap_time = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (coins_to_add, energy_cost, player_id))
        
        conn.commit()
        
        cursor.execute('SELECT * FROM mining_players WHERE id = ?', (player_id,))
        player = cursor.fetchone()
        conn.close()
        return dict(player) if player else None
    
    def update_player_energy(self, player_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT *, 
            (julianday('now') - julianday(last_energy_update)) * 86400 as seconds_passed
            FROM mining_players WHERE id = ?
        ''', (player_id,))
        player = cursor.fetchone()
        
        if player:
            seconds_passed = player['seconds_passed']
            energy_recovered = int(seconds_passed * player['energy_recharge_rate'])
            new_energy = min(player['energy'] + energy_recovered, player['energy_max'])
            
            cursor.execute('''
                UPDATE mining_players 
                SET energy = ?,
                    last_energy_update = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_energy, player_id))
            conn.commit()
        
        cursor.execute('SELECT * FROM mining_players WHERE id = ?', (player_id,))
        player = cursor.fetchone()
        conn.close()
        return dict(player) if player else None
    
    def purchase_boost(self, player_id, boost_type, cost, boost_effects):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT coins FROM mining_players WHERE id = ?', (player_id,))
        player = cursor.fetchone()
        
        if not player or player['coins'] < cost:
            conn.close()
            return {'success': False, 'error': 'Insufficient coins'}
        
        cursor.execute('UPDATE mining_players SET coins = coins - ? WHERE id = ?', (cost, player_id))
        
        update_fields = []
        update_values = []
        for field, value in boost_effects.items():
            update_fields.append(f'{field} = {field} + ?')
            update_values.append(value)
        
        if update_fields:
            update_values.append(player_id)
            cursor.execute(f'UPDATE mining_players SET {", ".join(update_fields)} WHERE id = ?', update_values)
        
        cursor.execute('''
            INSERT INTO mining_boosts (player_id, boost_type) 
            VALUES (?, ?)
            ON CONFLICT(player_id, boost_type) DO UPDATE SET 
            boost_level = boost_level + 1,
            purchased_at = CURRENT_TIMESTAMP
        ''', (player_id, boost_type))
        
        conn.commit()
        cursor.execute('SELECT * FROM mining_players WHERE id = ?', (player_id,))
        player = cursor.fetchone()
        conn.close()
        return {'success': True, 'player': dict(player)}
    
    def get_mining_leaderboard(self, bot_id, limit=10):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT username, first_name, coins, level, total_taps
            FROM mining_players 
            WHERE bot_id = ?
            ORDER BY coins DESC
            LIMIT ?
        ''', (bot_id, limit))
        
        leaderboard = cursor.fetchall()
        conn.close()
        return [dict(entry) for entry in leaderboard]
    
    def activate_bot(self, bot_id, webhook_url):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE bots 
            SET is_active = 1, webhook_url = ?
            WHERE id = ?
        ''', (webhook_url, bot_id))
        
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        return updated
    
    def create_game_session(self, player_id, session_token):
        from datetime import timedelta
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        expires_at = datetime.now() + timedelta(hours=24)
        
        cursor.execute('''
            INSERT INTO game_sessions (player_id, session_token, expires_at)
            VALUES (?, ?, ?)
        ''', (player_id, session_token, expires_at))
        
        conn.commit()
        conn.close()
    
    def validate_game_session(self, session_token):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT player_id FROM game_sessions 
            WHERE session_token = ? AND expires_at > CURRENT_TIMESTAMP
        ''', (session_token,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result['player_id'] if result else None
