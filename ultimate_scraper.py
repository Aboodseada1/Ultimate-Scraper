#!/usr/bin/env python3
"""
ultimate_scraper.py - Standalone Web Scraper with Fallback Mechanisms

Scrapes a given URL using multiple methods, falling back until successful:
1. Fast methods (httpx/cloudscraper)
2. Playwright (headless Chromium with optional profile)
3. Selenium Firefox (headless with optional profile)
4. Selenium Chrome (headless with optional profile)

Outputs raw HTML or beautified text content to console or file (TXT/JSON).
Requires necessary libraries installed for chosen methods. See README.md.
"""

import os
import sys
import time
import json
import argparse
import logging
from pathlib import Path
import traceback # For detailed error logging
import re # For cleaning

# --- Library Imports ---
# Core dependencies
import httpx
import cloudscraper
try:
    from bs4 import BeautifulSoup # For cleaning HTML
except ImportError:
    print("Warning: 'beautifulsoup4' not installed. HTML cleaning ('beautify') requires it (pip install beautifulsoup4 lxml). Falling back to raw HTML.")
    BeautifulSoup = None
try:
    import lxml # Recommended parser for BeautifulSoup
except ImportError:
     print("Warning: 'lxml' not installed. BeautifulSoup will use Python's built-in parser (html.parser), which might be less robust.")
     # BeautifulSoup will automatically use 'html.parser' if lxml is not found

# Optional dependencies (imported later when needed/checked)
playwright = None
selenium = None
webdriver_manager = None

# --- Logging Setup ---
# Configure root logger first
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s [%(name)s] %(message)s', stream=sys.stdout)
# Get logger for this module
logger = logging.getLogger("ultimate_scraper")

# --- HTML Cleaning Function (Integrated) ---
def clean_html(html_content):
    """
    Basic cleaning of HTML content. Removes scripts, styles, nav, footers, etc.
    Extracts structured text content by default.

    Args:
        html_content (str): Raw HTML string.

    Returns:
        str: Cleaned/extracted text content. Returns original on error or if bs4 not found.
    """
    if not html_content:
        return ""
    if BeautifulSoup is None:
         logger.warning("BeautifulSoup not available for cleaning HTML. Returning raw content.")
         return html_content

    try:
        # Use lxml if available, otherwise html.parser
        parser = 'lxml' if 'lxml' in sys.modules else 'html.parser'
        soup = BeautifulSoup(html_content, parser)

        # Remove common noise tags
        tags_to_remove = ['script', 'style', 'nav', 'footer', 'aside', 'header', 'form', 'iframe', 'button', 'input', 'textarea', 'select', 'option', 'noscript', 'link', 'meta']
        for tag in soup.find_all(tags_to_remove):
            tag.decompose()

        # Attempt to find the main content area (heuristic, might need adjustment)
        main_content = soup.find('main') or soup.find('article') or soup.find('div', role='main') or soup.find('body')

        if main_content:
            # Get text, try to preserve paragraphs with newlines, strip extra whitespace
            text_content = main_content.get_text(separator='\n', strip=True)
            # Consolidate multiple blank lines into single blank lines
            cleaned_text = re.sub(r'\n\s*\n', '\n\n', text_content)
            return cleaned_text.strip() # Remove leading/trailing whitespace
        else:
             # Fallback if no body or main tag found (should be rare)
             text_content = soup.get_text(separator='\n', strip=True)
             cleaned_text = re.sub(r'\n\s*\n', '\n\n', text_content)
             return cleaned_text.strip()

    except Exception as e:
        logger.error(f"Error cleaning HTML: {e}. Returning raw content.")
        logger.debug(traceback.format_exc())
        # Fallback to returning original content if cleaning fails
        return html_content

# --- Scraping Methods ---

