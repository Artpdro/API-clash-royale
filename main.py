import requests
import json

URL_CARDS = 'https://api.clashroyale.com/v1/cards'

headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6ImE1ZDU1MzY4LTRhMDMtNGMyMi05Yzk0LTBmMjM4MmUzNWRlNSIsImlhdCI6MTc0NDc2MTcyNCwic3ViIjoiZGV2ZWxvcGVyLzJhNzRiOWNhLTUzMTEtNzZkNi01ZDlkLWUxZTZhOTdkY2I5NSIsInNjb3BlcyI6WyJyb3lhbGUiXSwibGltaXRzIjpbeyJ0aWVyIjoiZGV2ZWxvcGVyL3NpbHZlciIsInR5cGUiOiJ0aHJvdHRsaW5nIn0seyJjaWRycyI6WyIxNDMuMjA4LjEyOC4xMjIiXSwidHlwZSI6ImNsaWVudCJ9XX0.9xkwxR25EGBq2qcMopXhYa4U7JDg61sBWJ5jtN-M3InkHz5cuXXRDjEFQXGJk24e4CCEgjfVFV2YeAuh1bfHAg'
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
