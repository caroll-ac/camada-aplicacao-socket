import socket
import json
import time
from threading import Thread
from concurrent.futures import ThreadPoolExecutor


# ============================
# Servidor
# ============================
class ServidorAtendimento:
    def __init__(self, endereco_servidor="0.0.0.0", porta_servidor=3214, max_conexoes=1):
        # criação do socket e configuração
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((endereco_servidor, porta_servidor))
        self.socket.listen(max_conexoes)
        print(f"Servidor escutando em {endereco_servidor}:{porta_servidor}")

        # Registro de thread para atendimento e registros de usuários
        self.threadClientes = {}
        
        # Simbolo da moeda, valor -> quanto 1 BRL compra dessa moeda
        self.listaMoedas = {
            "USD": 0.18,
            "EUR": 0.16,
            "GBP": 0.13,
            "JPY": 28.50,
            "AUD": 0.27,
            "CAD": 0.24,
            "CHF": 0.16,
            "CNY": 1.27,
            "ARS": 32.50,
        }

        # Inicia uma thread dedicada para escuta de novas conexões
        self.threadEscuta = Thread(target=self.implementacaoThreadEscuta, daemon=True)
        self.threadEscuta.start()

    def handlerDeMensagem(self, mensagem):
        """Processa mensagens recebidas e retorna resposta"""
        if mensagem.get("AÇÃO") == "LISTAR MOEDAS":
            return {"MOEDAS": self.listaMoedas}
        else:
            return {"ERRO": "AÇÃO desconhecida"}

    def implementacaoThreadCliente(self, enderecoDoCliente, socketParaCliente):
        """Atendimento a um cliente conectado"""
        print(f"Cliente {enderecoDoCliente} conectado.")
        socketParaCliente.settimeout(10)

        while True:
            try:
                mensagem = socketParaCliente.recv(512)
            except socket.timeout:
                print(f"Cliente {enderecoDoCliente} inativo. Encerrando conexão.")
                socketParaCliente.close()
                break
            except Exception as e:
                print(f"Erro com o cliente {enderecoDoCliente}: {e}")
                break

            if not mensagem:
                break

            try:
                mensagem_decodificada = json.loads(mensagem.decode("utf-8"))
                print(f"Servidor recebeu: {mensagem_decodificada}")

                resposta = self.handlerDeMensagem(mensagem_decodificada)
                resposta_bytes = json.dumps(resposta).encode("utf-8")

                socketParaCliente.send(resposta_bytes)
                print(f"Servidor enviou: {resposta}")
            except Exception as e:
                print(f"Erro ao processar mensagem: {e}")
                break

        print(f"Conexão encerrada com {enderecoDoCliente}")
        socketParaCliente.close()

    def implementacaoThreadEscuta(self):
        """Thread principal que aceita conexões"""
        while True:
            try:
                socketParaCliente, enderecoDoCliente = self.socket.accept()
            except OSError:
                print("Servidor: socket fechado, encerrando escuta.")
                break

            thread = Thread(
                target=self.implementacaoThreadCliente,
                args=(enderecoDoCliente, socketParaCliente),
                daemon=True,
            )
            self.threadClientes[enderecoDoCliente] = thread
            thread.start()


# ============================
# Cliente
# ============================
def cliente():
    socket_cliente_thread = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    nome_servidor = socket.gethostname()
    ip_servidor = socket.gethostbyname_ex(nome_servidor)
    print("Cliente tentando conectar em:", ip_servidor[2][0])

    # espera o servidor iniciar
    time.sleep(2)

    socket_cliente_thread.connect((ip_servidor[2][0], 3214))
    print("Cliente conectado ao servidor.")

    mensagens = [{"AÇÃO": "LISTAR MOEDAS"}]

    for mensagem in mensagens:
        mensagem_bytes = json.dumps(mensagem).encode("utf-8")
        socket_cliente_thread.send(mensagem_bytes)
        msg = socket_cliente_thread.recv(4096)
        print("Cliente recebeu:", json.loads(msg.decode("utf-8")))

    socket_cliente_thread.close()
    print("Cliente finalizado.")


# ============================
# Execução principal
# ============================
if __name__ == "__main__":
    # Cria e inicia o cliente em thread paralela
    threadPool = ThreadPoolExecutor()
    threadPool.submit(cliente)

    # Cria o servidor
    servidor = ServidorAtendimento()

    # Aguarda (só pra manter vivo enquanto roda o teste)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Encerrando servidor...")
        servidor.socket.close()