import os
from pathlib import Path
from instagrapi import Client
from dotenv import load_dotenv

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
# The login function will prompt for 2FA if needed
cl.login(username, password)

# Save the session
cl.dump_settings(session_file)

print(f"\nSUCCESS! Session has been saved to '{session_file}'.")
print("The main script can now upload to Instagram without needing to log in again.") 