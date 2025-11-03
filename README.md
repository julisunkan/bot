# BotForge Pro

A full-stack Telegram Bot Creator Platform with AI automation, cryptocurrency integration, and analytics.

## Features

- **Bot Management**: Create, manage, and deploy Telegram bots with ease
- **AI Integration**: Gemini-powered auto-reply generation and smart suggestions
- **Crypto Tracking**: Real-time cryptocurrency prices via CoinGecko API
- **Template Marketplace**: 5 pre-built bot templates ready to clone
- **Analytics Dashboard**: Track bot performance and crypto market data
- **Dark/Light Theme**: Toggle between themes with persistent preferences

## Quick Start

1. **Generate an Account**: Click "Generate Account" for instant access
2. **Browse Templates**: Explore pre-built bot templates in the marketplace
3. **Create Your Bot**: Get a token from @BotFather on Telegram
4. **Add Commands**: Build your bot with custom commands and responses
5. **Export & Deploy**: Download your bot configuration as JSON

## Templates Included

1. **Airdrop Bot** - Crypto airdrop distribution with referral system
2. **Payment Bot** - Cryptocurrency payment processing
3. **Referral Bot** - Referral tracking with rewards and leaderboard
4. **NFT Verification Bot** - Verify NFT ownership for exclusive access
5. **AI Chat Bot** - Intelligent conversations powered by AI

## Tech Stack

- **Backend**: Flask 3.0.0 + SQLite
- **Frontend**: Bootstrap 5 + Vanilla JavaScript
- **AI**: Google Gemini API
- **Crypto**: CoinGecko API
- **Security**: Fernet encryption for bot tokens

## Installation

```bash
pip install -r requirements.txt
python app.py
```

The app will run on http://localhost:5000

## Environment Variables

- `SESSION_SECRET` - Flask session secret (optional, auto-generated)
- `GEMINI_API_KEY` - Gemini API key for AI features (optional)

## Project Structure

```
├── app.py                    # Main Flask application
├── utils/                    # Utility modules
│   ├── database.py          # Database operations
│   ├── ai.py                # AI integration
│   ├── crypto.py            # Crypto API wrapper
│   └── telegram_api.py      # Telegram Bot API
├── templates/               # HTML templates
├── templates_library/       # Bot template JSON files
└── static/                  # CSS and JavaScript
```

## Security

- Passwords hashed with werkzeug
- Bot tokens encrypted with Fernet (AES-128)
- Session-based authentication
- SQLite with foreign key constraints

## License

MIT License - Feel free to use this for educational purposes.

## Support

For issues or questions, please check the documentation in `replit.md`.
