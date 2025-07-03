import os
import time
import random
from instagrapi import Client

# CONFIGURATION
username = "the_hell_bot"
password = "Rohit@123"
target_username = "natgeo"  # Change this to any account whose followers you want to follow
follows_per_session = 30
pause_hours = 3
min_delay = 10
max_delay = 60

def login(cl):
    try:
        cl.login(username, password)
        print(f"Logged in as {username}.")
        return True
    except Exception as e:
        print(f"Failed to log in: {e}")
        return False

def main():
    cl = Client()
    if not login(cl):
        return
    while True:
        try:
            print(f"\nFetching followers of {target_username}...")
            target_user_id = cl.user_id_from_username(target_username)
            followers = cl.user_followers(target_user_id, amount=follows_per_session*2)
            print(f"Found {len(followers)} followers. Starting to follow...")
            followed_count = 0
            for user_id, user in followers.items():
                if followed_count >= follows_per_session:
                    print(f"Session limit reached ({follows_per_session}). Pausing for {pause_hours} hours...")
                    time.sleep(pause_hours * 3600)
                    if not login(cl):
                        return
                    followed_count = 0
                try:
                    print(f"Attempting to follow: {user.username} (ID: {user_id})")
                    result = cl.user_follow(user_id)
                    print(f"Follow attempt result for {user.username}: {result}")
                    followed_count += 1
                except Exception as e:
                    if 'login_required' in str(e):
                        print("Session expired or blocked. Re-logging in...")
                        if not login(cl):
                            return
                        continue
                    print(f"Failed to follow {user.username}: {e}")
                delay = random.uniform(min_delay, max_delay)
                print(f"Waiting {delay:.1f} seconds before next action...")
                time.sleep(delay)
        except Exception as e:
            print(f"Major error: {e}. Pausing for 10 minutes before retrying...")
            time.sleep(600)
            if not login(cl):
                return

if __name__ == "__main__":
    main() 