"""
Configurações do Bot - Foxbit
"""

import os

from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

class Config:
    # Foxbit API (opcional - para modo real)
    API_KEY = os.getenv('FOXBIT_API_KEY', '')
    API_SECRET = os.getenv('FOXBIT_API_SECRET', '')
    
    # URLs das APIs
    FOXBIT_URL = "https://api.foxbit.com.br/rest/v3"
    COINGECKO_URL = "https://api.coingecko.com/api/v3"
    
    # Parâmetros de trading
    SYMBOL = "BTCBRL"  # Par Bitcoin/Real
    BUY_THRESHOLD = -2.0  # Comprar quando cair 2%
    SELL_THRESHOLD = 4.0  # Vender quando subir 4%
    STOP_LOSS = -3.0      # Stop loss
    MAX_TRADES_PER_DAY = 3  # Limite diário de trades
    MAX_BUYS = 3  # Número máximo de compras em escala (scale-in)
    
    # Configurações do bot
    CHECK_INTERVAL = 30  # Segundos entre verificações
    SIMULATION_MODE = True  # True = só observa | False = opera de verdade
