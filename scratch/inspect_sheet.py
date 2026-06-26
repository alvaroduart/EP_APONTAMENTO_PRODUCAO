import os
import sys
import django

# Set up paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from producao.infrastructure.repositories import GoogleSheetsProducaoRepository

def main():
    try:
        repo = GoogleSheetsProducaoRepository()
        print("Fetching parsed OPs...")
        ops = repo.list_ops()
        
        print(f"Successfully parsed {len(ops)} OPs.")
        print("\nParsed OPs sample:")
        for op in ops[:10]:
            print(f"ID: {op.id} | Cliente: {op.cliente} | Produto: {op.descricao_produto}")
            
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
