# AN6001 Group Project: Smart Dashboard

![Vercel](https://img.shields.io/badge/vercel-%23000000.svg?style=for-the-badge&logo=vercel&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)

A personal finance dashboard application with AI-powered chat assistance, built with Flask and deployed on Vercel with Neon Postgres database.

🔗 **[Deployed Web](https://smartdashboard-five.vercel.app/)**
(login username **vedika** and password **test123** to test existing account)

## Features

- 🔐 **User Authentication & Session Management** - Handles secure registration and login using Flask sessions
- 💬 **Chatbot Assistant** - Processes natural language messages via the chat route
- 💰 **Transaction Management** - Allows users to add and store financial records (date, amount, category, merchant)
- 📊 **Financial Analytics Dashboard** - Aggregates data for category and monthly spending views
- 🔮 **What-If Spending Simulation** - Predicts financial outcomes based on hypothetical budget changes

## Tech Stack

- **Backend**: Python, Flask
- **Database**: Neon Postgres (serverless)
- **Deployment**: Vercel
- **Frontend**: HTML, CSS, JavaScript
- **Database Driver**: psycopg2

## Project Structure

```
.
├── app.py                        # Main Flask application
├── requirements.txt              # Python dependencies
├── .gitignore                    # Git ignore file
├── README.md                     # Project documentation
├── VERCEL_POSTGRES_SETUP.md      # Vercel Postgres setup guide
├── data/
│   ├── chat_history.csv          # Chat history data
│   ├── users.csv                 # User data (CSV format)
│   ├── users.db                  # SQLite database (local development)
│   └── users.json                # Initial data (migrated to Postgres on first run)
├── static/
│   ├── analytics.js              # Analytics JavaScript
│   ├── chatbot.js                # Chatbot functionality
│   ├── style.css                 # Main stylesheet
│   └── images/                   # Image assets
├── templates/
│   ├── add_transaction.html      # Add transaction page
│   ├── analytics.html            # Analytics dashboard
│   ├── dashboard.html            # Main dashboard
│   └── login.html                # Login page
└── utils/                        # Utility functions
    ├── analytics_context.py      # Analytics context processor
    ├── auth.py                   # Authentication utilities
    ├── chatbot.py                # Chatbot logic
    ├── data_store.py             # Database operations and data management
    ├── finance.py                # Finance calculations
    ├── llm_test.py               # LLM testing utilities
    └── what_if.py                # What-if scenario analysis
```

## Setup

### Prerequisites

- Python 3.9+
- Vercel account
- Neon Postgres account (or get one through Vercel integration)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/smartdashboard.git
   cd smartdashboard
   ```
   
   Or try the live demo at: https://smartdashboard-five.vercel.app/

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   
   Create a `.env` file:
   ```env
   DATABASE_URL=postgresql://user:password@host/database?sslmode=require
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

   The app will be available at `http://localhost:5000`

### Deploy to Vercel

1. **Install Vercel CLI** (optional)
   ```bash
   npm i -g vercel
   ```

2. **Connect to Vercel**
   ```bash
   vercel
   ```

3. **Add Neon Integration**
   - Go to [Vercel Marketplace - Neon](https://vercel.com/integrations/neon)
   - Click "Add Integration"
   - Select your project
   - This automatically sets up all database environment variables

4. **Deploy**
   ```bash
   git push origin main
   ```
   
   Or use Vercel CLI:
   ```bash
   vercel --prod
   ```

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    username TEXT PRIMARY KEY,
    password TEXT,
    profile JSONB DEFAULT '{}',
    accounts JSONB DEFAULT '{}',
    chat_history JSONB DEFAULT '[]'
);
```

### Transactions Table
```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    username TEXT REFERENCES users(username) ON DELETE CASCADE,
    date TEXT,
    amount REAL,
    category TEXT,
    merchant TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Environment Variables

The following environment variables are automatically set by the Neon integration:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Pooled Postgres connection string (recommended) |
| `DATABASE_URL_UNPOOLED` | Direct Postgres connection |
| `POSTGRES_HOST` | Database host |
| `POSTGRES_DATABASE` | Database name (neon-green-garden) |
| `POSTGRES_USER` | Database user |
| `POSTGRES_PASSWORD` | Database password |

## Data Migration

On first run, the application will:
1. Create necessary database tables
2. Check for existing `data/users.json` file
3. Automatically migrate JSON data to Postgres
4. All subsequent operations use Postgres

## API Functions

### Data Store (`utils/data_store.py`)

```python
from utils.data_store import load_data, load_user, save_user, save_data

# Load all users
users = load_data()

# Load specific user
user = load_user("username")

# Save user data
save_user(username, user_data)
# or
save_user(user_dict)  # if user_dict contains 'username' key

# Save all users
save_data(users_dict)
```

## Development Notes

- The app automatically initializes the database schema on startup
- JSONB columns are used for flexible data storage (profile, accounts, chat_history)
- Transactions are indexed by username for optimal query performance
- CASCADE delete ensures data integrity when users are removed

## Troubleshooting

### Database Connection Issues

If you encounter connection errors:

1. **Verify environment variables**
   ```bash
   vercel env ls
   ```

2. **Check Neon dashboard**
   - Ensure database is active
   - Verify connection string is correct

3. **Test connection locally**
   ```bash
   python -c "import psycopg2; conn = psycopg2.connect('<your-connection-string>'); print('Connected!')"
   ```

### Common Errors

**Error: `psycopg2` module not found**
```bash
pip install psycopg2-binary
```

**Error: `DATABASE_URL` not set**
- Add the Neon integration in Vercel
- Or manually add `DATABASE_URL` to environment variables

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with Flask
- Deployed on Vercel
- Database powered by Neon Postgres
- UI inspired by modern dashboard design patterns

## Support

For issues and questions:
- Open an issue on GitHub
- Check Vercel deployment logs
- Review Neon database logs in the Neon console

---

**Note**: This is a personal finance application. Always ensure proper security measures are in place before handling sensitive financial data in production.
