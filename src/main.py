import os
import re
import time
import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from config import FAUCET_URL, SELECTED_NETWORK, HEADLESS, SESSION_FILE, SCREENSHOT_DIR, USER_DATA_DIR, LOG_FILE, TARGET_ADDRESS
from utils import send_email, wait_for_status


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)


# Convert str to bool
def str_to_bool(str, default=True):
    if str is None:
        return default
    return str.strip().lower() in ("1", "true", "yes", "y", "on")


# Click on elements
def try_to_click(locator, timeout_ms=2000):
    try:
        locator.click(timeout=timeout_ms)
        return True
    except Exception as e:
        logging.error(f"Click failed: {e}")
        return False


# main
def main():

    os.makedirs(SCREENSHOT_DIR, exist_ok=True) 

    # Start playwright
    with sync_playwright() as p:

        # Open Google Chrome with a persistent user profile             
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=HEADLESS,
            channel="chrome",             
            args=["--disable-blink-features=AutomationControlled"]  
        )

        page = context.pages[0] if context.pages else context.new_page()

        # Go directly to the Faucet page
        page.goto(FAUCET_URL, wait_until="domcontentloaded")

        # Make sure we actually landed on the faucet (not stuck on gds.google.com redirect)
        try:
            page.wait_for_url("**/application/web3/faucet/**", timeout=60000)
            logging.info("Arrived at Faucet page")
        except Exception as e:
            logging.error(f"Did not reach faucet page in time: {e}")
            filename = os.path.join(SCREENSHOT_DIR, f"faucet_nav_error_{int(time.time())}.png")
            page.screenshot(path=filename)
            logging.info(f"Navigation error screenshot saved: {filename}")
            send_email(
                subject="Faucet Navigation Failed",
                body=f"Could not reach faucet page.\nTime: {time.ctime()}",
                attachment_path=filename,
            )
            return

        # Check Google login state automatically 
        try:
            # Look for any element that contains "Sign in" text
            signin_locator = page.get_by_text(re.compile(r"sign in", re.I))

            if signin_locator.is_visible(timeout=3000):  # check within 3s
                logging.info("You are NOT logged in. Please sign into Google in the opened Chrome window")

                # Wait until "Sign in" text disappears OR until timeout (5 minutes)
                try:
                    page.wait_for_function(
                        """() => !document.body.innerText.match(/sign in/i)""",
                        timeout=300000  # 5 minutes
                    )
                    logging.info("Google login detected automatically (Sign in disappeared)")
                except Exception:
                    logging.warning("Timeout waiting for login. You can still press ENTER to continue")
                    input(">>> Press ENTER here once you finished logging in")

                # Save session snapshot
                try:
                    context.storage_state(path=SESSION_FILE)
                    logging.info(f"Google session saved (snapshot exported to {SESSION_FILE})")
                except Exception as e:
                    logging.warning(f"Could not export storage_state: {e}")

            else:
                logging.info("Google account is already logged in, continuing")

        except Exception as e:
            logging.warning(f"Could not check login state automatically: {e}")


        # Select network
        logging.info(f"[STEP] Select network: {SELECTED_NETWORK}")
        page.get_by_role("combobox", name="Select network").click()
        page.get_by_role("option", name=SELECTED_NETWORK).click()
        logging.info(f"[SUCCESS] Selected network: {SELECTED_NETWORK}")


        # Fill the wallet address
        logging.info("[STEP] Filling wallet address")
        page.get_by_placeholder(re.compile(r"0x|vitalik\.eth", re.I)).fill(TARGET_ADDRESS) # Regex to find the correct placeholder
        logging.info(f"[SUCCESS] Wallet address filled: {TARGET_ADDRESS}")

        
        # Click on the Recieve button
        logging.info("[STEP] Clicking on Receive button")
        page.get_by_role("button", name=re.compile(r"receive.*sepolia\s*eth", re.I)).click()
        logging.info("[SUCCESS] Clicked on Receive button")


        # Check the response - daily limit/success/fail
        # Check for daily limit
        try:
            page.get_by_text(re.compile(r"Each Google Account.*one drip", re.I)).wait_for(timeout=3000)
            logging.warning("[LIMIT] Daily limit reached - wait 24h")
            filename = os.path.join(SCREENSHOT_DIR, f"faucet_limit_{int(time.time())}.png")
            page.screenshot(path=filename)
            logging.info(f"Daily limit screenshot saved: {filename}")
            send_email(
                subject="Faucet Daily Limit Reached",
                body=f"Daily limit reached. Please try again after 24h.\nAddress: {TARGET_ADDRESS}\nTime: {time.ctime()}", attachment_path=filename)
            return
        except:
            logging.info("No daily limit detected - continuing")


        # Checks for success or fail
        status = wait_for_status(page, timeout=30000)

        filename = os.path.join(SCREENSHOT_DIR, f"faucet_{status}_{int(time.time())}.png")
        page.screenshot(path=filename)

        if status == "success":
            logging.info(f"Screenshot saved: {filename}")
            send_email(
                subject="Faucet Success",
                body=f"Faucet request succeeded!\nAddress: {TARGET_ADDRESS}\nTime: {time.ctime()}", attachment_path=filename)
        else:
            logging.error("Faucet request failed or timed out")
            logging.info(f"Error screenshot saved: {filename}")
            send_email(
                subject="Faucet Failed",
                body=f"Faucet request failed or timed out.\nAddress: {TARGET_ADDRESS}\nTime: {time.ctime()}", attachment_path=filename)
            return
        

        # Close the browser
        context.close()


if __name__ == "__main__":
    main()
