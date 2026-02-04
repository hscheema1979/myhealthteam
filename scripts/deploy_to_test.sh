#!/bin/bash
# ============================================
# Deploy to Test Instance on VPS2
# Usage: ./scripts/deploy_to_test.sh
# ============================================

set -e

TEST_DOMAIN="test.myhealthteam.org"
TEST_APP_DIR="/opt/test_myhealthteam"

echo "=========================================="
echo "Deploying to Test Instance"
echo "=========================================="
echo ""

# Check if we're on test branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "test" ]; then
    echo "WARNING: You are on branch '$CURRENT_BRANCH', not 'test'"
    echo "Continue anyway? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

echo "Deploying branch: $CURRENT_BRANCH"
echo ""

# Deploy to VPS2
ssh server2 << EOF
    echo "[1/3] Pulling latest code..."
    cd $TEST_APP_DIR
    git fetch origin
    git checkout $CURRENT_BRANCH 2>/dev/null || git checkout -b $CURRENT_BRANCH origin/$CURRENT_BRANCH
    git pull origin $CURRENT_BRANCH

    echo "[2/4] Syncing database from production..."
    cp /opt/myhealthteam/production.db /opt/test_myhealthteam/test.db
    echo "Database synced."

    echo "[3/4] Installing dependencies..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt

    echo "[4/4] Restarting service..."
    sudo systemctl restart myhealthteam-test

    # Wait for service to start
    sleep 2

    # Check status
    if systemctl is-active --quiet myhealthteam-test; then
        echo "SUCCESS: Service is running"
    else
        echo "ERROR: Service failed to start"
        sudo systemctl status myhealthteam-test --no-pager -l
        exit 1
    fi
EOF

echo ""
echo "=========================================="
echo "Deploy Complete!"
echo "=========================================="
echo ""
echo "Test instance: https://$TEST_DOMAIN"
echo "View logs: ssh server2 'sudo journalctl -u myhealthteam-test -f'"
echo ""
