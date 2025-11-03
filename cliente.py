import argparse
from socket import socket, AF_INET, SOCK_STREAM
import sys
import struct

def valid_currency(code: str) -> str:
    code = code.strip().upper()
    if len(code) != 3 or not code.isalpha():
        raise ValueError('Código de moeda deve ter 3 letras (ex: USD, BRL)')
    return code

def prompt_currency(prompt_text: str) -> str:
    while True:
        try:
            val = input(prompt_text).strip()
            return valid_currency(val)
        except ValueError as e:
            print(f'Entrada inválida: {e}')

def prompt_amount(prompt_text: str) -> float:
    while True:
        val = input(prompt_text).strip().replace(',', '.')
        try:
            amount = float(val)
            if amount <= 0:
                print('O valor deve ser maior que zero')
                continue
            return amount
        except ValueError:
            print('Valor inválido. Use um número, ex: 100 ou 12.50')

def build_binary_message(from_curr: str, to_curr: str, amount: float) -> bytes:
    """
    Formato binário compacto (10 bytes):
    - 3 bytes: moeda origem (ASCII)
    - 3 bytes: moeda destino (ASCII)
    - 4 bytes: valor (float IEEE 754, big-endian)
    """
    message = from_curr.encode('ascii')  # 3 bytes
    message += to_curr.encode('ascii')   # 3 bytes
    message += struct.pack('>f', amount) # 4 bytes (big-endian float)
    return message

def main():
    parser = argparse.ArgumentParser(description='Cliente conversor de moedas')
    parser.add_argument('server', nargs='?', default='192.168.1.65',
                        help='IP do servidor (padrão: 127.0.0.1)')
    parser.add_argument('--port', '-p', type=int, default=6000,
                        help='Porta do servidor (padrão: 6000)')
    args = parser.parse_args()
    
    serverName = args.server
    serverPort = args.port
    
    print('=' * 60)
    print('💱 CLIENTE CONVERSOR DE MOEDAS (FORMATO BINÁRIO)')
    print('=' * 60)
    print(f'Conectando a {serverName}:{serverPort}...')
    
    clientSocket = socket(AF_INET, SOCK_STREAM)
    
    try:
        clientSocket.connect((serverName, serverPort))
        print('✅ Conectado ao servidor!\n')
        
        print('MOEDAS DISPONÍVEIS (exemplos):')
        print('  USD - Dólar Americano')
        print('  BRL - Real Brasileiro')
        print('  EUR - Euro')
        print('  GBP - Libra Esterlina')
        print('  JPY - Iene Japonês')
        print()
        
        print('Preencha os dados da conversão:')
        from_curr = prompt_currency('  Moeda origem (ex: USD): ')
        to_curr = prompt_currency('  Moeda destino (ex: BRL): ')
        amount = prompt_amount('  Valor (ex: 100.00): ')
        
        message = build_binary_message(from_curr, to_curr, amount)
        
        print(f'\n⏳ Enviando requisição ({len(message)} bytes)...')
        clientSocket.send(message)
        
        # Recebe resposta (8 bytes se sucesso, texto se erro)
        response = clientSocket.recv(1024)
        
        print('\n' + '=' * 60)
        print('📊 RESULTADO DA CONVERSÃO')
        print('=' * 60)
        
        # Verifica se é resposta binária (8 bytes) ou erro (texto)
        if len(response) == 8:
            # Desempacota dois floats: resultado e taxa
            result, rate = struct.unpack('>ff', response)
            
            print(f'\n  De:        {from_curr}')
            print(f'  Valor:     {amount:.2f}')
            print(f'\n  Para:      {to_curr}')
            print(f'  Resultado: {result:.2f}')
            print(f'\n  Taxa:      1 {from_curr} = {rate:.6f} {to_curr}')
        else:
            # Resposta de erro em texto
            error_msg = response.decode()
            print(f'\n❌ {error_msg}')
        
        print('\n' + '=' * 60)
        
    except ConnectionRefusedError:
        print('❌ Erro: Não foi possível conectar ao servidor')
        print('   Verifique se o servidor está rodando e o IP/porta estão corretos')
        sys.exit(1)
    except Exception as e:
        print(f'❌ Erro: {e}')
        sys.exit(1)
    finally:
        try:
            clientSocket.close()
        except:
            pass
        print('\n👋 Desconectado')

if __name__ == '__main__':
    main()