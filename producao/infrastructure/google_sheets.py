import os
import json
import gspread
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from django.conf import settings

def get_sheets_client():
    token_json_str = os.environ.get('GOOGLE_TOKEN_JSON')
    
    if token_json_str:
        # Load credentials directly from environment variable (ideal for Vercel)
        info = json.loads(token_json_str)
        token_scopes = info.get('scopes', ['https://www.googleapis.com/auth/spreadsheets'])
        creds = Credentials.from_authorized_user_info(
            info,
            scopes=token_scopes
        )
    else:
        # Fallback to local token file
        token_path = settings.TOKEN_FILE
        if not os.path.exists(token_path):
            raise FileNotFoundError(
                f"Arquivo de token não encontrado em: {token_path}. "
                "Por favor, execute o comando: python manage.py authenticate_sheets"
            )
        
        # Load local token scopes dynamically to avoid scope mismatch errors during refresh
        try:
            with open(token_path, 'r', encoding='utf-8') as f:
                token_data = json.load(f)
            token_scopes = token_data.get('scopes', ['https://www.googleapis.com/auth/spreadsheets'])
        except Exception:
            token_scopes = ['https://www.googleapis.com/auth/spreadsheets']

        creds = Credentials.from_authorized_user_file(
            token_path, 
            scopes=token_scopes
        )
    
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Try to save updated token locally if possible (will silently skip on read-only filesystems like Vercel)
        token_json_str = os.environ.get('GOOGLE_TOKEN_JSON')
        if not token_json_str:
            try:
                token_path = settings.TOKEN_FILE
                with open(token_path, 'w', encoding='utf-8') as token_file:
                    token_file.write(creds.to_json())
            except Exception as e:
                # Log warning or skip silently in serverless environments
                print(f"Warning: Could not save refreshed token to local file: {e}")
            
    client = gspread.authorize(creds)
    return client

def get_spreadsheet():
    client = get_sheets_client()
    return client.open_by_key(settings.SPREADSHEET_ID)
