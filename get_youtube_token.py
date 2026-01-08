import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# The permissions the bot needs
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def main():
    if not os.path.exists("client_secret.json"):
        print("ERROR: client_secret.json not found!")
        return

    print("Opening browser for authentication...")
    
    # Run the standard OAuth flow (opens browser)
    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret.json", SCOPES
    )
    creds = flow.run_local_server(port=0)

    # Convert credentials to dictionary
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes
    }

    # Save to file
    with open("youtube_token.json", "w") as f:
        json.dump(token_data, f)

    print("\nSUCCESS! created 'youtube_token.json'")
    print("Now creating the GitHub Secret:")
    print("1. Go to GitHub Secrets")
    print("2. Create 'YOUTUBE_TOKEN_JSON'")
    print("3. Paste the ENTIRE content of youtube_token.json")

if __name__ == "__main__":
    main()
