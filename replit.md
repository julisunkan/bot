# BotForge Pro - Telegram Bot Creator Platform

## Overview
BotForge Pro is a full-stack Flask + SQLite web application for creating and managing Telegram bots with AI automation, cryptocurrency integration, analytics, and a marketplace for bot templates.

## Project Status
- **Status**: MVP Complete (November 3, 2025)
- **Version**: 1.0.0
- **Framework**: Flask 3.0.0 + SQLite
- **Language**: Python 3.11

## Features Implemented

### Core Features (MVP)
1. **User Authentication System**
   - Anonymous account generation
   - Username/password registration
   - Secure session management
   - Referral code system

2. **Bot Management**
   - Create/delete/clone Telegram bots
   - Bot token verification via Telegram API
   - Command management (add/edit bot commands)
   - Export bot configurations as JSON
   - Encrypted bot token storage using Fernet

3. **Template Library**
   - 5 Pre-built bot templates:
     - Airdrop Bot (crypto airdrop distribution)
     - Payment Bot (cryptocurrency payments)
     - Referral Bot (referral tracking & rewards)
     - NFT Verification Bot (NFT ownership verification)
     - AI Chat Bot (intelligent conversations)

4. **AI Integration**
   - Gemini API integration for auto-reply generation
   - AI-suggested command responses
   - Intent detection (keywords: price, buy, claim, help, balance)
   - Fallback responses when AI unavailable

5. **Crypto Integration**
   - CoinGecko API for real-time cryptocurrency prices
   - Multi-coin price tracking (BTC, ETH, BNB)
   - Trending coins display
   - Global crypto market statistics

6. **Analytics Dashboard**
   - Bot statistics (total bots, messages)
   - Cryptocurrency price tracking
   - Visual charts and metrics
   - Export capabilities (planned)

7. **Marketplace**
   - Browse community templates
   - Clone templates instantly
   - Template ratings and downloads tracking
   - Preview templates before cloning

8. **UI/UX**
   - Responsive Bootstrap 5 design
   - Dark/Light theme toggle (persists in localStorage)
   - Modern gradient landing page
   - Intuitive navigation

## Database Schema

### Tables
- `users`: User accounts (id, username, password_hash, wallet_address, referral_code, plan)
- `bots`: User-created bots (id, user_id, bot_name, bot_token, bot_config)
- `templates`: Bot templates (id, title, description, category, json_file, rating, downloads)
- `bot_commands`: Bot command definitions (id, bot_id, command, response_type, response_content)
- `analytics`: Bot analytics (id, bot_id, message_count, active_users, date)
- `referrals`: Referral tracking (id, referrer_id, referred_id, credits_earned)
- `template_ratings`: User ratings for templates (id, template_id, user_id, rating, review)

## Project Structure
```
/
├── app.py                      # Main Flask application
├── database.db                 # SQLite database (auto-created)
├── requirements.txt            # Python dependencies
├── .gitignore                 # Git ignore rules
├── .encryption_key            # Fernet encryption key (auto-generated)
├── static/
│   ├── css/
│   │   └── style.css          # Custom styles with dark/light theme
│   └── js/
│       └── main.js            # Theme toggle & utilities
├── templates/
│   ├── base.html              # Base template with navbar
│   ├── index.html             # Landing page
│   ├── login.html             # Login/register page
│   ├── dashboard.html         # User dashboard
│   ├── create_bot.html        # Bot creation form
│   ├── bot_detail.html        # Bot management & commands
│   ├── marketplace.html       # Template marketplace
│   ├── analytics.html         # Analytics dashboard
│   └── settings.html          # User settings
├── templates_library/
│   ├── airdrop.json           # Airdrop bot template
│   ├── payment.json           # Payment bot template
│   ├── referral.json          # Referral bot template
│   ├── nft_verification.json  # NFT verification template
│   └── ai_chatbot.json        # AI chatbot template
└── utils/
    ├── database.py            # Database operations & encryption
    ├── ai.py                  # Gemini AI integration
    ├── crypto.py              # CoinGecko API wrapper
    └── telegram_api.py        # Telegram Bot API wrapper
```

