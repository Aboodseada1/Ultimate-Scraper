from playwright.sync_api import sync_playwright
import os
import time

# Profile directory for Chromium (Chrome/Edge)
CHROMIUM_PROFILE = 'Playwright-Profile'

def setup_playwright_profile():
    # Get absolute path to profile directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    profile_directory = os.path.join(current_dir, CHROMIUM_PROFILE)
    
    print(f"Setting up Playwright Chromium profile directory: {profile_directory}")
    
    # Ensure the profile directory exists
    if not os.path.exists(profile_directory):
        os.makedirs(profile_directory)
        print(f"Created profile directory at: {profile_directory}")
    else:
        print(f"Profile directory already exists at: {profile_directory}")
    
    # Initialize Playwright
    with sync_playwright() as playwright:
        try:
            # Use Chromium (default Playwright browser - Chrome/Edge)
            browser_context = playwright.chromium.launch_persistent_context(
                user_data_dir=profile_directory,
                headless=False,  # Run with UI visible for login
                slow_mo=100  # Slow down operations for stability
            )
            
            page = browser_context.new_page()
            
            # Navigate to login page 
            print("Navigating to Google page...")
            page.goto("https://www.google.com")
            
            
            # Keep browser open until interrupted
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nSaving profile and closing browser...")
            
            # Close properly
            browser_context.close()
            print("Playwright Chromium profile setup complete!")
            
        except Exception as e:
            print(f"Error during profile setup: {e}")

if __name__ == "__main__":
    setup_playwright_profile()