# 1. FAST METHODS
def fast_scrape(url, beautify=True):
    """Scrape URL using httpx or cloudscraper."""
    logger.debug(f"Attempting fast scrape: {url}")
    content = None
    method_used = None
    # Common headers mimicking a browser
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8', 'Accept-Language': 'en-US,en;q=0.9'}

    # Try httpx first
    try:
        with httpx.Client(timeout=15.0, follow_redirects=True, limits=httpx.Limits(max_connections=100)) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status() # Raise error for bad status codes (4xx, 5xx)
            content = response.text
            method_used = "httpx"
            logger.debug(f"httpx scrape successful for {url} (Status: {response.status_code}).")
    except Exception as e:
        logger.debug(f"httpx failed for {url}: {e}")
        # If httpx fails, try cloudscraper
        try:
            # Cloudscraper might need specific settings depending on the site
            scraper = cloudscraper.create_scraper(
                 browser={'custom': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'} # Mimic browser
            )
            response = scraper.get(url, timeout=20) # Slightly longer timeout for potential challenges
            response.raise_for_status()
            content = response.text
            method_used = "cloudscraper"
            logger.debug(f"cloudscraper scrape successful for {url} (Status: {response.status_code}).")
        except Exception as e_cs:
            logger.debug(f"cloudscraper failed for {url}: {e_cs}")

    if content:
        logger.info(f"Fast scrape successful ({method_used}) for: {url}")
        return clean_html(content) if beautify else content, method_used
    else:
        logger.info(f"Fast scrape failed for: {url}")
        return None, None

# 2. PLAYWRIGHT METHOD
def playwright_scrape(url, profile_path=None, beautify=True):
    """Scrape URL using Playwright with optional profile."""
    global playwright # Allow modification of the global variable
    if playwright is None: # Only try importing once
        try:
            from playwright.sync_api import sync_playwright
            playwright = sync_playwright # Assign to global if import succeeds
            logger.debug("Playwright imported successfully.")
        except ImportError:
            logger.warning("Playwright library not installed. Skipping Playwright method. (pip install playwright && playwright install chromium)")
            playwright = False # Mark as checked and failed
            return None, None
    elif playwright is False: # Already checked and failed
         return None, None

    logger.debug(f"Attempting Playwright scrape: {url}")
    context = None
    browser = None
    content = None
    method = None

    try:
        with playwright() as p:
            browser_type = p.chromium
            # Use new headless mode which is closer to non-headless
            launch_options = {"headless": True, "args": ["--headless=new", "--disable-gpu"]}
            # Standard context options
            context_options = {
                "user_agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                "viewport": {"width": 1920, "height": 1080},
                "ignore_https_errors": True # Handle potential SSL issues
            }

            if profile_path and Path(profile_path).exists():
                 logger.info(f"Attempting to use Playwright profile: {profile_path}")
                 # Note: Persistent context is generally needed for profiles,
                 # and headless might be problematic. We launch non-persistent here.
                 # User data dir for non-persistent launch doesn't usually load cookies effectively.
                 logger.warning("Profile path specified, but Playwright profile loading in standard headless mode has limitations. Cookies/sessions might not be loaded.")
                 # launch_options["user_data_dir"] = str(profile_path) # This is incorrect for launch()

            browser = browser_type.launch(**launch_options)
            context = browser.new_context(**context_options)
            page = context.new_page()

            try:
                logger.debug(f"Navigating to {url} with Playwright...")
                # Wait for network idle to catch more dynamic content loading
                page.goto(url, wait_until="networkidle", timeout=60000) # Increased timeout
                # Optional: Add specific waits for elements if needed
                # page.wait_for_selector('#some-important-element', timeout=10000)
                page.wait_for_timeout(3000) # Short generic wait after network idle
                content_html = page.content()
                content = clean_html(content_html) if beautify else content_html
                method = "playwright"
                logger.info(f"Playwright scrape successful for: {url}")

            finally:
                 if context: context.close()
                 if browser: browser.close()

            return content, method

    except Exception as e:
        logger.warning(f"Playwright scrape failed for {url}: {e}")
        logger.debug(traceback.format_exc()) # Log full traceback for debugging
        # Ensure cleanup even on error
        if context:
            try: context.close()
            except: pass
        if browser:
            try: browser.close()
            except: pass
        return None, None

# --- Helper to check and import Selenium/Webdriver Manager ---
def _ensure_selenium_dependencies():
    global selenium, webdriver_manager
    if selenium is not None: # Already checked (successfully or unsuccessfully)
        return selenium is not False # Return True if available, False if check failed

    selenium = False # Assume failure initially
    webdriver_manager = False
    try:
        import selenium
        from selenium import webdriver
        from selenium.webdriver.firefox.service import Service as FirefoxService
        from selenium.webdriver.firefox.options import Options as FirefoxOptions
        from selenium.webdriver.chrome.service import Service as ChromeService
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        selenium = { # Store imported components
             "webdriver": webdriver,
             "FirefoxService": FirefoxService, "FirefoxOptions": FirefoxOptions,
             "ChromeService": ChromeService, "ChromeOptions": ChromeOptions
        }
        logger.debug("Selenium library imported successfully.")
        try:
            from webdriver_manager.firefox import GeckoDriverManager
            from webdriver_manager.chrome import ChromeDriverManager
            webdriver_manager = { # Store manager classes
                 "firefox": GeckoDriverManager,
                 "chrome": ChromeDriverManager
            }
            logger.debug("webdriver-manager imported successfully.")
        except ImportError:
            logger.warning("webdriver-manager not installed. Selenium will rely on drivers being in PATH. (pip install webdriver-manager)")
            webdriver_manager = {} # Indicate manager is unavailable but selenium is

        return True # Selenium (and maybe manager) are available

    except ImportError:
        logger.warning("Selenium library not installed. Skipping Selenium methods. (pip install selenium)")
        return False # Mark selenium as unavailable

# 3. SELENIUM FIREFOX METHOD
def firefox_scrape(url, profile_path=None, beautify=True):
    """Scrape URL using Selenium Firefox with optional profile."""
    if not _ensure_selenium_dependencies():
        return None, None # Dependencies not met

    logger.debug(f"Attempting Firefox scrape: {url}")
    driver = None
    try:
        options = selenium["FirefoxOptions"]()
        options.add_argument("--headless") # Standard headless
        options.add_argument("--window-size=1920,1080")

        if profile_path and Path(profile_path).exists():
            logger.info(f"Using Firefox profile: {profile_path}")
            options.add_argument("-profile")
            options.add_argument(str(profile_path))
        else:
             logger.debug("No valid Firefox profile path provided or found.")

        service_args = {}
        if "firefox" in webdriver_manager:
             try:
                 # Ensure the path is a string
                 service_args['executable_path'] = str(webdriver_manager["firefox"]().install())
                 logger.debug("Using GeckoDriverManager to manage geckodriver.")
             except Exception as wd_e:
                 logger.warning(f"GeckoDriverManager failed ({wd_e}), assuming geckodriver is in PATH.")
        else:
             logger.debug("Assuming geckodriver is in PATH (webdriver-manager not available).")

        service = selenium["FirefoxService"](**service_args)
        driver = selenium["webdriver"].Firefox(service=service, options=options)
        driver.set_page_load_timeout(60) # Increased timeout

        try:
            logger.debug(f"Navigating to {url} with Firefox...")
            driver.get(url)
            time.sleep(5) # Wait for JS rendering (adjust as needed)
            content_html = driver.page_source
            content = clean_html(content_html) if beautify else content_html
            method = "firefox"
            logger.info(f"Firefox scrape successful for: {url}")
            return content, method
        finally:
            if driver: driver.quit()

    except Exception as e:
        logger.warning(f"Firefox scrape failed for {url}: {e}")
        logger.debug(traceback.format_exc())
        if driver:
            try: driver.quit()
            except: pass
        return None, None

# 4. SELENIUM CHROME METHOD
def chrome_scrape(url, profile_path=None, beautify=True):
    """Scrape URL using Selenium Chrome with optional profile."""
    if not _ensure_selenium_dependencies():
        return None, None # Dependencies not met

    logger.debug(f"Attempting Chrome scrape: {url}")
    driver = None
    try:
        options = selenium["ChromeOptions"]()
        options.add_argument("--headless=new") # Use new headless mode
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--log-level=3") # Suppress console logs from Chrome/Driver
        options.add_experimental_option('excludeSwitches', ['enable-logging']) # Further suppress logs

        if profile_path and Path(profile_path).exists():
            logger.info(f"Attempting to use Chrome profile: {profile_path}")
            # Headless + user-data-dir can be tricky. It *might* work with --headless=new
            # but often requires the profile structure to be just right.
            options.add_argument(f"--user-data-dir={profile_path}")
            # Sometimes specifying the default profile within the user-data-dir helps
            # options.add_argument("--profile-directory=Default")
            logger.warning("Chrome profile specified; ensure profile structure is correct and headless mode is compatible.")
        else:
             logger.debug("No valid Chrome profile path provided or found.")

        service_args = {}
        if "chrome" in webdriver_manager:
             try:
                 service_args['executable_path'] = str(webdriver_manager["chrome"]().install())
                 logger.debug("Using ChromeDriverManager to manage chromedriver.")
             except Exception as wd_e:
                 logger.warning(f"ChromeDriverManager failed ({wd_e}), assuming chromedriver is in PATH.")
        else:
             logger.debug("Assuming chromedriver is in PATH (webdriver-manager not available).")

        service = selenium["ChromeService"](**service_args)
        driver = selenium["webdriver"].Chrome(service=service, options=options)
        driver.set_page_load_timeout(60) # Increased timeout

        try:
            logger.debug(f"Navigating to {url} with Chrome...")
            driver.get(url)
            time.sleep(5) # Wait for JS rendering (adjust as needed)
            content_html = driver.page_source
            content = clean_html(content_html) if beautify else content_html
            method = "chrome"
            logger.info(f"Chrome scrape successful for: {url}")
            return content, method
        finally:
            if driver: driver.quit()

    except Exception as e:
        logger.warning(f"Chrome scrape failed for {url}: {e}")
        logger.debug(traceback.format_exc())
        if driver:
            try: driver.quit()
            except: pass
        return None, None


# --- Main Orchestration Function ---
def scrape_url_orchestrator(url, beautify=True, playwright_profile=None, firefox_profile=None, chrome_profile=None):
    """
    Scrape a single URL using all available methods as fallbacks.

    Args:
        url (str): The URL to scrape.
        beautify (bool): Clean HTML for AI if True.
        playwright_profile (str, optional): Path to Playwright profile.
        firefox_profile (str, optional): Path to Firefox profile.
        chrome_profile (str, optional): Path to Chrome profile.

    Returns:
        dict: Result containing 'url', 'content', 'method', 'beautified'.
              'content' and 'method' will be None if all attempts fail.
    """
    # Validate URL basic structure early
    if not url or not (url.startswith('http://') or url.startswith('https://')):
        logger.error(f"Invalid URL provided: {url}. Must start with http:// or https://")
        return {"url": url, "content": None, "method": None, "beautified": beautify, "error": "Invalid URL schema"}

    logger.info(f"Orchestrating scrape for: {url} (Beautify: {beautify})")
    result = {"url": url, "content": None, "method": None, "beautified": beautify}

    # --- Define scraping attempts in order ---
    scrape_attempts = [
        ("fast", lambda: fast_scrape(url, beautify)),
        ("playwright", lambda: playwright_scrape(url, playwright_profile, beautify)),
        ("firefox", lambda: firefox_scrape(url, firefox_profile, beautify)),
        ("chrome", lambda: chrome_scrape(url, chrome_profile, beautify))
    ]

    for method_name, scrape_func in scrape_attempts:
        logger.info(f"Trying method: {method_name}")
        try:
            content, method_used = scrape_func()
            if content is not None: # Check for non-empty content as well? "" is valid empty page. None means failure.
                result.update({"content": content, "method": method_used})
                logger.info(f"Success with method: {method_used}")
                return result
            else:
                logger.info(f"Method {method_name} failed or returned no content.")
        except Exception as e:
            logger.error(f"Exception during method {method_name} for {url}: {e}")
            logger.debug(traceback.format_exc()) # Log full traceback for this specific error

    # If loop finishes, all methods failed
    logger.error(f"All scraping methods failed for URL: {url}")
    result["error"] = "All scraping methods failed"
    return result

# --- Main Execution Block ---
def main():
    parser = argparse.ArgumentParser(
        description="Ultimate Web Scraper: Scrapes a URL using multiple fallback methods.",
        epilog="Example: python ultimate_scraper.py https://example.com -o output.txt -f txt --log-level DEBUG"
    )
    parser.add_argument("url", help="The URL to scrape (must start with http:// or https://).")
    parser.add_argument("-o", "--output-file", help="Path to save the output file.", default=None)
    parser.add_argument("-f", "--output-format", choices=['txt', 'json'], default='txt', help="Output format (txt or json). 'txt' outputs only the content, 'json' outputs the full result dictionary. Default: txt")
    parser.add_argument("-r", "--raw", action="store_true", help="Output raw HTML content (do not beautify/clean).")
    parser.add_argument("--pp", "--playwright-profile", dest="playwright_profile", help="Path to the Playwright profile directory.")
    parser.add_argument("--fp", "--firefox-profile", dest="firefox_profile", help="Path to the Firefox profile directory.")
    parser.add_argument("--cp", "--chrome-profile", dest="chrome_profile", help="Path to the Chrome profile directory.")
    parser.add_argument("-l", "--log-level", default="INFO", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help="Set logging level.")

    args = parser.parse_args()

    # --- Configure Logging Level ---
    log_level_map = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARNING': logging.WARNING, 'ERROR': logging.ERROR, 'CRITICAL': logging.CRITICAL}
    log_level = log_level_map.get(args.log_level.upper(), logging.INFO)
    # Set level specifically for our logger
    logger.setLevel(log_level)
    # Set level for root logger to affect library logs (optional, can be noisy)
    # logging.getLogger().setLevel(log_level)
    # Quieten overly verbose library loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(logging.WARNING)
    logging.getLogger("selenium.webdriver.common.service").setLevel(logging.WARNING)
    logging.getLogger("webdriver_manager").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.INFO) # Sometimes noisy on DEBUG


    logger.info("="*30)
    logger.info(" Starting Ultimate Scraper ".center(30,"="))
    logger.info("="*30)
    start_time = time.time()

    # Determine if cleaning should happen
    beautify = not args.raw
    if args.raw:
        logger.info("Raw HTML output requested (no cleaning/beautification).")
    elif BeautifulSoup is None:
         logger.warning("HTML cleaning disabled because 'beautifulsoup4' is not installed.")
         beautify = False # Force raw if library missing

    # Perform scraping
    result = scrape_url_orchestrator(
        url=args.url,
        beautify=beautify,
        playwright_profile=args.playwright_profile,
        firefox_profile=args.firefox_profile,
        chrome_profile=args.chrome_profile
    )

    end_time = time.time()
    logger.info(f"Scraping finished in {end_time - start_time:.2f} seconds.")
    logger.info(f"Method successful: {result['method'] or 'None'}")

    # --- Handle Output ---
    output_content = ""
    if args.output_format == 'json':
        # Always output the full result dictionary as JSON
        # Ensure content is serializable (it should be string or None)
        if result.get("content") is not None and not isinstance(result["content"], str):
             logger.warning("Content is not a string, converting for JSON output.")
             result["content"] = str(result["content"])
        output_content = json.dumps(result, indent=2, ensure_ascii=False) # Use ensure_ascii=False for broader char support
    else: # txt format
        if result["content"]:
            output_content = result["content"]
        else:
            # Provide an error message in txt output if failed
            output_content = f"Error: Failed to scrape URL: {args.url}\nMethod attempted last: {result['method'] or 'N/A'}\nError details: {result.get('error', 'Unknown error')}"

    if args.output_file:
        try:
            # Ensure directory exists
            output_path = Path(args.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_content)
            logger.info(f"Output successfully saved to: {args.output_file}")
        except Exception as e:
            logger.error(f"Failed to write output to file '{args.output_file}': {e}")
            # Print to console as fallback if file write fails
            print("\n--- Output (Error writing to file, fallback to Console) ---")
            print(output_content)
            print("--- End Output ---")
    else:
        # Print to console
        # Use sys.stdout.buffer.write for potential encoding issues if needed, but print usually works
        # For large output, printing directly might be slow or truncate in some terminals.
        # Consider only printing a summary or head/tail if output is very large and not saved to file.
        print("\n--- Output ---")
        # Limit console output length to avoid flooding?
        max_console_len = 10000
        if len(output_content) > max_console_len:
            print(output_content[:max_console_len])
            print(f"\n... [Output truncated for console display, full content length: {len(output_content)} characters]")
        else:
             print(output_content)
        print("--- End Output ---")

    # Final status based on content
    if result["content"] is None:
         logger.critical(f"Failed to retrieve content for {args.url}")
         sys.exit(1) # Exit with error code if failed
    else:
         logger.info("Scraping process completed.")
         sys.exit(0) # Exit successfully


if __name__ == "__main__":
    # Add initial hints for optional dependencies
    try:
        import playwright
    except ImportError:
        logger.info("Hint: Playwright method requires installation: pip install playwright && playwright install chromium")
    try:
        import selenium
    except ImportError:
        logger.info("Hint: Selenium methods (Firefox/Chrome) require installation: pip install selenium")
    try:
         import webdriver_manager
    except ImportError:
         logger.info("Hint: Auto driver management requires installation: pip install webdriver-manager (otherwise drivers must be in PATH)")

    main()