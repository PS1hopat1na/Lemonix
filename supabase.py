import requests

SUPABASE_URL = 'https://your-project.supabase.co'
SUPABASE_KEY = 'your-api-key'

def get_products():
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}'
    }
    response = requests.get(f'{SUPABASE_URL}/rest/v1/products?select=*', headers=headers)
    if response.status_code == 200:
        return response.json()
    return []
