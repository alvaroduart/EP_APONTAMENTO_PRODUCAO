import os
from django.core.management.base import BaseCommand
from django.conf import settings
from google_auth_oauthlib.flow import InstalledAppFlow

class Command(BaseCommand):
    help = 'Autentica a aplicação com a API do Google Sheets e gera o arquivo token.json'

    def handle(self, *args, **options):
        credentials_path = settings.CREDENTIALS_FILE
        token_path = settings.TOKEN_FILE

        if not os.path.exists(credentials_path):
            self.stdout.write(self.style.ERROR(f'Arquivo de credenciais não encontrado em: {credentials_path}'))
            return

        scopes = ['https://www.googleapis.com/auth/spreadsheets']

        self.stdout.write('Iniciando o fluxo de autenticação do Google...')
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
        
        # Abre o navegador local para autenticar
        creds = flow.run_local_server(port=0)

        # Salva o token.json para futuras requisições
        with open(token_path, 'w', encoding='utf-8') as token_file:
            token_file.write(creds.to_json())

        self.stdout.write(self.style.SUCCESS(f'Autenticação realizada com sucesso! Token salvo em: {token_path}'))
