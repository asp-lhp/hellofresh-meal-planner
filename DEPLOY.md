# Deploying Meal Planner to Fly.io

This guide walks you through deploying the Meal Planner to Fly.io for mobile access.

## Prerequisites

1. **Install Fly CLI**
   ```bash
   # macOS
   brew install flyctl

   # Or via curl
   curl -L https://fly.io/install.sh | sh
   ```

2. **Create Fly.io account**
   ```bash
   fly auth signup
   # Or if you have an account:
   fly auth login
   ```

## Step 1: Deploy the .NET API

```bash
cd meal-planner/api

# First time: create the app
fly launch --no-deploy

# Set any secrets if needed
# fly secrets set SOME_SECRET=value

# Deploy
fly deploy

# Note the URL (e.g., https://meal-planner-api-asp.fly.dev)
```

## Step 2: Deploy the Flask Web App

```bash
cd meal-planner

# First time: create the app
fly launch --no-deploy

# Set environment variables
fly secrets set API_BASE_URL=https://meal-planner-api-asp.fly.dev/api
fly secrets set ANTHROPIC_API_KEY=your-api-key-here

# Deploy
fly deploy

# Note the URL (e.g., https://meal-planner-asp.fly.dev)
```

## Step 3: Upload Your Database

If you have an existing recipes database:

```bash
# SSH into the running app
fly ssh console -a meal-planner-asp

# The database mount is at /app/database
# You can upload via scp or sftp
```

Or copy locally:
```bash
# Copy your local database to the Fly.io volume
fly sftp shell -a meal-planner-asp
put database/recipes.db /app/database/recipes.db
```

## Step 4: Access Your App

Open in browser:
```
https://meal-planner-asp.fly.dev
```

Or on your phone - just visit the same URL!

## Useful Commands

```bash
# View logs
fly logs -a meal-planner-asp

# SSH into container
fly ssh console -a meal-planner-asp

# Check app status
fly status -a meal-planner-asp

# Scale up/down
fly scale count 1 -a meal-planner-asp

# Open in browser
fly open -a meal-planner-asp
```

## Costs

Fly.io free tier includes:
- 3 shared-cpu-1x VMs with 256MB RAM
- 3GB persistent storage

The configuration uses:
- 512MB RAM (within free tier)
- Auto-stop when idle (saves resources)
- Auto-start on request

**Estimated cost: $0/month** on free tier (with auto-stop)

## Troubleshooting

### App not starting
```bash
fly logs -a meal-planner-asp
```

### Database not found
Make sure the volume is mounted and database exists:
```bash
fly ssh console -a meal-planner-asp
ls -la /app/database/
```

### API connection failed
Check the API_BASE_URL secret is set correctly:
```bash
fly secrets list -a meal-planner-asp
```

## Custom Domain (Optional)

```bash
# Add your domain
fly certs add yourdomain.com -a meal-planner-asp

# Then add DNS records as instructed
```
