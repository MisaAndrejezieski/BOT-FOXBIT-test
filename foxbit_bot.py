"""
BOT DE TRADING PARA FOXBIT
Acompanha preços REAIS em tempo real
Estratégia: COMPRA -2% | VENDA +4%
"""

import json
import os
import time
from datetime import date, datetime

import requests

from config import Config


class FoxbitBot:
    def __init__(self):
        self.config = Config()
        self.capital = 1000  # Capital inicial para simulação
        self.capital_inicial = 1000
        self.position = None
        self.price_history = []
        self.trades_today = 0
        self.last_trade_date = date.today()
        self.total_trades = []
        
        print("\n" + "="*70)
        print("🤖 BOT FOXBIT - PREÇOS EM TEMPO REAL")
        print("="*70)
        print(f"📊 Modo: {'🔍 OBSERVAÇÃO' if self.config.SIMULATION_MODE else '💰 REAL'}")
        print(f"📈 Estratégia: COMPRA {self.config.BUY_THRESHOLD}% | VENDA +{self.config.SELL_THRESHOLD}%")
        print(f"🛑 Stop Loss: {self.config.STOP_LOSS}%")
        print(f"⏱️  Atualização: a cada {self.config.CHECK_INTERVAL} segundos")
        print("="*70)
    
    def get_preco_foxbit(self):
        """
        Busca preço REAL da Foxbit via API pública
        Retorna: (preço, volume, variação_24h)
        """
        try:
            # Endpoint público da Foxbit (não precisa de API Key)
            url = f"{self.config.FOXBIT_URL}/ticker"
            params = {'market_symbol': self.config.SYMBOL}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                dados = response.json()
                if 'data' in dados and len(dados['data']) > 0:
                    preco = float(dados['data'][0]['last'])
                    volume = float(dados['data'][0]['volume'])
                    
                    # Busca variação em outra API
                    variacao = self.get_variacao_coingecko()
                    
                    return preco, volume, variacao
            else:
                print(f"⚠️ Foxbit API retornou código {response.status_code}")
        except Exception as e:
            print(f"⚠️ Erro ao acessar Foxbit: {e}")
        
        # Fallback: CoinGecko
        return self.get_preco_coingecko()
    
    def get_preco_coingecko(self):
        """
        Fallback: Busca preço da CoinGecko (gratuito e confiável)
        """
        try:
            url = f"{self.config.COINGECKO_URL}/simple/price"
            params = {
                'ids': 'bitcoin',
                'vs_currencies': 'brl',
                'include_24hr_change': 'true',
                'include_last_updated_at': 'true'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                dados = response.json()
                preco = float(dados['bitcoin']['brl'])
                variacao = float(dados['bitcoin']['brl_24h_change'])
                
                print("   📡 Fonte: CoinGecko")
                return preco, 0, variacao
        except Exception as e:
            print(f"⚠️ Erro ao acessar CoinGecko: {e}")
        
        return None, None, None
    
    def get_variacao_coingecko(self):
        """Busca variação de 24h na CoinGecko"""
        try:
            url = f"{self.config.COINGECKO_URL}/simple/price"
            params = {
                'ids': 'bitcoin',
                'vs_currencies': 'brl',
                'include_24hr_change': 'true'
            }
            response = requests.get(url, params=params, timeout=5)
            dados = response.json()
            return float(dados['bitcoin']['brl_24h_change'])
        except:
            return 0
    
    def analisar_compra(self, preco_atual):
        """Analisa se deve comprar baseado na queda"""
        if len(self.price_history) < 2:
            return False, 0
        
        # Calcula variação percentual
        variacao = (preco_atual - self.price_history[-2]) / self.price_history[-2] * 100
        
        if variacao <= self.config.BUY_THRESHOLD:
            return True, variacao
        return False, variacao
    
    def analisar_venda(self, preco_atual):
        """Analisa se deve vender baseado no lucro"""
        if not self.position:
            return False, 0
        
        buy_price = self.position['price']
        lucro = (preco_atual - buy_price) / buy_price * 100
        
        if lucro >= self.config.SELL_THRESHOLD:
            return True, lucro
        elif lucro <= self.config.STOP_LOSS:
            return True, lucro
        return False, lucro
    
    def reset_daily_counter(self):
        """Reseta contador diário de trades"""
        today = date.today()
        if today > self.last_trade_date:
            self.trades_today = 0
            self.last_trade_date = today
    
    def comprar_simulado(self, preco, variacao):
        """Simula uma compra (sem dinheiro real)"""
        if self.trades_today >= self.config.MAX_TRADES_PER_DAY:
            print(f"   ⚠️ Limite diário de {self.config.MAX_TRADES_PER_DAY} trades atingido")
            return False
        
        quantidade = self.capital / preco
        
        self.position = {
            'price': preco,
            'quantity': quantidade,
            'time': datetime.now(),
            'variacao': variacao
        }
        
        self.capital = 0
        self.trades_today += 1
        
        print(f"\n🟢 SINAL DE COMPRA (SIMULADO)!")
        print(f"   Preço: R$ {preco:,.2f}")
        print(f"   Quantidade: {quantidade:.6f} BTC")
        print(f"   Variação: {variacao:.2f}%")
        print(f"   💰 Seria gasto: R$ {quantidade * preco:,.2f}")
        
        return True
    
    def vender_simulado(self, preco, lucro):
        """Simula uma venda (sem dinheiro real)"""
        if not self.position:
            return False
        
        valor_venda = self.position['quantity'] * preco
        lucro_abs = valor_venda - (self.position['quantity'] * self.position['price'])
        
        self.capital = valor_venda
        
        # Registra trade simulado
        trade = {
            'compra_price': self.position['price'],
            'venda_price': preco,
            'quantidade': self.position['quantity'],
            'lucro_percent': lucro,
            'lucro_abs': lucro_abs,
            'tempo': (datetime.now() - self.position['time']).total_seconds() / 60,
            'data': datetime.now()
        }
        self.total_trades.append(trade)
        
        print(f"\n🔴 SINAL DE VENDA (SIMULADO)!")
        print(f"   Preço: R$ {preco:,.2f}")
        print(f"   Lucro: {lucro:.2f}%")
        print(f"   Lucro R$: R$ {lucro_abs:.2f}")
        print(f"   Tempo em posição: {trade['tempo']:.1f} minutos")
        
        self.position = None
        return True
    
    def mostrar_status(self, preco, variacao_24h):
        """Mostra status atual com preços reais"""
        print("\n" + "-"*70)
        print(f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"💰 BTC/BRL: R$ {preco:,.2f}")
        
        if variacao_24h:
            seta = "▲" if variacao_24h > 0 else "▼"
            print(f"📊 24h: {seta} {variacao_24h:+.2f}%")
        
        # Mostra análise técnica
        if len(self.price_history) > 1:
            variacao = (preco - self.price_history[-2]) / self.price_history[-2] * 100
            print(f"📈 Variação atual: {variacao:+.2f}%")
        
        if self.position:
            lucro = (preco - self.position['price']) / self.position['price'] * 100
            print(f"📌 Em posição: {self.position['quantity']:.6f} BTC")
            print(f"📈 Lucro atual: {lucro:.2f}%")
            print(f"🎯 Alvo venda: +{self.config.SELL_THRESHOLD}%")
            print(f"🛑 Stop loss: {self.config.STOP_LOSS}%")
        else:
            print(f"💤 Aguardando queda de {self.config.BUY_THRESHOLD}%")
        
        print(f"📊 Trades simulados hoje: {self.trades_today}/{self.config.MAX_TRADES_PER_DAY}")
        print(f"💰 Capital simulado: R$ {self.capital:,.2f}")
        print("-"*70)
    
    def executar(self):
        """
        Loop principal do bot com preços REAIS
        """
        print(f"\n🔍 Conectando às APIs de preço...")
        print("="*70)
        
        # Testa conexão inicial
        preco, volume, variacao = self.get_preco_foxbit()
        if preco:
            print(f"✅ Conectado! Preço atual: R$ {preco:,.2f}")
        else:
            print("⚠️ Usando modo offline para testes")
        
        try:
            while True:
                # Reseta contador diário
                self.reset_daily_counter()
                
                # Busca preço REAL
                preco, volume, variacao = self.get_preco_foxbit()
                
                if preco:
                    # Atualiza histórico
                    self.price_history.append(preco)
                    if len(self.price_history) > 100:
                        self.price_history.pop(0)
                    
                    # Mostra status
                    self.mostrar_status(preco, variacao)
                    
                    # Análise de trading (simulada)
                    if not self.position:
                        comprar, variacao_atual = self.analisar_compra(preco)
                        if comprar:
                            self.comprar_simulado(preco, variacao_atual)
                    else:
                        vender, lucro = self.analisar_venda(preco)
                        if vender:
                            self.vender_simulado(preco, lucro)
                else:
                    print("\n❌ Erro ao buscar preços. Tentando novamente...")
                
                # Aguarda próximo ciclo
                time.sleep(self.config.CHECK_INTERVAL)
                
        except KeyboardInterrupt:
            self.mostrar_relatorio()
    
    def executar_manual(self):
        """Loop para acompanhamento com operações manuais"""
        executar_acompanhamento_manual(self)
    
    def mostrar_relatorio(self):
        """Mostra relatório da simulação"""
        print("\n" + "="*70)
        print("📊 RELATÓRIO DA SIMULAÇÃO")
        print("="*70)
        
        if self.total_trades:
            lucros = [t['lucro_percent'] for t in self.total_trades]
            lucros_abs = [t['lucro_abs'] for t in self.total_trades]
            tempos = [t['tempo'] for t in self.total_trades]
            
            print(f"\n📈 ESTATÍSTICAS:")
            print(f"   Total de trades: {len(self.total_trades)}")
            print(f"   Trades com lucro: {len([l for l in lucros if l > 0])}")
            print(f"   Trades com prejuízo: {len([l for l in lucros if l < 0])}")
            print(f"   Win Rate: {len([l for l in lucros if l > 0])/len(lucros)*100:.1f}%")
            print(f"   Lucro médio: {sum(lucros)/len(lucros):.2f}%")
            print(f"   Maior lucro: {max(lucros):.2f}%")
            print(f"   Maior prejuízo: {min(lucros):.2f}%")
            
            print(f"\n💰 RESULTADO FINANCEIRO:")
            print(f"   Capital inicial: R$ {self.capital_inicial:,.2f}")
            print(f"   Capital final: R$ {self.capital:,.2f}")
            print(f"   Lucro total: R$ {self.capital - self.capital_inicial:,.2f}")
            print(f"   Rentabilidade: {(self.capital/self.capital_inicial - 1)*100:.2f}%")
            
            print(f"\n📋 ÚLTIMOS TRADES:")
            for trade in self.total_trades[-3:]:
                print(f"   • Compra: R$ {trade['compra_price']:,.0f} → "
                      f"Venda: R$ {trade['venda_price']:,.0f} | "
                      f"Lucro: {trade['lucro_percent']:.2f}%")
        else:
            print("\nNenhum trade foi executado na simulação")
        
        print("\n" + "="*70)
        print("✅ Simulação encerrada")
        print("="*70)

    def compra_manual(self, quantidade_btc, preco_compra):
        """Compra manual com quantidade customizável"""
        if self.position:
            print(f"❌ Já possui uma posição ativa! Venda primeiro.")
            return False
        
        if quantidade_btc <= 0:
            print(f"❌ Quantidade deve ser maior que zero")
            return False
        
        valor_gasto = quantidade_btc * preco_compra
        
        if valor_gasto > self.capital:
            print(f"❌ Capital insuficiente!")
            print(f"   Disponível: R$ {self.capital:,.2f}")
            print(f"   Necessário: R$ {valor_gasto:,.2f}")
            return False
        
        self.position = {
            'price': preco_compra,
            'quantity': quantidade_btc,
            'time': datetime.now(),
            'variacao': 0,
            'manual': True
        }
        
        self.capital -= valor_gasto
        self.trades_today += 1
        
        print(f"\n🟢 COMPRA MANUAL REALIZADA!")
        print(f"   Preço: R$ {preco_compra:,.2f}")
        print(f"   Quantidade: {quantidade_btc:.6f} BTC")
        print(f"   Valor gasto: R$ {valor_gasto:,.2f}")
        print(f"   Capital restante: R$ {self.capital:,.2f}")
        print(f"   Hora: {datetime.now().strftime('%H:%M:%S')}")
        
        return True
    
    def venda_manual(self, preco_venda):
        """Venda manual da posição atual"""
        if not self.position:
            print(f"❌ Não há posição ativa para vender!")
            return False
        
        valor_venda = self.position['quantity'] * preco_venda
        valor_compra = self.position['quantity'] * self.position['price']
        lucro_abs = valor_venda - valor_compra
        lucro_percent = (lucro_abs / valor_compra) * 100
        
        self.capital += valor_venda
        
        # Registra trade manual
        trade = {
            'compra_price': self.position['price'],
            'venda_price': preco_venda,
            'quantidade': self.position['quantity'],
            'lucro_percent': lucro_percent,
            'lucro_abs': lucro_abs,
            'tempo': (datetime.now() - self.position['time']).total_seconds() / 60,
            'data': datetime.now(),
            'manual': True
        }
        self.total_trades.append(trade)
        
        print(f"\n🔴 VENDA MANUAL REALIZADA!")
        print(f"   Preço: R$ {preco_venda:,.2f}")
        print(f"   Quantidade vendida: {self.position['quantity']:.6f} BTC")
        print(f"   Valor ganho: R$ {valor_venda:,.2f}")
        print(f"   Lucro: R$ {lucro_abs:+,.2f} ({lucro_percent:+.2f}%)")
        print(f"   Tempo em posição: {trade['tempo']:.1f} minutos")
        print(f"   Capital agora: R$ {self.capital:,.2f}")
        print(f"   Hora: {datetime.now().strftime('%H:%M:%S')}")
        
        self.position = None
        return True
    
    def menu_operador(self, preco_atual):
        """Menu para operações manuais durante acompanhamento"""
        print(f"\n{'='*70}")
        print(f"💡 PREÇO ATUAL: R$ {preco_atual:,.2f}")
        print(f"{'='*70}")
        print("\n📋 OPÇÕES DE OPERAÇÃO:")
        print("  [1] 🟢 Comprar manualmente")
        print("  [2] 🔴 Vender manualmente")
        print("  [3] 📊 Ver posição atual")
        print("  [4] 💰 Ver capital")
        print("  [5] 📈 Continuar acompanhando")
        print("  [0] ❌ Encerrar")
        print("-"*70)


def menu():
    """Menu principal"""
    print("""
╔══════════════════════════════════════════════════════════╗
║   BOT FOXBIT - ACOMPANHAMENTO EM TEMPO REAL             ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║   Este bot ACOMPANHA preços REAIS da Foxbit             ║
║   e SIMULA trades baseados na estratégia -2%/+4%        ║
║                                                          ║
║   📍 SEM RISCO - Apenas observação e simulação          ║
║   📍 Preços atualizados a cada 30 segundos              ║
║   📍 Operações manuais disponíveis                      ║
║   📍 Estratégia testada com dados REAIS do mercado      ║
║                                                          ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║   [1] Modo AUTOMÁTICO (estratégia -2%/+4%)             ║
║   [2] Modo MANUAL (você controla as operações)          ║
║   [0] Sair                                              ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    opcao = input("   ▶️  Escolha uma opção: ").strip()
    
    if opcao == "1":
        print("\n🤖 Iniciando modo AUTOMÁTICO...")
        bot = FoxbitBot()
        bot.executar()
    elif opcao == "2":
        print("\n👤 Iniciando modo MANUAL...")
        bot = FoxbitBot()
        bot.executar_manual()
    else:
        print("   ✅ Encerrando...")


def executar_acompanhamento_manual(bot):
    """
    Loop para acompanhamento com operações manuais
    """
    print(f"\n🔍 Conectando às APIs de preço...")
    print("="*70)
    
    # Testa conexão inicial
    preco, volume, variacao = bot.get_preco_foxbit()
    if preco:
        print(f"✅ Conectado! Preço atual: R$ {preco:,.2f}")
    else:
        print("⚠️ Usando modo offline para testes")
    
    input("\nPressione ENTER para começar...")
    
    try:
        while True:
            # Reseta contador diário
            bot.reset_daily_counter()
            
            # Busca preço REAL
            preco, volume, variacao = bot.get_preco_foxbit()
            
            if preco:
                # Atualiza histórico
                bot.price_history.append(preco)
                if len(bot.price_history) > 100:
                    bot.price_history.pop(0)
                
                # Mostra status
                bot.mostrar_status(preco, variacao)
                
                # Menu de operações
                bot.menu_operador(preco)
                
                opcao = input("   ▶️  Opção: ").strip()
                
                if opcao == "1":
                    try:
                        qtd = float(input("   Quantidade de BTC: "))
                        preco_compra = float(input("   Preço de compra (ENTER para preço atual): ").strip() or preco)
                        bot.compra_manual(qtd, preco_compra)
                    except ValueError:
                        print("   ❌ Valor inválido!")
                
                elif opcao == "2":
                    try:
                        preco_venda = float(input("   Preço de venda (ENTER para preço atual): ").strip() or preco)
                        bot.venda_manual(preco_venda)
                    except ValueError:
                        print("   ❌ Valor inválido!")
                
                elif opcao == "3":
                    if bot.position:
                        lucro = (preco - bot.position['price']) / bot.position['price'] * 100
                        print(f"\n📌 POSIÇÃO ATIVA:")
                        print(f"   Quantidade: {bot.position['quantity']:.6f} BTC")
                        print(f"   Preço de entrada: R$ {bot.position['price']:,.2f}")
                        print(f"   Preço atual: R$ {preco:,.2f}")
                        print(f"   Lucro/Prejuízo: {lucro:+.2f}%")
                        print(f"   Valor: R$ {bot.position['quantity'] * preco:,.2f}")
                    else:
                        print(f"\n💤 Sem posição ativa")
                
                elif opcao == "4":
                    print(f"\n💰 CAPITAL: R$ {bot.capital:,.2f}")
                    print(f"   Capital inicial: R$ {bot.capital_inicial:,.2f}")
                    if bot.position:
                        print(f"   Investido: R$ {bot.position['quantity'] * bot.position['price']:,.2f}")
                
                elif opcao == "5":
                    print("   ⏳ Aguardando próximo ciclo...")
                    time.sleep(bot.config.CHECK_INTERVAL)
                
                elif opcao == "0":
                    bot.mostrar_relatorio()
                    return
                
                else:
                    print("   ⚠️ Opção inválida!")
                    time.sleep(1)
            else:
                print("\n❌ Erro ao buscar preços. Tentando novamente...")
                time.sleep(5)
            
    except KeyboardInterrupt:
        bot.mostrar_relatorio()

if __name__ == "__main__":
    menu()
