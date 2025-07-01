import os
from pathlib import Path
from instagrapi import Client
from dotenv import load_dotenv
import sys

print("--- Instagram Login Helper ---")
print("This script will help you log in to Instagram and save your session.")
print("You only need to run this once, or when your session expires.\n")

load_dotenv()

cl = Client()
session_file = Path("session.json")

# Get username and password
username = os.getenv('INSTAGRAM_USERNAME')
password = os.getenv('INSTAGRAM_PASSWORD')

if not username or not password:
    print("Could not find Instagram credentials in your .env file.")
    username = input("Please enter your Instagram username: ")
    password = input("Please enter your Instagram password: ")

print(f"Logging in as {username}...")

try:
    cl.login(username, password)
    # Save the session only if login is successful
    cl.dump_settings(session_file)
    print(f"\nSUCCESS! Session has been saved to '{session_file}'.")
    print("The main script can now upload to Instagram without needing to log in again.")
except Exception as e:
    print(f"\nERROR: Login failed. Reason: {e}")
    if "challenge_required" in str(e) or "Please check the code" in str(e):
        print("Instagram is requiring additional verification (challenge/2FA).\n" \
              "Please check your email/phone for a code, and try again.\n" \
              "If the problem persists, log in via browser to complete any security checks.")
    elif "Please wait a few minutes before you try again." in str(e):
        print("Instagram is rate-limiting your login attempts. Please wait and try again later.")
    else:
        print("An unknown error occurred. Please check your credentials and network connection.")
    sys.exit(1) 