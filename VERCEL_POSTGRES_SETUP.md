# Vercel PostgreSQL Setup

## Deployment Steps

### 1. On Vercel Dashboard:
- Go to **Settings → Integrations** 
- Add **Vercel Postgres** integration
- This creates a PostgreSQL database and sets `DATABASE_URL` environment variable automatically

### 2. Vercel Environment:
- The `DATABASE_URL` is automatically set in your environment
- Data will persist across all requests ✓

### 3. Local Development:
For local testing with PostgreSQL:

```bash
# Option 1: Use Docker
docker run --name postgres-smart -e POSTGRES_PASSWORD=postgres -d -p 5432:5432 postgres

# Create database
docker exec postgres-smart psql -U postgres -c "CREATE DATABASE smart_dashboard;"

# Set local environment variable
export DATABASE_LOCAL_URL="postgresql://postgres:postgres@localhost/smart_dashboard"
```

Or set in `.env`:
```
DATABASE_LOCAL_URL=postgresql://postgres:postgres@localhost/smart_dashboard
```

### 4. Install Dependencies:
```bash
pip install psycopg2-binary
```

### 5. Deploy to Vercel:
```bash
git add .
git commit -m "Switch to PostgreSQL"
git push
```

Vercel will automatically:
- Read `DATABASE_URL` from Vercel Postgres
- Initialize tables on first request
- Migrate from `data/users.json` on first request

## Data Persistence
✓ **All data persists** across requests, deployments, and restarts
✓ Analytics data survives page refreshes
✓ User transactions are permanent
