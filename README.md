# Ultimate Web Scraper

A standalone Python script designed to scrape web pages using a multi-layered approach with fallbacks. It attempts faster methods first and progressively uses browser automation if needed, increasing the likelihood of successfully retrieving content from various websites, including those with JavaScript rendering or basic anti-bot measures.

## Features

* **Multiple Scraping Methods:** Uses `httpx`, `cloudscraper`, `playwright` (Chromium), `selenium` (Firefox), and `selenium` (Chrome) in a specific fallback order.
* **Resilient Scraping:** Automatically tries the next method if a previous one fails.
* **JavaScript Rendering:** Handles dynamic content loaded by JavaScript via browser automation (Playwright/Selenium).
* **Anti-Bot Evasion:** Incorporates `cloudscraper` and options in browser automation to bypass some basic protections.
* **Optional Browser Profiles:** Supports using pre-configured profiles for Playwright, Firefox, and Chrome (useful for logged-in sessions or specific configurations). *See Profile Setup section.*
* **Flexible Output:** Saves scraped content to console or a file.
* **Output Formats:** Outputs either raw HTML or cleaned/beautified text content (suitable for LLM processing) in `txt` or `json` format.
* **JSON Output Details:** Includes the scraped content, the successful method used, the original URL, and beautification status.
* **Configurable Logging:** Adjustable log levels for detailed debugging.
* **Standalone CLI Tool:** Designed for easy command-line execution.

## Scraping Method Order

1. `httpx` / `cloudscraper` (Fastest, direct HTTP requests)
2. `playwright` (Headless Chromium automation)
3. `selenium` with Firefox (Headless automation)
4. `selenium` with Chrome (Headless automation)

## Prerequisites

* **Python:** Python 3.8+ recommended.
* **Pip:** Python package installer.
* **Core Libraries:** `requests`, `httpx`, `cloudscraper`, `beautifulsoup4`, `lxml` (Install via `requirements.txt`).
* **Optional Browser Automation Libraries:** (Install based on methods you want enabled)
* * **For Playwright:** `playwright` library (`pip install playwright`) AND browser binaries (`playwright install chromium`)
  * **For Selenium (Firefox/Chrome):** `selenium` library (`pip install selenium`)
  * **For Automatic Driver Management (Recommended for Selenium):** `webdriver-manager` (`pip install webdriver-manager`). If not installed, `geckodriver` (for Firefox) and `chromedriver` (for Chrome) must be manually installed and available in your system's PATH.
* **Optional Browser Profiles:** Pre-configured browser profile folders if you intend to use the profile arguments (see Profile Setup).

## Installation

1. **Clone the repository or download the scripts:** Contains `ultimate_scraper.py` and optional profile creation scripts.
2. ```bash
   git clone <repository_url> # Replace with your actual repo URL
   cd <repository_directory>
   ```
3. Or simply download the `ultimate_scraper.py` and `requirements.txt` files.
4. **(Recommended)** Create and activate a Python virtual environment:
5. ```bash
   python -m venv venv
   source venv/bin/activate # On Windows use `venv\Scripts\activate`
   ```
6. **Install dependencies from `requirements.txt`:** This file includes core and optional libraries.
7. ```bash
   pip install -r requirements.txt
   ```
8. **(Optional but required for Playwright method)** Install Playwright browser binaries:
9. ```bash
   playwright install chromium # Or playwright install to install all
   ```

## Profile Setup (Optional)

This scraper supports using existing browser profiles, which is useful for sites requiring logins or having specific cookie/storage states. You can create these profiles manually or use the provided helper scripts (`create_chrome_profile.py`, `create_firefox_profile.py`, `create_playwright_profile.py`).

* Run the desired `create_*.py` script (e.g., `python create_chrome_profile.py`).
* A browser window will open.
* **Log in to any websites** you need sessions for (e.g., Apollo, LinkedIn, etc.).
* Browse a bit to ensure cookies/local storage are saved.
* Close the browser window (or press Ctrl+C in the terminal for the Chrome/Playwright scripts).
* The script will create a profile folder (e.g., `Chrome-Profile`) in the same directory.
* Use the path to this folder with the corresponding command-line argument (`--cp`, `--fp`, `--pp`) when running `ultimate_scraper.py`.

## Usage

Run the script from your terminal:

```bash
python ultimate_scraper.py <url> [options]
```

**Arguments:**

* `url`: (Required) The full URL to scrape (must start with `http://` or `https://`).
* `-o`, `--output-file`: (Optional) Path to save the output file. If omitted, output goes to the console.
* `-f`, `--output-format`: (Optional) Output format: `txt` (content only) or `json` (full result dictionary). Default: `txt`.
* `-r`, `--raw`: (Optional) Output raw HTML content instead of cleaned/beautified text.
* `--pp`, `--playwright-profile`: (Optional) Path to the Playwright profile directory.
* `--fp`, `--firefox-profile`: (Optional) Path to the Firefox profile directory.
* `--cp`, `--chrome-profile`: (Optional) Path to the Chrome profile directory.
* `-l`, `--log-level`: (Optional) Set logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. Default: `INFO`.

## Examples

*(Replace `https://example.com` and profile paths)*

```bash
# Scrape and print cleaned text content to console
python ultimate_scraper.py https://example.com

# Scrape raw HTML and save to file
python ultimate_scraper.py https://quotes.toscrape.com/js/ -r -o raw_output.html

# Scrape and save full JSON result (including method used) to file
python ultimate_scraper.py https://httpbin.org/get -f json -o result.json

# Scrape using a specific Chrome profile and save cleaned text
python ultimate_scraper.py https://github.com/login --cp ./Chrome-Profile -o github_content.txt

# Scrape with debug logging
python ultimate_scraper.py https://news.ycombinator.com -l DEBUG
```

## Output Formats

**TXT Format (`-f txt`, default):** Outputs only the scraped content (either raw HTML if `-r` is used, or cleaned text otherwise). If scraping fails, it outputs an error message.

**JSON Format (`-f json`):** Outputs a JSON object containing:

* `url`: The original URL requested.
* `content`: The scraped content (string, raw or cleaned) or `null` if failed.
* `method`: The name of the successful scraping method (string, e.g., `"httpx"`, `"playwright"`) or `null`.
* `beautified`: Boolean indicating if the content was cleaned (`true`) or raw (`false`).
* `error`: An error message (string) if all methods failed.

### Example JSON Output (Success):

```json
{
  "url": "https://example.com",
  "content": "Example Domain\n\nThis domain is for use in illustrative examples in documents...",
  "method": "httpx",
  "beautified": true
}
```

### Example JSON Output (Failure):

```json
{
  "url": "https://nonexistent.example.com",
  "content": null,
  "method": null,
  "beautified": true,
  "error": "All scraping methods failed"
}
```

## Dependencies

See `requirements.txt` file. Core dependencies are `requests`, `httpx`, `cloudscraper`, `beautifulsoup4`, `lxml`. Optional dependencies for browser automation are `playwright`, `selenium`, `webdriver-manager`.

## Contributing

Contributions are welcome! Please feel free to open an issue for bugs or suggestions, or submit a pull request on [GitHub](https://github.com/Aboodseada1?tab=repositories).

## Support Me

If you find this tool useful, consider supporting its development via [PayPal](http://paypal.me/aboodseada1999). Thank you!

## License

This project is licensed under the MIT License.

```
MIT License

Copyright (c) 2025 Abood

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```