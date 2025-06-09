# # JUSTLearn Bot 🤖

An intelligent Telegram bot designed for Computer Science students to practice Data Structures concepts through adaptive testing and exam simulation.

## 🌟 Features

### 📚 Learning Modes
- **Adaptive Tests** - AI-powered difficulty adjustment based on performance
- **Mimic Exams** - Simulate real CS211 exams (First/Second/Final)
- **Mini Tests** - Focused practice on weak topics
- **Reevaluation Tests** - Retry failed topics with structured difficulty progression

### 🎯 Smart Features
- **Multilingual Support** - English & Arabic interface
- **Progress Tracking** - Visual charts and performance analytics
- **Weak Topic Detection** - Automatic identification and targeted practice
- **Daily Reminders** - Customizable study notifications
- **Session Management** - Resume interrupted tests

### 📊 Topics Covered
- Algorithm Analysis and Big-O Notation
- Array-Based Lists & Linked Lists
- Stacks, Queues & Recursion
- Searching and Hashing
- Binary Trees & Graphs
- Sorting Algorithms

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.8+
Telegram Bot Token (from @BotFather)
```

### Local Installation
```bash
# Clone repository
git clone https://github.com/JustLearn2025/JustLearn2025.git
cd JustLearn2025

# Install dependencies
pip install -r requirements.txt

# Run bot
python chatbot.py --token YOUR_BOT_TOKEN
```

### Railway Deployment
1. Fork this repository
2. Connect to [Railway](https://railway.app)
3. Set environment variable: `BOT_TOKEN=your_telegram_bot_token`
4. Deploy automatically

## 💻 Usage

### Basic Commands
```
/start - Welcome message and language selection
/adaptive_test - Start intelligent adaptive testing
/mimic_incamp_exam - Practice with exam simulations
/topics - View all available topics
/results - Check your performance history
/progress - View visual progress charts
/set_reminder - Set daily study reminders
/reset - Clear current session
```

### Getting Started
1. Start the bot: `/start`
2. Select your language (English/Arabic)
3. Choose a learning mode
4. Begin practicing!

## 🏗️ Architecture

```
├── chatbot.py              # Main bot logic & Telegram handlers
├── database/
│   ├── database_manager.py # SQLite operations
│   └── migrate_to_sqlite.py # JSON to SQLite migration
├── bot/
│   ├── exam_manager.py     # Exam creation & management
│   ├── search_engine.py    # FAISS-based question retrieval
│   └── user_tracker.py     # User sessions & progress
└── data/
    └── justlearn.db        # SQLite database
```

## 🛠️ Technical Stack

- **Backend**: Python 3.8+
- **Bot Framework**: python-telegram-bot
- **Database**: SQLite with JSON compatibility
- **Search**: FAISS vector similarity
- **ML**: Sentence Transformers for embeddings
- **Visualization**: Matplotlib for progress charts
- **Deployment**: Railway.app

## 📈 Data Migration

If migrating from JSON to SQLite:
```bash
python database/migrate_to_sqlite.py --data-dir data --backup-dir backup_json
```

## 🌍 Internationalization

Supports both English and Arabic with:
- RTL text support for Arabic
- Localized error messages
- Cultural adaptations for Jordanian timezone

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines
- Maintain existing functionality
- Follow Python PEP 8 style guide
- Add comments for complex logic
- Test with both languages

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support and suggestions:
- 📧 Email: just.learn.supp@gmail.com
- 🐛 Issues: [GitHub Issues](https://github.com/JustLearn2025/JustLearn2025/issues)

## 🎯 Roadmap

- [ ] Additional CS topics (Algorithms, Operating Systems)
- [ ] Voice message support
- [ ] Study groups and collaborative features
- [ ] Advanced analytics dashboard
- [ ] Mobile app companion

---

<div align="center">
  <strong>Built with ❤️ for Computer Science Education</strong>
</div>
