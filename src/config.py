import os
from dotenv import load_dotenv


# Load env vars once
load_dotenv()

# Target address
TARGET_ADDRESS = os.getenv("TARGET_ADDRESS")


# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_TO = os.getenv("EMAIL_TO")


# Faucet configuration
FAUCET_URL= "https://cloud.google.com/application/web3/faucet/ethereum/sepolia"
SELECTED_NETWORK = "Ethereum Sepolia (0.05 ETH)"
HEADLESS=False
SESSION_FILE = "state.json"  
SCREENSHOT_DIR = "screenshots"
USER_DATA_DIR = "chrome-data" 
LOG_FILE = "faucet.log"
