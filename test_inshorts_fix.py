#!/usr/bin/env python3
"""
Test script to verify InShorts API fix.
This script demonstrates that the updated InShorts integration can handle
multiple API response formats and field name variations.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "config"))

from unittest.mock import Mock, patch
from src.scraper import ArticleScraper
from config.settings import Config


def test_old_api_format():
    """Test that the scraper still works with the old API format."""
    print("Testing old API format compatibility...")

    scraper = ArticleScraper()

    # Mock response with old format
    mock_response = Mock()
    mock_response.json.return_value = {
        "data": {
            "news_list": [
                {
                    "hash_id": "old-format-1",
                    "title": "Old Format Article",
                    "content": "This uses the old API format",
                    "source_name": "Old Source",
                    "source_url": "https://example.com/old",
                    "image_url": "https://example.com/old.jpg",
                    "created_at": "2025-01-01T00:00:00Z",
                    "tags": ["test"],
                }
            ]
        }
    }
    mock_response.raise_for_status.return_value = None

    with patch.object(scraper.session, "get", return_value=mock_response):
        articles = scraper._fetch_inshorts_category("all", 5)

    assert len(articles) == 1
    assert articles[0]["title"] == "Old Format Article"
    assert articles[0]["url"] == "https://example.com/old"
    print("✓ Old format works!")


def test_new_public_api_format():
    """Test that the scraper works with the new public API format."""
    print("Testing new public API format...")

    scraper = ArticleScraper()

    # Mock response with new public API format
    mock_response = Mock()
    mock_response.json.return_value = {
        "data": [
            {
                "id": "new-format-1",
                "title": "New Format Article",
                "content": "This uses the new public API format",
                "author": "Public API",
                "readMoreUrl": "https://example.com/new",
                "imageUrl": "https://example.com/new.jpg",
                "date": 1704067200,
                "tags": "news,tech",
            }
        ]
    }
    mock_response.raise_for_status.return_value = None

    with patch.object(scraper.session, "get", return_value=mock_response):
        articles = scraper._fetch_inshorts_category("all", 5)

    assert len(articles) == 1
    assert articles[0]["title"] == "New Format Article"
    assert articles[0]["url"] == "https://example.com/new"
    print("✓ New public API format works!")


def test_alternative_format():
    """Test alternative API response format."""
    print("Testing alternative API format...")

    scraper = ArticleScraper()

    # Mock response with articles array format
    mock_response = Mock()
    mock_response.json.return_value = {
        "articles": [
            {
                "id": "alt-format-1",
                "headline": "Alternative Format Article",
                "description": "Another format variation",
                "sourceName": "Alt Source",
                "url": "https://example.com/alt",
                "thumbnail": "https://example.com/alt.jpg",
                "published": "2025-01-01T00:00:00Z",
                "tags": ["alternative"],
            }
        ]
    }
    mock_response.raise_for_status.return_value = None

    with patch.object(scraper.session, "get", return_value=mock_response):
        articles = scraper._fetch_inshorts_category("all", 5)

    assert len(articles) == 1
    assert articles[0]["title"] == "Alternative Format Article"
    assert articles[0]["url"] == "https://example.com/alt"
    print("✓ Alternative format works!")


def test_direct_list_format():
    """Test direct list API response format."""
    print("Testing direct list format...")

    scraper = ArticleScraper()

    # Mock response with direct list format
    mock_response = Mock()
    mock_response.json.return_value = [
        {
            "hash_id": "list-format-1",
            "title": "List Format Article",
            "content": "Direct list response",
            "source_name": "List Source",
            "source_url": "https://example.com/list",
            "image_url": "https://example.com/list.jpg",
            "created_at": "2025-01-01T00:00:00Z",
            "tags": ["list"],
        }
    ]
    mock_response.raise_for_status.return_value = None

    with patch.object(scraper.session, "get", return_value=mock_response):
        articles = scraper._fetch_inshorts_category("all", 5)

    assert len(articles) == 1
    assert articles[0]["title"] == "List Format Article"
    assert articles[0]["url"] == "https://example.com/list"
    print("✓ Direct list format works!")


def test_field_name_variations():
    """Test that various field name variations are handled."""
    print("Testing field name variations...")

    scraper = ArticleScraper()

    test_cases = [
        {
            "input": {
                "title": "Test",
                "source_url": "https://example.com/1",
                "content": "Content",
                "image_url": "https://example.com/1.jpg",
            },
            "expected_url": "https://example.com/1",
        },
        {
            "input": {
                "headline": "Test",
                "readMoreUrl": "https://example.com/2",
                "description": "Content",
                "imageUrl": "https://example.com/2.jpg",
            },
            "expected_url": "https://example.com/2",
        },
        {
            "input": {
                "name": "Test",
                "url": "https://example.com/3",
                "summary": "Content",
                "thumbnail": "https://example.com/3.jpg",
            },
            "expected_url": "https://example.com/3",
        },
    ]

    for i, test_case in enumerate(test_cases):
        article = scraper._parse_inshorts_article(test_case["input"], "test")
        assert article is not None, f"Test case {i} failed to parse"
        assert (
            article["url"] == test_case["expected_url"]
        ), f"Test case {i} URL mismatch"

    print(f"✓ All {len(test_cases)} field name variations work!")


def main():
    """Run all tests."""
    print("=" * 60)
    print("InShorts API Fix Verification Tests")
    print("=" * 60)
    print()

    tests = [
        test_old_api_format,
        test_new_public_api_format,
        test_alternative_format,
        test_direct_list_format,
        test_field_name_variations,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ Test failed: {e}")
            failed += 1

    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("✅ All tests passed! The InShorts API fix is working correctly.")
        print()
        print("Summary of improvements:")
        print("  • Updated API endpoint to use public API wrapper")
        print("  • Modern user agent (Chrome 120)")
        print("  • Support for multiple API response structures")
        print("  • Support for various field name variations")
        print("  • Robust error handling")
        return True
    else:
        print("❌ Some tests failed. Please review the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
