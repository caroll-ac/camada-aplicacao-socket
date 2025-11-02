import argparse
import os
from socket import socket, AF_INET, SOCK_STREAM
import sys


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


def build_message(from_curr: str, to_curr: str, amount: float) -> str:
    # mantém o formato esperado pelo servidor: FROM|TO|AMOUNT
    return f"{from_curr}|{to_curr}|{amount:.2f}"


def main():
    # Carrega variáveis do arquivo .env (se existir) para encapsular o IP/PORT
    def load_dotenv(path='.env'):
        try:
            if not os.path.exists(path):
                return
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        k, v = line.split('=', 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k and v and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

    load_dotenv()

    parser = argparse.ArgumentParser(description='Cliente conversor de moedas')
    parser.add_argument('server', nargs='?', default=os.environ.get('SERVER', '127.0.0.1'),
                        help='IP do servidor (padrão: 127.0.0.1 ou definido em .env)')
    parser.add_argument('--port', '-p', type=int, default=int(os.environ.get('PORT', '6000')),
                        help='Porta do servidor (padrão: 6000 ou definido em .env)')

    args = parser.parse_args()

    serverName = args.server
    serverPort = args.port

    print('=' * 60)
    print('💱 CLIENTE CONVERSOR DE MOEDAS')
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

        # perguntas separadas
        print('Preencha os dados da conversão:')
        from_curr = prompt_currency('  Moeda origem (ex: USD): ')
        to_curr = prompt_currency('  Moeda destino (ex: BRL): ')
        amount = prompt_amount('  Valor (ex: 100.00): ')

        message = build_message(from_curr, to_curr, amount)

        print('\n⏳ Enviando requisição...')
        clientSocket.send(message.encode())

        response = clientSocket.recv(4096).decode()

        print('\n' + '=' * 60)
        print('📊 RESULTADO DA CONVERSÃO')
        print('=' * 60)

        parts = response.split('|')

        if parts[0] == 'SUCESSO':
            from_curr = parts[1]
            to_curr = parts[2]
            amount = float(parts[3])
            result = float(parts[4])
            rate = float(parts[5])

            print(f'\n  De:        {from_curr}')
            print(f'  Valor:     {amount:.2f}')
            print(f'\n  Para:      {to_curr}')
            print(f'  Resultado: {result:.2f}')
            print(f'\n  Taxa:      1 {from_curr} = {rate:.6f} {to_curr}')
        else:
            print(f'\n❌ {response}')

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
