#!/bin/bash
# Deploy onboarding patient_status fix to VPS2
# This script will:
# 1. Upload fixed files to VPS2
# 2. Run the migration to add missing columns
# 3. Upload the fixed transform script
# 4. Restart the service

set -e  # Exit on any error

# VPS2 Configuration - UPDATE THESE
VPS2_USER="user"
VPS2_HOST="vps2"
VPS2_PATH="/path/to/myhealthteam2/Dev"  # UPDATE THIS PATH

# Local files to upload
FILES_TO_UPLOAD=(
    "fix_vps2_patient_status_column.py"
    "transform_production_data_v3_fixed.py"
)

echo "=========================================="
echo "VPS2 Onboarding Fix Deployment"
echo "=========================================="
echo ""

# Step 1: Upload files
echo "Step 1: Uploading fixed files to VPS2..."
for file in "${FILES_TO_UPLOAD[@]}"; do
    if [ -f "$file" ]; then
        echo "  Uploading $file..."
        scp "$file" "${VPS2_USER}@${VPS2_HOST}:${VPS2_PATH}/"
    else
        echo "  ERROR: File $file not found!"
        exit 1
    fi
done
echo "  ✓ All files uploaded"
echo ""

# Step 2: Run migration on VPS2
echo "Step 2: Running migration on VPS2..."
ssh "${VPS2_USER}@${VPS2_HOST}" << EOF
    cd ${VPS2_PATH}
    echo "  Running fix_vps2_patient_status_column.py..."
    python3 fix_vps2_patient_status_column.py
    echo "  ✓ Migration completed"
EOF
echo ""

# Step 3: Restart service
echo "Step 3: Restarting service on VPS2..."
ssh "${VPS2_USER}@${VPS2_HOST}" << EOF
    echo "  Restarting myhealthteam service..."
    systemctl restart myhealthteam
    echo "  ✓ Service restarted"
    
    # Check service status
    echo "  Checking service status..."
    systemctl status myhealthteam --no-pager -l
EOF
echo ""

echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Please verify the onboarding queue is working by:"
echo "1. Opening your application in browser"
echo "2. Navigating to Onboarding Queue"
echo "3. Confirming no 'no such column' error appears"
echo ""
