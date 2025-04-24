# Extração de API Clash Royale

Este projeto coleta dados da API oficial do Clash Royale e armazena as informações em um banco de dados MongoDB.

---

## **📌 Funcionalidades**

**Coleta dados de:**

- Cartas.

- Membros de um clã.

- Batalhas recentes de cada jogador do clã.

**Armazena os dados em coleções MongoDB:**

- cards: Cartas disponíveis no jogo

- battles: Detalhes das batalhas

**Processa os seguintes dados adicionais:**

- Data formatada da batalha ("YYYY/MM/DD")

- Timestamp em segundos

- Diferença de troféus entre jogador e oponente

- Torres destruídas

- Quem venceu a batalha

## **📌 Requisitos**

- Python 3.8+

- MongoDB Atlas ou local

- Acesso à API do Clash Royale (token de desenvolvedor)
  
## **📌 Instalação**

1- Clone este repositório:

  ```bash
git clone https://github.com/seu-usuario/clash-royale-data.git
cd clash-royale-data
```

2- Instale as dependências:

  ```bash
pip install -r requirements.txt
```
3- Configure o token no cabeçalho da requisição (Authorization) no script principal.

## **📌 Uso**

Execute o script principal:

  ```bash
python main.py
```

O script vai:

- Buscar todos os membros de um clã

- Coletar os perfis e últimas batalhas de cada jogador

- Salvar todos os dados no MongoDB
