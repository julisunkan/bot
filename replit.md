# Advanced Bots Creator - Telegram Bot Creator Platform

## Overview
Advanced Bots Creator is a full-stack Flask + SQLite web application designed to empower users to create, manage, and deploy Telegram bots with advanced functionalities. The platform integrates AI automation, cryptocurrency features, and analytics. It also includes a marketplace for bot templates, simplifying bot creation and fostering a community for sharing and utilizing pre-built bot configurations. The project aims to provide a comprehensive, user-friendly environment for both novice and experienced bot developers to build sophisticated Telegram bots, including specialized applications like tap-to-earn mining games.

## User Preferences
- None specified yet

## System Architecture
The application is built on Flask 3.0.0 and utilizes SQLite for its database, chosen for its simplicity and ease of migration. The UI/UX features a responsive design using Bootstrap 5, incorporating a dark/light theme toggle, modern gradient landing pages, and an intuitive mobile-app style interface with bottom navigation.

Key technical implementations and features include:
- **User Authentication:** Secure user authentication with anonymous account generation, username/password registration, and session management.
- **Bot Management:** Core functionality for creating, cloning, and deleting Telegram bots, managing bot commands, and secure encryption of bot tokens using Fernet.
- **Template System:** A robust template library with pre-built bot templates (e.g., Airdrop, Payment, Referral, AI Chatbot, Tap-to-Earn Mining Bot). Includes advanced template management features like editing via JSON editor, importing/exporting templates as ZIP files, and applying templates to existing bots.
- **AI Integration:** Integration with the Gemini API for features like auto-reply generation, AI-suggested command responses, and intent detection, with graceful fallback mechanisms.
- **Cryptocurrency Integration:** Real-time cryptocurrency price tracking and trending coin display powered by the CoinGecko API.
- **Analytics Dashboard:** Provides bot statistics, cryptocurrency price tracking, and visual charts for monitoring performance.
- **Telegram Tap-to-Earn Mining Bot:** A full-featured game system integrated as a Telegram Mini App, including real-time mining, boosts, referral systems, tasks, and leaderboards, with robust anti-cheat and session-based authentication.
- **Security:** Password hashing using Werkzeug, Fernet encryption for bot tokens, session-based authentication, and CSRF protection.

The project structure is organized with `app.py` as the main application, a `static/` directory for CSS/JS, a `templates/` directory for HTML, a `templates_library/` for bot templates, and a `utils/` directory for database operations, AI, crypto, and Telegram API wrappers.

## External Dependencies
- **Flask 3.0.0**: Web framework.
- **requests 2.31.0**: HTTP requests.
- **werkzeug 3.0.1**: Password hashing.
- **cryptography 41.0.7**: Token encryption (Fernet).
- **openpyxl 3.1.2**: Excel export.
- **reportlab 4.0.7**: PDF generation.
- **google-generativeai 0.3.2**: Gemini AI integration.
- **CoinGecko API**: Real-time cryptocurrency prices.
- **Telegram Bot API**: Bot token verification and interaction.