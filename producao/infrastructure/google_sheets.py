import os
import gspread
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from django.conf import settings

def get_sheets_client():
    token_path = settings.TOKEN_FILE
    
    if not os.path.exists(token_path):
        raise FileNotFoundError(
            f"Arquivo de token não encontrado em: {token_path}. "
            "Por favor, execute o comando: python manage.py authenticate_sheets"
        )
        
    creds = Credentials.from_authorized_user_file(
        token_path, 
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_path, 'w', encoding='utf-8') as token_file:
            token_file.write(creds.to_json())
            
    client = gspread.authorize(creds)
    return client

def get_spreadsheet():
    client = get_sheets_client()
    return client.open_by_key(settings.SPREADSHEET_ID)
