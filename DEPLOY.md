# Deploying Meal Planner to Fly.io

Two services: .NET API + Flask Web App. Deploy the API first.

## Prerequisites

```bash
# Install Fly CLI
brew install flyctl

# Login
fly auth login
```

## Step 1: Create the Database Volume

The API needs persistent storage for SQLite.

```bash
fly volumes create meal_planner_db --region dfw --size 1 -a meal-planner-api-asp
```

## Step 2: Deploy the .NET API

```bash
cd api

# First time only: create the app
fly launch --no-deploy

# Deploy
fly deploy

# Verify it's running
fly status
fly logs
```

API will be at: `https://meal-planner-api-asp.fly.dev`

Test the health endpoint:
```bash
curl https://meal-planner-api-asp.fly.dev/health
```

## Step 3: Upload Your Database

```bash
# SSH into the API container
fly ssh console -a meal-planner-api-asp

# Check the mount
ls -la /app/data/

# Exit
exit
```

Upload your local database:
```bash
fly sftp shell -a meal-planner-api-asp
put ../database/recipes.db /app/data/recipes.db
exit
```

Or use scp:
```bash
fly ssh sftp shell -a meal-planner-api-asp
# Then: put database/recipes.db /app/data/recipes.db
```

## Step 4: Deploy the Flask Web App

```bash
cd ..  # Back to project root

# Set secrets (Google OAuth + Flask secret key)
fly secrets set \
  GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com \
  GOOGLE_CLIENT_SECRET=your-client-secret \
  SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Deploy
fly deploy

# Verify
fly status
fly logs
```

Web app will be at: `https://meal-planner-asp.fly.dev`

## Step 5: Configure Google OAuth

Add the production callback URL to Google Cloud Console:

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials
2. Edit your OAuth 2.0 Client ID
3. Add Authorized redirect URI: `https://meal-planner-asp.fly.dev/auth/google/callback`
4. Save

## Step 6: Test Everything

1. Visit `https://meal-planner-asp.fly.dev`
2. Click "Sign in with Google"
3. Browse recipes, create a meal plan
4. Check the shopping list

---

## Useful Commands

```bash
# View logs
fly logs -a meal-planner-asp
fly logs -a meal-planner-api-asp

# SSH into containers
fly ssh console -a meal-planner-asp
fly ssh console -a meal-planner-api-asp

# Check status
fly status -a meal-planner-asp
fly status -a meal-planner-api-asp

# Restart
fly apps restart meal-planner-asp

# Open in browser
fly open -a meal-planner-asp

# Update secrets
fly secrets set KEY=value -a meal-planner-asp

# List secrets
fly secrets list -a meal-planner-asp
```

---

## Custom Domain (Optional)

```bash
# Add your domain
fly certs add meals.yourdomain.com -a meal-planner-asp

# Add DNS records as instructed (CNAME to fly.dev)
```

Then update Google OAuth redirect URI to include your custom domain.

---

## Costs

Fly.io free tier:
- 3 shared-cpu-1x VMs with 256MB RAM
- 3GB persistent storage

Your config uses:
- 512MB RAM per service (may exceed free tier)
- Auto-stop when idle (saves money)

**Estimated: $0-5/month** depending on usage.

To stay on free tier, reduce memory to 256MB in fly.toml files.

---

## Troubleshooting

### API not connecting to database
```bash
fly ssh console -a meal-planner-api-asp
ls -la /app/data/
# Should show recipes.db
```

### Web app can't reach API
```bash
# Check the API is running
curl https://meal-planner-api-asp.fly.dev/health

# Check API_BASE_URL is set
fly secrets list -a meal-planner-asp
```

### Google OAuth not working
- Check redirect URI matches exactly (including https)
- Check GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are set
- Check Flask logs: `fly logs -a meal-planner-asp`

### Container keeps restarting
```bash
fly logs -a meal-planner-asp
# Look for startup errors
```
