import os
import time
import shutil
import platform
import subprocess
try:
    import undetected_chromedriver as uc
except ImportError:
    print("Installing undetected-chromedriver package...")
    subprocess.check_call(["pip", "install", "undetected-chromedriver"])
    import undetected_chromedriver as uc

def setup_chrome_profile():
    # Profile directory name
    PROFILE_NAME = 'Chrome-Profile'
    
    # Get the current directory where the script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    profile_directory = os.path.join(current_dir, PROFILE_NAME)
    
    print(f"Setting up Chrome profile directory: {profile_directory}")
    
    # Ensure the profile directory exists
    if not os.path.exists(profile_directory):
        os.makedirs(profile_directory)
        print(f"Created profile directory at: {profile_directory}")
    else:
        print(f"Profile directory already exists at: {profile_directory}")

    # Configure options for undetected-chromedriver
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={profile_directory}")
    
    # Additional options to make the browser more stable and less detectable
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    
    # Add a custom user agent to appear more like a regular user
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    
    try:
        print("\n=====================================================")
        print("IMPORTANT: Launching Chrome with custom profile")
        print("Please wait while Chrome is being configured...")
        print("=====================================================\n")
        
        # Initialize undetected-chromedriver with our options
        # no_sandbox=True makes it work in more environments
        # headless=False ensures we can see the browser and interact with it
        driver = uc.Chrome(
            options=options,
            use_subprocess=True,  # More stable in some environments
            driver_executable_path=None,  # Let it find/download the appropriate driver
            version_main=None,  # Auto-detect Chrome version
            no_sandbox=True
        )
        
        # Navigate to Google 
        print("Navigating to Google page...")
        driver.get("https://www.google.com")
        
        # Keep browser open until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nSaving profile and closing browser...")
        
        # Close properly
        driver.quit()
        print("Chrome profile setup complete!")
        print(f"Profile saved at: {profile_directory}")
        print("\nTo use this profile in your own code:")
        print("options = uc.ChromeOptions()")
        print(f"options.add_argument('--user-data-dir={profile_directory}')")
        print("driver = uc.Chrome(options=options)")
        
    except Exception as e:
        print(f"Error during profile setup: {e}")
        
    finally:
        # Make sure any leftover Chrome processes are cleaned up
        kill_chrome_processes()

def kill_chrome_processes():
    """Kill any remaining Chrome processes to avoid conflicts on next run"""
    system = platform.system()
    
    try:
        if system == "Windows":
            os.system("taskkill /f /im chrome.exe /t")
        elif system in ["Darwin", "Linux"]:
            os.system("pkill -f chrome")
    except:
        pass

if __name__ == "__main__":
    setup_chrome_profile()