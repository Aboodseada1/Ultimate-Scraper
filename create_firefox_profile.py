import os
import time
import subprocess
import platform
import shutil
import tempfile

def setup_firefox_profile():
    # Profile directory name
    PROFILE_NAME = 'Firefox-Profile'
    
    # Get the current directory where the script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    profile_directory = os.path.join(current_dir, PROFILE_NAME)
    
    print(f"Setting up Firefox profile directory: {profile_directory}")
    
    # Ensure the profile directory exists
    if not os.path.exists(profile_directory):
        os.makedirs(profile_directory)
        print(f"Created profile directory at: {profile_directory}")
    else:
        print(f"Profile directory already exists at: {profile_directory}")
    
    # Determine Firefox binary path based on OS
    firefox_bin = get_firefox_binary()
    if not firefox_bin:
        print("Could not find Firefox installation. Please make sure Firefox is installed.")
        return
    
    # Launch Firefox with the custom profile
    try:
        # Command to launch Firefox with specific profile
        cmd = [
            firefox_bin,
            "--new-instance",
            f"--profile", profile_directory,
            "--no-remote",  # Don't connect to existing Firefox process
            "https://www.google.com"  # Initial URL to load
        ]
        
        
        # Launch Firefox with the profile
        process = subprocess.Popen(cmd)
        
        # Wait for user to manually close Firefox
        print("Firefox is running. Please close the browser when you're finished...")
        process.wait()
        
        print("\nFirefox closed. Profile has been saved.")
        print(f"Profile location: {profile_directory}")
        print("\nTo reuse this profile, launch Firefox with:")
        print(f"  {firefox_bin} --profile \"{profile_directory}\"")
        
    except Exception as e:
        print(f"Error during profile setup: {e}")

def get_firefox_binary():
    """Find the Firefox binary based on the operating system"""
    system = platform.system()
    
    if system == "Windows":
        # Common installation paths on Windows
        possible_paths = [
            os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'Mozilla Firefox', 'firefox.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'), 'Mozilla Firefox', 'firefox.exe')
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
    
    elif system == "Darwin":  # macOS
        # Common installation paths on macOS
        possible_paths = [
            "/Applications/Firefox.app/Contents/MacOS/firefox",
            f"/Users/{os.getlogin()}/Applications/Firefox.app/Contents/MacOS/firefox"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
    
    elif system == "Linux":
        # Try to find Firefox using 'which' command
        try:
            return subprocess.check_output(["which", "firefox"]).decode().strip()
        except subprocess.CalledProcessError:
            try:
                return subprocess.check_output(["which", "firefox-esr"]).decode().strip()
            except subprocess.CalledProcessError:
                pass
    
    # If we get here, we couldn't find Firefox
    return None

if __name__ == "__main__":
    setup_firefox_profile()