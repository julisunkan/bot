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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
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
                FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE
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
    
    def create_bot(self, user_id, bot_name, bot_token, bot_config):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        encrypted_token = self.encrypt_token(bot_token)
        
        cursor.execute(
            'INSERT INTO bots (user_id, bot_name, bot_token, bot_config) VALUES (?, ?, ?, ?)',
            (user_id, bot_name, encrypted_token, bot_config)
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
