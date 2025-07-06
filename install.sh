#!/bin/bash
# CommandState Installation Script

echo "🚀 Installing CommandState - Modern Process Monitor"
echo "=================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.7 or higher and try again."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully!"
    echo ""
    echo "🎉 CommandState is ready to use!"
    echo ""
    echo "Usage:"
    echo "  python3 commandstate.py          # Run modern version"
    echo "  python3 commandstate_classic.py  # Run classic version"
    echo ""
    echo "Keyboard shortcuts:"
    echo "  q     - Quit"
    echo "  r     - Refresh"
    echo "  k     - Kill process (SIGKILL)"
    echo "  t     - Terminate process (SIGTERM)"
    echo ""
    echo "Happy monitoring! 🔍"
else
    echo "❌ Failed to install dependencies."
    echo "Please check your internet connection and try again."
    exit 1
fi
