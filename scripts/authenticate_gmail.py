import os
import sys

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google_auth_oauthlib.flow import InstalledAppFlow
from config.settings import settings

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]

def authenticate():
    cred_path = settings.gmail_credentials_path
    token_path = settings.gmail_token_path

    if not os.path.exists(cred_path):
        print(f"ERROR: Credentials file not found at '{cred_path}'.")
        print("Please place your downloaded 'gmail_credentials.json' from Google Cloud Console in the 'credentials/' folder.")
        sys.exit(1)

    print(f"Starting Google OAuth flow using '{cred_path}'...")
    print("A browser window will open automatically. Sign in and grant the requested permissions.")
    print("If you see 'Google hasn't verified this app', click 'Advanced' -> 'Go to Email Routing System (unsafe)'.\n")

    try:
        flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)
        creds = flow.run_local_server(port=0)

        os.makedirs(os.path.dirname(token_path) or ".", exist_ok=True)
        with open(token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

        print("\n=======================================================")
        print(" SUCCESS! Gmail OAuth Token generated successfully!")
        print(f" Saved to: {token_path}")
        print("=======================================================")
        print("\nNEXT STEP FOR RENDER DEPLOYMENT:")
        print("1. Open 'credentials/gmail_token.json' in VS Code and copy its entire contents.")
        print("2. Go to your Render Dashboard -> Service -> Environment -> Secret Files.")
        print("3. Edit 'gmail_token.json', paste the copied content, and click Save.")
        print("=======================================================\n")
    except Exception as e:
        print(f"\nAuthentication failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    authenticate()
