from solana.rpc.api import Client
from solders.pubkey import Pubkey
import requests
import numpy as np
import talib
from telegram import Bot
import asyncio

# Configuração da conexão com Solana
solana_client = Client("https://api.mainnet-beta.solana.com")
wallet_address = Pubkey.from_string("CDXiTWKFzujsAy4jsXPF2q94QBidhRD76CxHCb442Q2X")

def verificar_saldo(wallet):
    saldo = solana_client.get_balance(wallet)
    print(f"Saldo da carteira: {saldo.value / 1e9} SOL")  # Corrigido acesso ao saldo
verificar_saldo(wallet_address)

# Coleta de preços via Jupiter DEX
JUPITER_API = "https://quote-api.jup.ag/v6/quote?inputMint=So11111111111111111111111111111111111111112&outputMint=Es9vMFrzaCERpsYZnRbw7pJZrJmPfqoaQhSsqPdsCw66&amount=1000000000&slippageBps=50"

def obter_preco_atual():
    try:
        resposta = requests.get(JUPITER_API)
        if resposta.status_code == 200:
            dados = resposta.json()
            if "outAmount" in dados:
                return float(dados["outAmount"]) / 1e6  # Ajuste da unidade para USDT
            else:
                print("Chave 'outAmount' não encontrada na resposta da API.")
        else:
            print(f"❌ Erro ao obter preço. Código: {resposta.status_code}. Resposta: {resposta.text}")
    except Exception as e:
        print(f"Erro ao obter o preço: {e}")
    return None

preco = obter_preco_atual()

# Verifica se o preço foi obtido
if preco is None:
    print("⚠️ Erro ao obter o preço.")
    preco = 0.0  # Define um valor neutro para evitar erros

# Cálculo de indicadores técnicos
precos_historicos = np.array([30, 31, 32, 31.5, 33, 34, 35, 36, 37, 35], dtype=np.float64)

# Média Móvel
media_movel = talib.SMA(precos_historicos, timeperiod=5)

# RSI
rsi = talib.RSI(precos_historicos, timeperiod=14)

# Verifica valores inválidos
if np.isnan(media_movel[-1]):
    media_movel[-1] = np.mean(precos_historicos[-5:])  # Usa média dos últimos valores

if np.isnan(rsi[-1]):
    rsi[-1] = 50  # Define um valor neutro para o RSI

print(f"Média Móvel: {media_movel[-1]}")
print(f"RSI: {rsi[-1]}")

# Geração de sinais
def gerar_sinal(preco_atual, media_movel, rsi):
    if preco_atual is None or np.isnan(media_movel[-1]) or np.isnan(rsi[-1]):
        return "ERRO"  # Evita erro por comparação com NoneType
    
    if preco_atual > media_movel[-1] and rsi[-1] < 30:
        return "COMPRA"
    elif preco_atual < media_movel[-1] and rsi[-1] > 70:
        return "VENDA"
    else:
        return "NEUTRO"

sinal = gerar_sinal(preco, media_movel, rsi)
print(f"SINAL GERADO: {sinal}")

# Envio de sinais para o Telegram
TOKEN_TELEGRAM = "7941033937:AAGrj4Da_zRLo5IlWLvZurwZObNzkDien4I"
CHAT_ID = "7655798801"

async def enviar_sinal_telegram(sinal, preco):
    bot = Bot(token=TOKEN_TELEGRAM)
    mensagem = f"Sinal de Trading \n\nSinal: {sinal}\nPreço: {preco} USDT\n\n#Solana #Crypto"
    await bot.send_message(chat_id=CHAT_ID, text=mensagem)

# Chamada assíncrona para evitar warning
asyncio.run(enviar_sinal_telegram(sinal, preco))
