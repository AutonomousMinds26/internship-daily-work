#!/bin/bash
set -e

# ─────────────────────────────────────────────
#  RecruiterAI — Railway Deployment Script
#  Run this ONCE after signing in to a fresh
#  Railway account.
#
#  Usage:
#    export RAILWAY_TOKEN=xxxx   ← paste your token
#    bash deploy_railway.sh
# ─────────────────────────────────────────────

if [ -z "$RAILWAY_TOKEN" ]; then
  echo "❌  RAILWAY_TOKEN is not set."
  echo "    Get it from: https://railway.com/account/tokens"
  echo "    Then run:  export RAILWAY_TOKEN=your_token_here"
  exit 1
fi

ROOT="$(cd "$(dirname "$0")" && pwd)"
echo "📁  Project root: $ROOT"

# ── 1. Create project ──────────────────────────────────────────
echo ""
echo "🚂  Creating Railway project 'recruiterai'..."
cd "$ROOT"
railway init --name "recruiterai"

# ── 2. Add PostgreSQL plugin ────────────────────────────────────
echo ""
echo "🐘  Adding PostgreSQL database..."
railway add --plugin postgresql

# ── 3. Add Redis plugin ─────────────────────────────────────────
echo ""
echo "🔴  Adding Redis..."
railway add --plugin redis

# ── 4. Deploy Backend ───────────────────────────────────────────
echo ""
echo "⚙️   Deploying backend service..."
cd "$ROOT/backend"
railway service create --name "recruiterai-backend"
railway variables set \
  USE_MOCK_APIS=true \
  LLM_PROVIDER=groq \
  JWT_SECRET="$(openssl rand -hex 32)"
railway up --detach --service "recruiterai-backend"

# ── 5. Get backend URL ──────────────────────────────────────────
echo ""
echo "🌐  Getting backend domain..."
sleep 5
BACKEND_URL=$(railway domain --service "recruiterai-backend" 2>/dev/null || echo "")
if [ -z "$BACKEND_URL" ]; then
  echo "⚠️   Could not auto-detect backend URL."
  echo "     Open https://railway.com/dashboard, find recruiterai-backend, copy its domain."
  read -p "Paste backend URL here (e.g. https://xxx.up.railway.app): " BACKEND_URL
fi
echo "✅  Backend URL: $BACKEND_URL"

# ── 6. Deploy Frontend ──────────────────────────────────────────
echo ""
echo "🎨  Deploying frontend service..."
cd "$ROOT/frontend"
railway service create --name "recruiterai-frontend"
railway variables set \
  VITE_API_BASE_URL="$BACKEND_URL" \
  PORT=80
railway up --detach --service "recruiterai-frontend"

# ── 7. Print URLs ───────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉  Deployment complete!"
echo ""
echo "   Backend  → $BACKEND_URL"
echo "   Frontend → Check https://railway.com/dashboard → recruiterai-frontend → Settings → Domain"
echo ""
echo "   Default login:"
echo "     Admin:     admin_user / admin_password"
echo "     Recruiter: recruiter_user / recruiter_password"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
