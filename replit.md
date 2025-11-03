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

10. **Template Management** (NEW - November 3, 2025)
   - Edit templates directly from marketplace with JSON editor
   - Real-time JSON validation
   - Export templates as .zip files (includes template JSON + metadata)
   - Import custom templates from .zip files
   - Apply templates to existing bots (replaces all commands)
   - Easy-to-modify JSON configuration format
   - Dynamic template loading (imported templates appear immediately)

8. **UI/UX**
   - Responsive Bootstrap 5 design
   - Dark/Light theme toggle (persists in localStorage)
   - Modern gradient landing page
   - Intuitive navigation

9. **Telegram Tap-to-Earn Mining Bot** (NEW - November 3, 2025)
   - Full-featured tap-to-earn mining game for Telegram Mini Apps
   - Real-time coin mining with energy system
   - Boost system (Energy Limit, Multi-Tap, Recharge Speed)
   - Referral system with friend rewards
   - Task completion system for bonus coins
   - Leaderboard with global rankings
   - Secure session-based authentication with HMAC validation
   - Anti-cheat protection (server-side validation, session expiry)
   - Beautiful mobile-first UI with animations
   - Webhook integration for bot commands
   - One-click bot deployment from bot detail page

## Database Schema

### Tables
- `users`: User accounts (id, username, password_hash, wallet_address, referral_code, plan)
- `bots`: User-created bots (id, user_id, bot_name, bot_token, bot_config, is_active, webhook_url)
- `templates`: Bot templates (id, title, description, category, json_file, rating, downloads)
- `bot_commands`: Bot command definitions (id, bot_id, command, response_type, response_content)
- `analytics`: Bot analytics (id, bot_id, message_count, active_users, date)
- `referrals`: Referral tracking (id, referrer_id, referred_id, credits_earned)
- `template_ratings`: User ratings for templates (id, template_id, user_id, rating, review)

### Mining Bot Tables (NEW)
- `game_sessions`: Session tokens (id, player_id, session_token, created_at, expires_at)
- `mining_players`: Player profiles (id, bot_id, telegram_user_id, username, first_name, coins, energy, energy_max, last_energy_update, coins_per_tap, energy_recharge_rate)
- `mining_boosts`: Boost definitions (id, bot_id, boost_type, level, cost, effect_type, effect_value)
- `player_boosts`: Player-owned boosts (id, player_id, boost_id, purchased_at)
- `mining_tasks`: Task definitions (id, bot_id, task_type, title, description, reward_coins, requirements)
- `completed_tasks`: Completed tasks (id, player_id, task_id, completed_at)
- `mining_referrals`: Referral tracking (id, bot_id, referrer_telegram_id, referred_telegram_id, reward_coins, created_at)

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
│   ├── edit_template.html     # Template editor (NEW)
│   ├── import_template.html   # Template importer (NEW)
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
- November 3, 2025: **NEW FEATURE - Advanced Template Management**
  - Template editor with JSON syntax highlighting and real-time validation
  - Export templates as .zip packages with metadata
  - Import custom templates from .zip files
  - Apply templates to existing bots (one-click command replacement)
  - Dynamic template loading - imported templates appear immediately in marketplace
  - Easy-to-modify JSON configuration format for all templates
  - Database methods for full template CRUD operations

- November 3, 2025: **MAJOR FEATURE - Telegram Tap-to-Earn Mining Bot**
  - Complete tap-to-earn game system with Telegram Mini App integration
  - Session-based authentication with HMAC signature validation
  - Server-side game state management (coins, energy, boosts)
  - Anti-cheat security: session tokens, expiry checks, bot ownership validation
  - Real-time energy regeneration system
  - Boost marketplace (Energy Limit, Multi-Tap, Recharge Speed)
  - Referral system with friend rewards
  - Task completion system with configurable rewards
  - Global leaderboard with top players
  - Webhook endpoints for bot activation and command handling
  - Beautiful mobile-first UI with smooth animations
  - One-click deployment from bot detail page
  - Security features:
    * Telegram WebApp initData HMAC validation
    * Session tokens with 24-hour expiry
    * Server-side player_id binding (no client trust)
    * Bot ownership verification on all endpoints
    * Protection against replay attacks and ID spoofing

- November 3, 2025: UI/UX Enhancement - Animated Landing Page
  - Removed "Register" button from landing page
  - Replaced action buttons with animated circular icons
  - Added colorful animations: floating, bouncing, pulsing, sliding
  - Implemented glassmorphism effects on feature cards
  - Added rotating colorful icons to feature list (brain, bitcoin, grid, graph)
  - Continuous pulse-glow animations on action buttons
  - Ripple hover effects on circular icon buttons
  - Staggered slide-in animations for feature items
  - All animations are CSS-based for optimal performance

- November 3, 2025: Responsive Design Implementation
  - Adaptive container sizing (mobile → tablet → desktop → large desktop)
  - Responsive card grid: 2 columns (mobile) → 3 columns (tablet) → 4 columns (desktop)
  - Scalable bottom navigation (icons and text adapt to screen size)
  - Responsive typography and spacing across all breakpoints
  - Mobile-first approach with progressive enhancement
  - Breakpoints: 576px, 768px, 992px, 1200px

- November 3, 2025: Mobile-App Style Interface
  - Transformed to mobile-app aesthetic with bottom footer navigation
  - Colorful gradient cards throughout dashboard (red, blue, green, yellow)
  - Bottom navigation menu (Home, Create, Market, Analytics, Settings)
  - Improved accessibility with high-contrast navigation icons
  - Conditional bottom padding only when logged in

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
