from solana.rpc.api import Client as SolanaClient
from solders.pubkey import Pubkey as ChavePublica
import requests
import pandas as pd
from ta.trend import SMAIndicator as IndicadorSMA
from ta.momentum import RSIIndicator as IndicadorRSI
from telegram import Bot as TelegramBot
import asyncio


cliente_solana = SolanaClient("https://api.mainnet-beta.solana.com")


endereco_carteira = "DXiTWKFzujsAy4jsXPF2q94QBidhRD76CxHCb442Q2X"


URL_JUPITER = "https://quote-api.jup.ag/v6/quote?inputMint=So11111111111111111111111111111111111111112&outputMint=Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB&amount=1000000000&slippageBps=50"


def consultar_saldo(carteira):
    try:
        if len(carteira.strip()) != 44:
            print(f"Erro: Endereço inválido ({len(carteira)} caracteres, esperado 44)")
            return
        chave = ChavePublica.from_string(carteira)
        saldo = cliente_solana.get_balance(chave).value
        print(f"Saldo disponível: {saldo / 1e9:.4f} SOL")
    except Exception as erro:
        print(f"Erro ao obter saldo: {erro}")

# Função para recuperar o preço SOL/USDT

def obter_preco():
    try:
        resposta = requests.get(URL_JUPITER, timeout=10)
        info = resposta.json()
        valor = float(info["outAmount"]) / 1e6
        return valor if valor > 0 else None
    except Exception as erro:
        print(f"Erro ao consultar preço: {erro}")
        return None

# Função para determinar sinal de trading

def calcular_sinal(preco, media_movel, indice_rsi):
    if None in (preco, media_movel, indice_rsi) or pd.isna(media_movel) or pd.isna(indice_rsi):
        return "DADOS INSUFICIENTES"
    if preco > media_movel and indice_rsi < 40:
        return "COMPRA"
    elif preco < media_movel and indice_rsi > 70:
        return "VENDA"
    return "NEUTRO"

# Envio de sinal para o Telegram

async def enviar_alerta_telegram(sinal, preco):
    bot = TelegramBot(token=TOKEN_BOT_TELEGRAM)
    saldo = consultar_saldo(endereco_carteira)
    mensagem = (f"Sinal de Trading \n\nSinal: {sinal}\nPreço: {preco:.4f} USDT\n\n{saldo}\n\n#Solana #Crypto")
    
    try:
        await bot.send_message(chat_id=ID_CHAT_TELEGRAM, text=mensagem)
        print(f"Mensagem enviada com sucesso: {mensagem}")
    except Exception as erro:
        print(f"Erro ao enviar alerta: {erro}")

# Execução do programa
TOKEN_BOT_TELEGRAM = "7941033937:AAGrj4Da_zRLo5IlWLvZurwZObNzkDien4I"
ID_CHAT_TELEGRAM = "7655798801"
consultar_saldo(endereco_carteira)

preco_atual = obter_preco()
print(f"Preço SOL/USDT: {preco_atual:.4f} USDT" if preco_atual else "Preço indisponível")

historico_precos = [30, 31, 32, 31.5, 33, 34, 35, 36, 37, 35, 36, 37, 38, 39, 40]
dados = pd.DataFrame(historico_precos, columns=["fechamento"])

sma_calculado = IndicadorSMA(dados["fechamento"], window=5).sma_indicator().iloc[-1]
print(f"Média Móvel (5): {sma_calculado:.4f}" if pd.notna(sma_calculado) else "Erro no cálculo do SMA")

rsi_calculado = IndicadorRSI(dados["fechamento"], window=14).rsi().iloc[-1]
print(f"RSI (14): {rsi_calculado:.2f}" if pd.notna(rsi_calculado) else "Erro no cálculo do RSI")

sinal_trade = calcular_sinal(preco_atual, sma_calculado, rsi_calculado)
print(f"SINAL GERADO: {sinal_trade}")

# Envia sinal ao Telegram caso os dados sejam válidos
if sinal_trade != "DADOS INSUFICIENTES":
    asyncio.run(enviar_alerta_telegram(sinal_trade, preco_atual))