## API Endpoints

### Public Routes
- `GET /` - Landing page
- `GET /login` - Login page
- `POST /login` - Login handler
- `GET /register` - Registration page
- `POST /register` - Registration handler
- `GET /generate-account` - Anonymous account creation

### Protected Routes (Login Required)
- `GET /dashboard` - User dashboard
- `GET /create-bot` - Bot creation form
- `POST /create-bot` - Create new bot
- `GET /bot/<bot_id>` - Bot details & commands
- `POST /bot/<bot_id>/add-command` - Add bot command
- `POST /bot/<bot_id>/delete` - Delete bot
- `GET /bot/<bot_id>/export` - Export bot config
- `GET /marketplace` - Template marketplace
- `GET /marketplace/clone/<template_id>` - Clone template
- `GET /analytics` - Analytics dashboard
- `GET /settings` - User settings
- `POST /settings` - Update settings

### API Routes
- `POST /api/ai/generate-response` - AI response generation
- `GET /api/crypto/price/<coin_id>` - Get crypto price
- `GET /api/templates` - List all templates
- `GET /api/bots` - List user bots

## Dependencies
- Flask 3.0.0 - Web framework
- requests 2.31.0 - HTTP requests
- werkzeug 3.0.1 - Password hashing
- cryptography 41.0.7 - Token encryption
- openpyxl 3.1.2 - Excel export
- reportlab 4.0.7 - PDF generation
- google-generativeai 0.3.2 - Gemini AI

## Environment Variables
- `SESSION_SECRET` - Flask session secret (auto-generated if not set)
- `GEMINI_API_KEY` - Optional Gemini API key for AI features

## Configuration
- **Port**: 5000
- **Host**: 0.0.0.0 (binds to all interfaces)
- **Debug Mode**: Enabled (development)
- **Database**: SQLite (database.db)
- **Max Upload Size**: 16MB

## Security Features
- Password hashing using werkzeug
- Bot tokens encrypted with Fernet (AES-128)
- Session-based authentication
- CSRF protection (Flask built-in)
- Foreign key constraints enabled

## Usage

### Quick Start
1. Click "Generate Account" for instant anonymous access
2. Browse marketplace templates
3. Create your first bot (requires Telegram bot token from @BotFather)
4. Add commands and responses
5. Export bot configurations

### Getting a Telegram Bot Token
1. Open Telegram and search for @BotFather
2. Send `/newbot` command
3. Follow instructions to name your bot
4. Copy the bot token provided
5. Paste token in BotForge Pro

## Freemium Plan Limits
- **Free Plan**: 1 bot maximum, basic templates
- **Pro Plan**: Unlimited bots, all templates, Web3 features (implementation planned)

## Future Enhancements (Next Phase)
1. Visual drag-and-drop flow editor (jsPlumb/Drawflow)
2. Full Web3 integration (WalletConnect, token transfers)
3. Real-time Telegram bot emulator preview
4. Payment processing (NowPayments sandbox)
5. Flask-SocketIO for real-time updates
6. Public REST API with rate limiting
7. 2FA authentication (email OTP/Telegram)
8. Automated backups to Google Drive
9. PWA support (manifest + service worker)
10. Multi-language support

## Development Notes
- Database auto-initializes on first run
- Templates auto-populate on startup
- Encryption key auto-generates if missing
- Theme preference persists in localStorage
- All bot tokens stored encrypted in database

## Recent Changes
- November 3, 2025: Initial MVP implementation
  - Complete authentication system
  - Bot management with command builder
  - 5 pre-built templates
  - AI integration (Gemini)
  - Crypto price tracking (CoinGecko)
  - Analytics dashboard
  - Marketplace with template cloning
  - Dark/Light theme toggle
  - Responsive Bootstrap 5 UI

## User Preferences
- None specified yet

## Architecture Decisions
- SQLite for simplicity (easy to migrate to PostgreSQL later)
- Fernet encryption for bot tokens (symmetric encryption)
- Bootstrap 5 for rapid UI development
- CoinGecko API (free tier, no auth required)
- Gemini for AI (optional, graceful fallback)
- Session-based auth (suitable for MVP)
