from socket import *

serverName = '192.168.1.21' # IP da rede local
serverPort = 6000

print('=' * 60)
print('💱 CLIENTE CONVERSOR DE MOEDAS')
print('=' * 60)
print(f'Conectando a {serverName}:{serverPort}...')

clientSocket = socket(AF_INET, SOCK_STREAM)

try:

    clientSocket.connect((serverName, serverPort))
    print('✅ Conectado ao servidor!\n')
    
    print('MOEDAS DISPONÍVEIS:')
    print('  USD - Dólar Americano')
    print('  BRL - Real Brasileiro')
    print('  EUR - Euro')
    print('  GBP - Libra Esterlina')
    print('  JPY - Iene Japonês')
    print()
    print('FORMATO: FROM|TO|AMOUNT')
    print('Exemplo: USD|BRL|100')
    print('=' * 60)
    
    print('\n📝 Digite a conversão:')
    message = input('> ')
    
    print('\n⏳ Enviando requisição...')
    clientSocket.send(message.encode())
    
    response = clientSocket.recv(1024).decode()
    
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
        print(f'\n  Taxa:      1 {from_curr} = {rate:.4f} {to_curr}')
        
    else:
        print(f'\n❌ {response}')
    
    print('\n' + '=' * 60)
    
except ConnectionRefusedError:
    print('❌ Erro: Não foi possível conectar ao servidor')
    print('   Verifique se o servidor está rodando')
except Exception as e:
    print(f'❌ Erro: {e}')
finally:
    clientSocket.close()
    print('\n👋 Desconectado')
