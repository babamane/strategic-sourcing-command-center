import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DATA_DIR = os.getenv("DATA_DIR", "data")

# If modifying these scopes, delete the file token.json.
# We need read/write to set up the push watch.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def setup_watch():
    """Authenticates with Gmail and sets up the Pub/Sub push notification watch."""
    
    # --- CONFIGURATION (LOADED FROM .ENV) ---
    PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-project-id")
    TOPIC_NAME = os.getenv("GCP_TOPIC_NAME", "cra-webhook-topic") 
    
    FULL_TOPIC_NAME = f"projects/{PROJECT_ID}/topics/{TOPIC_NAME}"
    # ------------------------------------

    creds = None
    token_path = os.path.join(DATA_DIR, 'token.json')
    creds_path = os.path.join(DATA_DIR, 'credentials.json')

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # You must generate credentials.json from GCP -> APIs & Services -> Credentials -> Create OAuth Client ID (Desktop App)
            if not os.path.exists(creds_path):
                print(f"🚨 Error: '{creds_path}' not found!")
                print("1. Go to Google Cloud Console -> APIs & Services -> Credentials.")
                print("2. Create 'OAuth client ID' for a 'Desktop app'.")
                print(f"3. Download JSON and rename it to 'credentials.json' in the '{DATA_DIR}' folder.")
                return

            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)

        request_body = {
            "labelIds": ["INBOX"],
            "topicName": FULL_TOPIC_NAME
        }
        
        print(f"📡 Sending watch request to bind inbox to {FULL_TOPIC_NAME}...")
        response = service.users().watch(userId='me', body=request_body).execute()
        
        print("\n✅ Success! Gmail is now hooked to your Pub/Sub topic.")
        print(f"History ID created: {response.get('historyId')}")
        print("Your Fast API endpoint will now receive webhooks whenever new emails arrive.")

    except Exception as error:
        print(f"❌ An error occurred: {error}")
        print("Double check that you granted 'gmail-api-push@system.gserviceaccount.com' the 'Pub/Sub Publisher' role on your topic.")

if __name__ == '__main__':
    setup_watch()
