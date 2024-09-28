# settings_file.py

import os

# Force WebDriver Manager to use the /tmp directory for driver storage
os.environ["WDM_LOCAL"] = "1"
os.environ["WDM_CACHE_DIR"] = "/tmp"

# Headless mode (required for Streamlit or other cloud environments)
HEADLESS = True

# Timeouts
TIMEOUT = 10  # Default timeout in seconds for waiting on elements