#!/usr/bin/env bash
set -e

echo "Installing tTask..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Install dependencies
echo "Installing dependencies..."
./venv/bin/pip install -q -r requirements.txt

# Make executable
chmod +x taskjournal

# Create global ttask command
echo "Creating global command..."
INSTALL_DIR=$(pwd)
BIN_DIR="/usr/local/bin"

# Check if /usr/local/bin exists, create if needed
if [ ! -d "$BIN_DIR" ]; then
    sudo mkdir -p "$BIN_DIR"
fi

# Create symlink (will ask for password if needed)
if sudo ln -sf "$INSTALL_DIR/taskjournal" "$BIN_DIR/ttask"; then
    echo "✓ Created global 'ttask' command"
else
    echo "⚠ Could not create global command. You can create it manually:"
    echo "  sudo ln -s $INSTALL_DIR/taskjournal /usr/local/bin/ttask"
fi

echo ""
echo "✓ Installation complete!"
echo ""
echo "To run tTask:"
echo "  ttask          (from anywhere)"
echo "  ./taskjournal  (from this directory)"
echo ""
