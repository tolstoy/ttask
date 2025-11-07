#!/usr/bin/env bash
set -e

echo "Installing Task Journal..."

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

echo ""
echo "✓ Installation complete!"
echo ""
echo "To run Task Journal:"
echo "  ./taskjournal"
echo ""
echo "Or add to your PATH:"
echo "  ln -s $(pwd)/taskjournal /usr/local/bin/taskjournal"
echo ""
