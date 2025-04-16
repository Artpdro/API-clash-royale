import requests
import json

URL_CARDS = 'https://api.clashroyale.com/v1/cards'

headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer'
}

def get_all_cards():
    response = requests.get(URL_CARDS, headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        for card in data.get('items', []):
            print('========================================')
            print('Id:         ', card.get('id'))
            print('Nome:       ', card.get('name'))
            print('Max Level:  ', card.get('maxLevel'))
            print('Imagem:     ', card.get('iconUrls', {}).get('medium'))
            print('========================================')
    else:
        print("Erro na requisição:", response.text)

if __name__ == "__main__":
    get_all_cards()
