import socket
import json
import time
from threading import Thread
from concurrent.futures import ThreadPoolExecutor


# ============================
# Servidor
# ============================
class ServidorAtendimento:
    def __init__(self, endereco_servidor="0.0.0.0", porta_servidor=3214, max_conexoes=5):
        # Criação do socket e configuração
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((endereco_servidor, porta_servidor))
        self.socket.listen(max_conexoes)
        print(f"Servidor escutando em {endereco_servidor}:{porta_servidor}")

        self.threadClientes = {}
        self.listaMoedas = {
            "USD": 0.18, "EUR": 0.16, "GBP": 0.13, "JPY": 28.50,
            "AUD": 0.27, "CAD": 0.24, "CHF": 0.16, "CNY": 1.27, "ARS": 32.50,
        }

        # Thread dedicada à escuta
        self.threadEscuta = Thread(target=self.implementacaoThreadEscuta, daemon=True)
        self.threadEscuta.start()

    def handlerDeMensagem(self, mensagem):

        acao = mensagem.get("AÇÃO")

        if acao == "LISTAR":
            return {"MOEDAS": self.listaMoedas}
        elif acao == "CONSULTAR":
            if mensagem.get("MOEDA") in self.listaMoedas.keys():
                return {"COTAÇÃO": self.listaMoedas.get(mensagem.get("MOEDA"))}
        elif acao == "CONVERTER":
            moeda = mensagem.get("MOEDA")
            valor = mensagem.get("VALOR", 1.0)
            taxa = self.listaMoedas.get(moeda)
            if taxa:
                return {"VALOR_CONVERTIDO": valor * taxa}
            else:
                return {"ERRO": f"Moeda '{moeda}' não encontrada."}
        else:
            return {"ERRO": "AÇÃO desconhecida"}

    def implementacaoThreadCliente(self, enderecoDoCliente, socketParaCliente):
        """Atendimento a um cliente conectado"""
        print(f"Cliente {enderecoDoCliente} conectado.")
        socketParaCliente.settimeout(30)

        while True:
            try:
                mensagem = socketParaCliente.recv(512)
            except socket.timeout:
                print(f"Cliente {enderecoDoCliente} inativo. Encerrando conexão.")
                break
            except Exception as e:
                print(f"Erro com o cliente {enderecoDoCliente}: {e}")
                break

            if not mensagem:
                break

            try:
                mensagem_decodificada = json.loads(mensagem.decode("utf-8"))
                print(f"Recebido de {enderecoDoCliente}: {mensagem_decodificada}")

                resposta = self.handlerDeMensagem(mensagem_decodificada)
                socketParaCliente.send(json.dumps(resposta).encode("utf-8"))
                print(f"Enviado para {enderecoDoCliente}: {resposta}")
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
def cliente(id_cliente, mensagem):
    time.sleep(1)  # aguarda servidor iniciar
    socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    nome_servidor = socket.gethostname()
    ip_servidor = socket.gethostbyname(nome_servidor)
    socket_cliente.connect((ip_servidor, 3214))

    print(f"Cliente {id_cliente} conectado ao servidor {ip_servidor}:3214")

    socket_cliente.send(json.dumps(mensagem).encode("utf-8"))

    resposta = socket_cliente.recv(4096)
    print(f"Cliente {id_cliente} recebeu:", json.loads(resposta.decode("utf-8")))

    socket_cliente.close()
    print(f"Cliente {id_cliente} finalizado.")


# ============================
# Execução principal
# ============================
if __name__ == "__main__":
    servidor = ServidorAtendimento()

    mensagens = [
        {"AÇÃO": "LISTAR"},
        {"AÇÃO": "CONSULTAR", "MOEDA": "USD"},
        {"AÇÃO": "CONVERTER", "MOEDA": "EUR", "VALOR": 50},
        {"AÇÃO": "CONVERTER", "MOEDA": "JPY", "VALOR": 2000},
        {"AÇÃO": "CONSULTAR", "MOEDA": "ARS"},
    ]

    # Cria um cliente para cada mensagem
    with ThreadPoolExecutor() as pool:
        for i, msg in enumerate(mensagens):
            pool.submit(cliente, i, msg)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Encerrando servidor...")
        servidor.socket.close()
