"""
E2E test skeleton using Playwright.

Task #46: Critical user flow tests: register → summarize → view analytics.

Setup:
    pip install pytest-playwright
    playwright install chromium

Usage:
    pytest tests/e2e/ --headed  # watch the browser
    pytest tests/e2e/           # headless CI mode
"""

import re

import pytest

# Playwright fixtures are auto-injected by pytest-playwright
# (page, browser, context, etc.)


@pytest.fixture
def base_url():
    """Base URL for the running application."""
    return "http://localhost:5173"  # Vite dev server


@pytest.fixture
def api_url():
    """Base URL for the backend API."""
    return "http://localhost:8000/api/v1"


class TestCriticalFlows:
    """End-to-end tests for the core user journey."""

    @pytest.mark.skip(reason="Requires running frontend + backend. Run manually with --headed.")
    def test_homepage_loads(self, page, base_url):
        """Verify the homepage renders with the app name."""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")

        # App title should be visible
        assert page.title() == "PROBEXR — AI Summarizer"

        # Should see the summarizer input area
        assert page.locator("textarea").count() > 0

    @pytest.mark.skip(reason="Requires running frontend + backend. Run manually with --headed.")
    def test_register_flow(self, page, base_url):
        """Test user registration from the UI."""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")

        # Click sign up button (in sidebar or header)
        signup_btn = page.get_by_text(re.compile(r"sign\s*up", re.IGNORECASE))
        if signup_btn.count() > 0:
            signup_btn.first.click()

        # Fill registration form
        page.wait_for_selector("input[type='email']", timeout=5000)
        page.fill("input[type='email']", "e2e-test@example.com")

        password_inputs = page.locator("input[type='password']")
        if password_inputs.count() >= 1:
            password_inputs.first.fill("E2eTestPass123!@#")

        # Submit
        submit = page.get_by_role("button", name=re.compile(r"sign\s*up|register|create", re.IGNORECASE))
        if submit.count() > 0:
            submit.first.click()

        # Wait for result
        page.wait_for_timeout(2000)

    @pytest.mark.skip(reason="Requires running frontend + backend. Run manually with --headed.")
    def test_summarize_flow(self, page, base_url):
        """Test the core summarization flow."""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")

        # Find and fill the text input
        textarea = page.locator("textarea").first
        textarea.fill(
            "Artificial intelligence has transformed the technology landscape. "
            "Machine learning algorithms now power recommendation systems, "
            "natural language processing, and computer vision applications. "
            * 5
        )

        # Click summarize button
        summarize_btn = page.get_by_role("button", name=re.compile(r"summarize", re.IGNORECASE))
        if summarize_btn.count() > 0:
            summarize_btn.first.click()

        # Wait for summary output
        page.wait_for_timeout(5000)

        # Should see output content
        # (specific selectors depend on the UI implementation)

    @pytest.mark.skip(reason="Requires running frontend + backend. Run manually with --headed.")
    def test_analytics_tab(self, page, base_url):
        """Test navigating to the analytics tab."""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")

        # Click analytics tab
        analytics_btn = page.get_by_text(re.compile(r"analytics", re.IGNORECASE))
        if analytics_btn.count() > 0:
            analytics_btn.first.click()
            page.wait_for_timeout(2000)

            # Should see analytics heading
            heading = page.get_by_role("heading", name=re.compile(r"analytics", re.IGNORECASE))
            assert heading.count() > 0

    @pytest.mark.skip(reason="Requires running frontend + backend. Run manually with --headed.")
    def test_keyboard_shortcuts(self, page, base_url):
        """Test that keyboard shortcut overlay works."""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")

        # Press Cmd+/ to open shortcuts panel
        page.keyboard.press("Meta+/")
        page.wait_for_timeout(500)

        # Should see shortcuts overlay
        shortcuts_text = page.get_by_text(re.compile(r"shortcut|keyboard", re.IGNORECASE))
        assert shortcuts_text.count() > 0
