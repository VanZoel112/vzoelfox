#!/bin/bash

# Deploy VzoelFox to new AWS instance
# Usage: ./deploy-to-aws.sh <aws-ip> <key-path>

set -e

AWS_IP="${1:-13.236.95.51}"
KEY_PATH="${2:-~/keys/vzoel-key.pem}"
REMOTE_USER="ubuntu"
REMOTE_DIR="/home/ubuntu/vzoelfox"

echo "🚀 Starting deployment to AWS instance: $AWS_IP"

# Check if key file exists
if [ ! -f "$KEY_PATH" ]; then
    echo "❌ SSH key not found: $KEY_PATH"
    exit 1
fi

# Test SSH connection
echo "🔍 Testing SSH connection..."
if ! ssh -i "$KEY_PATH" -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$REMOTE_USER@$AWS_IP" 'echo "SSH connection successful"'; then
    echo "❌ SSH connection failed"
    exit 1
fi

echo "✅ SSH connection successful"

# Clean up remote directory first
echo "🧹 Cleaning remote directory..."
ssh -i "$KEY_PATH" "$REMOTE_USER@$AWS_IP" "rm -rf $REMOTE_DIR && mkdir -p $REMOTE_DIR"

# Copy files with proper line endings
echo "📁 Copying files..."
rsync -avz --delete \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.claude' \
    --exclude='.npm' \
    --exclude='node_modules' \
    --exclude='vzoelfox-backup' \
    --exclude='vzoelubot' \
    --exclude='*.db' \
    --exclude='*.session' \
    -e "ssh -i $KEY_PATH -o StrictHostKeyChecking=no" \
    ./ "$REMOTE_USER@$AWS_IP:$REMOTE_DIR/"

echo "🔧 Setting up environment on AWS..."
ssh -i "$KEY_PATH" "$REMOTE_USER@$AWS_IP" << 'EOF'
cd /home/ubuntu/vzoelfox

# Convert line endings to Unix format
find . -name "*.py" -type f -exec dos2unix {} \; 2>/dev/null || true

# Check Python syntax
echo "🐍 Checking Python syntax..."
python3 -m py_compile main.py
if [ $? -eq 0 ]; then
    echo "✅ main.py syntax is valid"
else
    echo "❌ main.py has syntax errors"
    exit 1
fi

# Check for required files
if [ ! -f "main.py" ]; then
    echo "❌ main.py not found"
    exit 1
fi

if [ ! -d "plugins" ]; then
    echo "❌ plugins directory not found"
    exit 1
fi

# Install Python packages
echo "📦 Installing Python packages..."
echo "Installing from requirements.txt..."
pip3 install --user -r requirements.txt

# Set permissions
chmod +x main.py
chmod -R 755 plugins/
chmod -R 755 utils/ 2>/dev/null || true

# Test import
echo "🔍 Testing Python imports..."
python3 -c "
import sys
sys.path.append('.')
try:
    import telethon
    print('✅ Telethon import successful')
    
    import main
    print('✅ Main module import successful')
    
    print('✅ All imports successful')
except Exception as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

echo "✅ AWS deployment setup completed"
EOF

if [ $? -eq 0 ]; then
    echo "🎉 Deployment successful!"
    echo "📝 To run the bot:"
    echo "   ssh -i $KEY_PATH $REMOTE_USER@$AWS_IP"
    echo "   cd $REMOTE_DIR"
    echo "   python3 main.py"
else
    echo "❌ Deployment failed"
    exit 1
fi