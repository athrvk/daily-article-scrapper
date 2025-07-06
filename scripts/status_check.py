#!/usr/bin/env python3
"""
Status check script for the Daily Article Scraper
Verifies that all components are working correctly
"""

import sys
import os
from pathlib import Path

def check_imports():
    """Check if all required modules can be imported."""
    try:
        print("🔍 Checking imports...")
        
        # Add the project paths
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root / 'src'))
        sys.path.insert(0, str(project_root / 'config'))
        
        # Test core imports
        import requests
        import feedparser
        import pymongo
        from bs4 import BeautifulSoup
        print("✅ Core dependencies imported successfully")
        
        # Test project imports
        from src.scraper import ArticleScraper
        from src.database import DatabaseManager
        from config.settings import Config
        print("✅ Project modules imported successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def check_configuration():
    """Check configuration setup."""
    try:
        print("🔍 Checking configuration...")
        
        # Check if .env file exists
        if Path('.env').exists():
            print("✅ .env file found")
        else:
            print("⚠️ .env file not found (using defaults)")
        
        # Test configuration loading
        sys.path.insert(0, 'config')
        from config.settings import Config
        config = Config()
        print(f"✅ Configuration loaded - Target articles: {config.TARGET_ARTICLE_COUNT}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def check_directories():
    """Check if required directories exist."""
    print("🔍 Checking directories...")
    
    required_dirs = ['src', 'config', 'logs', 'scripts', 'tests']
    all_exist = True
    
    for directory in required_dirs:
        if Path(directory).exists():
            print(f"✅ {directory}/ directory exists")
        else:
            print(f"❌ {directory}/ directory missing")
            all_exist = False
    
    return all_exist

def test_scraper():
    """Test basic scraper functionality."""
    try:
        print("🔍 Testing scraper...")
        
        sys.path.insert(0, 'src')
        sys.path.insert(0, 'config')
        
        from src.scraper import ArticleScraper
        scraper = ArticleScraper()
        
        # Test URL extraction
        test_articles = [
            {'url': 'https://example.com/1', 'title': 'Test 1'},
            {'url': 'https://example.com/2', 'title': 'Test 2'}
        ]
        urls = scraper.get_urls_only(test_articles)
        
        if len(urls) == 2:
            print("✅ Scraper basic functionality working")
            return True
        else:
            print("❌ Scraper test failed")
            return False
            
    except Exception as e:
        print(f"❌ Scraper test error: {e}")
        return False

def main():
    """Run all status checks."""
    print("🚀 Daily Article Scraper - Status Check")
    print("=" * 50)
    
    checks = [
        ("Directory Structure", check_directories),
        ("Python Imports", check_imports),
        ("Configuration", check_configuration),
        ("Scraper Functionality", test_scraper),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n📋 {name}")
        print("-" * 30)
        result = check_func()
        results.append((name, result))
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:<20} {status}")
        if not result:
            all_passed = False
    
    print("-" * 50)
    if all_passed:
        print("🎉 All checks passed! The project is ready to use.")
        print("\nNext steps:")
        print("1. Edit .env file with your MongoDB configuration")
        print("2. Run: python main.py")
        print("3. Set up GitHub Actions secrets for automation")
    else:
        print("⚠️ Some checks failed. Please review the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
