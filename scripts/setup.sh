#!/bin/bash

# Daily Article Scraper Setup Script
# This script sets up the development environment

set -e

echo "🚀 Setting up Daily Article Scraper..."

# Check if Python 3.8+ is installed
if ! python3 --version | grep -E "Python 3\.(8|9|10|11|12)" > /dev/null; then
    echo "❌ Python 3.8+ is required. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python version check passed"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Install development dependencies if in dev mode
if [ "$1" = "--dev" ]; then
    echo "🛠️ Installing development dependencies..."
    pip install -r requirements-dev.txt
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p data

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your MongoDB configuration"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your MongoDB configuration"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run the scraper: python main.py"
echo ""
echo "For GitHub Actions:"
echo "1. Set up repository secrets (MONGODB_URI, etc.)"
echo "2. Push to GitHub to trigger workflows"
echo ""
echo "Happy scraping! 📰"
