from socket import *
import requests
import json
import threading
from datetime import datetime, timedelta

serverPort = 6000

rates_cache = {
    'rates': {},
    'last_update': None,
    'cache_duration': 3600
}

cache_lock = threading.Lock()

client_counter = 0
active_clients = 0
clients_lock = threading.Lock()

# Retorna as taxas de hoje do Banco Central do Brasil de Dólar e Euro para Real
def get_bcb_rates():
    
    try:
        today = datetime.now()
        date_str = today.strftime('%m-%d-%Y')
        
        urls = {
            'USD': f'https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarDia(dataCotacao=@dataCotacao)?@dataCotacao=%27{date_str}%27&$format=json',
            'EUR': f'https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)?@moeda=%27EUR%27&@dataCotacao=%27{date_str}%27&$format=json',
        }
        
        rates = {'BRL': 1.0}
        
        try:
            resp = requests.get(urls['USD'], timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('value'):
                    rates['USD'] = 1.0 / data['value'][0]['cotacaoCompra']
                    print(f'[BCB] USD: {data["value"][0]["cotacaoCompra"]:.4f} BRL')
        except:
            pass
        
        try:
            resp = requests.get(urls['EUR'], timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('value'):
                    rates['EUR'] = 1.0 / data['value'][0]['cotacaoCompra']
                    print(f'[BCB] EUR: {data["value"][0]["cotacaoCompra"]:.4f} BRL')
        except:
            pass
        
        return rates
        
    except Exception as e:
        print(f'[BCB] Erro: {e}')
        return {}

# Combina a ExchangeRate-API com o BCB para obter taxas de câmbio atualizadas.
# Primeiro verifica o cache para evitar chamadas excessivas à API, mas se o cache estiver expirado (1 hora), busca novas taxas.
# Depois tenta obter a cotação pela ExchangeRate-API e substitui a taxa do BRL pela do BCB, se disponível.
# Senão, usa o fallback.
def get_exchange_rates():
    
    with cache_lock:
        now = datetime.now()
        
        if (rates_cache['last_update'] and 
            rates_cache['rates'] and
            (now - rates_cache['last_update']).seconds < rates_cache['cache_duration']):
            print('[CACHE] Usando taxas em cache')
            return rates_cache['rates'], rates_cache['last_update']
        
        print('[API] Buscando taxas atualizadas...')
        
        try:
            
            url = 'https://api.exchangerate-api.com/v4/latest/USD'
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                rates = data['rates']
                
                bcb_rates = get_bcb_rates()
                if 'BRL' in bcb_rates and bcb_rates['BRL'] != 1.0:
                    rates['BRL'] = 1.0 / bcb_rates['BRL']
                    print('[BCB] ✅ Usando cotação oficial do Banco Central para BRL')
                
                rates_cache['rates'] = rates
                rates_cache['last_update'] = now
                
                print(f'[API] ✅ {len(rates)} moedas disponíveis')
                
                return rates, now
            else:
                return get_fallback_rates(), now
                
        except Exception as e:
            print(f'[API] Erro: {e}')
            return get_fallback_rates(), now

# Taxas de câmbio fallback
def get_fallback_rates():
    return {
        'USD': 1.0,
        'BRL': 5.12,
        'EUR': 0.92,
        'GBP': 0.79,
        'JPY': 149.50,
        'CAD': 1.36,
        'AUD': 1.53,
        'CHF': 0.88,
        'CNY': 7.24,
        'ARS': 350.00,
        'MXN': 17.20,
        'CLP': 890.00
    }

# Processa a mensagem de conversão recebida do cliente
# Espera o formato <moeda_origem>|<moeda_destino>|<valor>
# Retorna a resposta no formato:
# SUCESSO|<moeda_origem>|<moeda_destino>|<valor>|<resultado>|<taxa>|<data_atualizacao>|<fonte>
# Ou
# ERRO:<mensagem_erro>
def convert_currency(message):

    try:
        parts = message.split('|')
        
        if len(parts) != 3:
            return "ERRO: Formato inválido. Use: FROM|TO|AMOUNT"
        
        from_curr = parts[0].strip().upper()
        to_curr = parts[1].strip().upper()
        amount = float(parts[2].strip())
        
        rates, last_update = get_exchange_rates()
        
        if from_curr not in rates:
            return f"ERRO: Moeda {from_curr} não suportada"
        
        if to_curr not in rates:
            return f"ERRO: Moeda {to_curr} não suportada"
        
        if amount <= 0:
            return "ERRO: Valor deve ser maior que zero"
        
        usd_amount = amount / rates[from_curr]
        result = usd_amount * rates[to_curr]
        rate = rates[to_curr] / rates[from_curr]
        
        update_time = last_update.strftime('%Y-%m-%d %H:%M:%S')
        
        source = "BCB+API" if (to_curr == 'BRL' or from_curr == 'BRL') else "API"
        
        response = f"SUCESSO|{from_curr}|{to_curr}|{amount:.2f}|{result:.2f}|{rate:.6f}|{update_time}|{source}"
        return response
        
    except ValueError:
        return "ERRO: Valor inválido"
    except Exception as e:
        return f"ERRO: {str(e)}"

# Função que trata cada cliente em uma thread separada
# Permite múltiplas conexões simultâneas
# Primeiro incrementa o contador de clientes ativos
# Depois processa a mensagem recebida e envia a resposta
# Finalmente decrementa o contador de clientes ativos ao desconectar
def handle_client(connectionSocket, addr, client_id):
    
    global active_clients
    
    with clients_lock:
        active_clients += 1
    
    print(f'\n[CONECTADO] Cliente #{client_id} - {addr[0]}:{addr[1]}')
    print(f'[INFO] Clientes ativos: {active_clients}')
    
    try:
        message = connectionSocket.recv(1024).decode()
        
        if not message:
            print(f'[AVISO] Cliente #{client_id} enviou mensagem vazia')
            return
        
        print(f'[RECEBIDO] Cliente #{client_id}: {message}')
        
        response = convert_currency(message)
        print(f'[ENVIANDO] Cliente #{client_id}: {response.split("|")[0]}')
        
        connectionSocket.send(response.encode())
        
    except Exception as e:
        print(f'[ERRO] Cliente #{client_id}: {e}')
        try:
            error_msg = f"ERRO: {str(e)}"
            connectionSocket.send(error_msg.encode())
        except:
            pass
    
    finally:
        connectionSocket.close()
        
        with clients_lock:
            active_clients -= 1
        
        print(f'[DESCONECTADO] Cliente #{client_id} - {addr[0]}:{addr[1]}')
        print(f'[INFO] Clientes ativos: {active_clients}')

serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind(('', serverPort))
serverSocket.listen(10)  # Até 10 conexões na fila

print('=' * 70)
print('💱 SERVIDOR CONVERSOR - MULTI-THREAD (BCB + API)')
print('=' * 70)
print(f'📡 Porta: {serverPort}')
print(f'🔧 Modo: Multi-thread (suporta múltiplos clientes)')
print('⏳ Carregando taxas iniciais...')

initial_rates, _ = get_exchange_rates()

print(f'✅ {len(initial_rates)} moedas carregadas')
print('🌍 Principais: USD, BRL, EUR, GBP, JPY, CAD, AUD, CHF, CNY, ARS')
print(f'💾 Cache: {rates_cache["cache_duration"]} segundos')
print('👂 Aguardando conexões...')
print('=' * 70)

try:
    while True:
        
        connectionSocket, addr = serverSocket.accept()
        
        client_counter += 1
        current_client_id = client_counter
        
        client_thread = threading.Thread(
            target=handle_client,
            args=(connectionSocket, addr, current_client_id),
            daemon=True
        )
        
        client_thread.start()
        
        print(f'[THREAD] Thread iniciada para Cliente #{current_client_id}')

except KeyboardInterrupt:
    print('\n\n[SERVIDOR] Encerrando servidor...')
    print(f'[INFO] Total de clientes atendidos: {client_counter}')
    serverSocket.close()
    print('[SERVIDOR] Servidor encerrado com sucesso')
except Exception as e:
    print(f'\n[ERRO FATAL] {e}')
    serverSocket.close()