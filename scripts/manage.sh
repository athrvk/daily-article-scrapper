#!/bin/bash

# Project management utility script
# Provides common commands for the Daily Article Scraper project

set -e

PROJECT_NAME="Daily Article Scraper"
PROJECT_DIR="/home/ubuntu/daily-article-scrapper"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Show help
show_help() {
    print_header "=== $PROJECT_NAME - Project Manager ==="
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup         Set up the development environment"
    echo "  status        Check project status"
    echo "  run           Run the article scraper"
    echo "  test          Run tests"
    echo "  lint          Run code linting"
    echo "  format        Format code"
    echo "  clean         Clean temporary files"
    echo "  install       Install dependencies"
    echo "  update        Update dependencies"
    echo "  backup        Create backup of articles"
    echo "  logs          Show recent logs"
    echo "  cleanup       Clean up old articles (2+ months)"
    echo "  stats         Show database statistics"
    echo "  help          Show this help message"
    echo ""
}

# Setup development environment
setup_project() {
    print_header "🚀 Setting up $PROJECT_NAME"
    
    if [ ! -f "$PROJECT_DIR/scripts/setup.sh" ]; then
        print_error "Setup script not found!"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    bash scripts/setup.sh --dev
    print_status "Setup completed!"
}

# Check project status
check_status() {
    print_header "📊 Checking $PROJECT_NAME Status"
    
    cd "$PROJECT_DIR"
    
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        python scripts/status_check.py
    else
        print_error "Virtual environment not found. Run 'setup' first."
        exit 1
    fi
}

# Run the scraper
run_scraper() {
    print_header "🔄 Running Article Scraper"
    
    cd "$PROJECT_DIR"
    
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        python main.py
    else
        print_error "Virtual environment not found. Run 'setup' first."
        exit 1
    fi
}

# Run tests
run_tests() {
    print_header "🧪 Running Tests"
    
    cd "$PROJECT_DIR"
    
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        pytest tests/ -v
    else
        print_error "Virtual environment not found. Run 'setup' first."
        exit 1
    fi
}

# Run linting
run_lint() {
    print_header "🔍 Running Code Linting"
    
    cd "$PROJECT_DIR"
    
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        flake8 src/ config/ main.py tests/
    else
        print_error "Virtual environment not found. Run 'setup' first."
        exit 1
    fi
}

# Format code
format_code() {
    print_header "✨ Formatting Code"
    
    cd "$PROJECT_DIR"
    
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        black src/ config/ main.py tests/
        isort src/ config/ main.py tests/
        print_status "Code formatted!"
    else
        print_error "Virtual environment not found. Run 'setup' first."
        exit 1
    fi
}

# Clean temporary files
clean_project() {
    print_header "🧹 Cleaning Project"
    
    cd "$PROJECT_DIR"
    
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    rm -rf .pytest_cache/ htmlcov/ .coverage dist/ *.egg-info/
    
    print_status "Project cleaned!"
}

# Install dependencies
install_deps() {
    print_header "📦 Installing Dependencies"
    
    cd "$PROJECT_DIR"
    
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        pip install -r requirements.txt
        print_status "Dependencies installed!"
    else
        print_error "Virtual environment not found. Run 'setup' first."
        exit 1
    fi
}

# Update dependencies
update_deps() {
    print_header "⬆️ Updating Dependencies"
    
    cd "$PROJECT_DIR"
    
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        pip install --upgrade -r requirements.txt
        print_status "Dependencies updated!"
    else
        print_error "Virtual environment not found. Run 'setup' first."
        exit 1
    fi
}

# Create backup
create_backup() {
    print_header "💾 Creating Backup"
    
    cd "$PROJECT_DIR"
    
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup article JSON files
    cp articles_*.json "$BACKUP_DIR/" 2>/dev/null || true
    
    # Backup logs
    cp -r logs/ "$BACKUP_DIR/" 2>/dev/null || true
    
    print_status "Backup created in $BACKUP_DIR"
}

# Show logs
show_logs() {
    print_header "📋 Recent Logs"
    
    cd "$PROJECT_DIR"
    
    if [ -f "logs/scraper.log" ]; then
        tail -20 logs/scraper.log
    else
        print_warning "No log file found."
    fi
}

# Clean up old articles
cleanup_articles() {
    print_header "🧹 Cleaning Up Old Articles"
    
    cd "$PROJECT_DIR"
    
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        python scripts/cleanup_articles.py
    else
        print_error "Virtual environment not found. Run 'setup' first."
        exit 1
    fi
}

# Show database statistics
show_stats() {
    print_header "📊 Database Statistics"
    
    cd "$PROJECT_DIR"
    
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        python scripts/cleanup_articles.py --stats
    else
        print_error "Virtual environment not found. Run 'setup' first."
        exit 1
    fi
}

# Main command dispatcher
case "$1" in
    setup)
        setup_project
        ;;
    status)
        check_status
        ;;
    run)
        run_scraper
        ;;
    test)
        run_tests
        ;;
    lint)
        run_lint
        ;;
    format)
        format_code
        ;;
    clean)
        clean_project
        ;;
    install)
        install_deps
        ;;
    update)
        update_deps
        ;;
    backup)
        create_backup
        ;;
    logs)
        show_logs
        ;;
    cleanup)
        cleanup_articles
        ;;
    stats)
        show_stats
        ;;
    help|--help|-h)
        show_help
        ;;
    "")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
