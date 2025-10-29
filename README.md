# camada-aplicacao-socket


# 💱 Servidor e Cliente de Conversão de Moedas Multi-Thread

Este projeto implementa um servidor TCP multi-thread para conversão de moedas. Ele utiliza um sistema de cache, busca as taxas de câmbio através de uma API externa (ExchangeRate-API) e integra as cotações oficiais do Banco Central do Brasil (BCB) para BRL, USD e EUR.

## ⚙️ Requisitos

Para executar o servidor e o cliente, você precisa ter o Python instalado e as seguintes bibliotecas:

1.  **`requests`**: Para fazer chamadas HTTP às APIs de taxa de câmbio.

### Instalação de Dependências

```bash
pip install requests
```

## 🚀 Como Executar

O projeto é dividido em duas partes: o Servidor (`servidor.py`) e o Cliente (`cliente.py`). Eles devem ser executados em terminais separados e, idealmente, em máquinas diferentes na mesma rede para testar a comunicação.

### 1\. Iniciar o Servidor

O servidor deve ser executado primeiro. Ele inicializará o socket, carregará as taxas iniciais (com cache de 1 hora) e começará a escutar na porta `6000`.

**Comando:**

```bash
python servidor.py
```

**Saída Esperada (Início):**

```
======================================================================
💱 SERVIDOR CONVERSOR - MULTI-THREAD (BCB + API)
======================================================================
📡 Porta: 6000
🔧 Modo: Multi-thread (suporta múltiplos clientes)
⏳ Carregando taxas iniciais...
[BCB] USD: 5.4012 BRL
[BCB] EUR: 5.7890 BRL
[BCB] ✅ Usando cotação oficial do Banco Central para BRL
[API] ✅ 162 moedas disponíveis
✅ 162 moedas carregadas
🌍 Principais: USD, BRL, EUR, GBP, JPY, CAD, AUD, CHF, CNY, ARS
💾 Cache: 3600 segundos
👂 Aguardando conexões...
======================================================================
```

### 2\. Iniciar o Cliente

O cliente estabelece a conexão com o IP do servidor na porta `6000`.

#### Configuração de Acesso (Importante\!)

Antes de executar, você deve configurar a variável `serverName` no arquivo `cliente.py`:

```python
# cliente.py

# Mude este IP para o endereço IP local (LAN) do computador que está rodando o servidor.
serverName = '192.168.1.21' 
serverPort = 6000
```

**Comando:**

```bash
python cliente.py
```

## 💬 Protocolo de Comunicação

O cliente e o servidor se comunicam usando um formato de mensagem simples:

### Requisição do Cliente

O cliente envia uma única string no formato:

```
<MOEDA_ORIGEM>|<MOEDA_DESTINO>|<VALOR>
```

**Exemplo:** `USD|BRL|100`

### Resposta do Servidor

O servidor retorna uma string de resposta que começa com `SUCESSO` ou `ERRO`.

#### 1\. Resposta de Sucesso

```
SUCESSO|<moeda_origem>|<moeda_destino>|<valor_enviado>|<resultado_calculado>|<taxa_usada>|<data_atualizacao>|<fonte>
```

**Exemplo de Saída no Cliente:**

```
📝 Digite a conversão:
> EUR|JPY|50

⏳ Enviando requisição...

============================================================
📊 RESULTADO DA CONVERSÃO
============================================================

  De:        EUR
  Valor:     50.00

  Para:      JPY
  Resultado: 8185.76

  Taxa:      1 EUR = 163.7152 JPY

============================================================
```

#### 2\. Resposta de Erro

```
ERRO: <mensagem_detalhada_do_erro>
```

**Exemplo:**

```
❌ ERRO: Moeda XYZ não suportada
```

## 🔑 Funcionalidades Chave do Servidor

  * **Multi-Threading:** Permite que o servidor atenda vários clientes simultaneamente usando threads.
  * **Cache de Taxas:** As taxas são buscadas nas APIs a cada 1 hora (`cache_duration = 3600` segundos) para reduzir a latência e a carga da API.
  * **Fontes de Dados Híbridas:**
      * **BCB (Banco Central do Brasil):** Usado para obter a cotação oficial de Dólar e Euro em relação ao Real, garantindo maior precisão para operações envolvendo BRL.
      * **ExchangeRate-API:** Usada como fonte principal de taxas de USD para o resto do mundo.
      * **Fallback:** Se as APIs falharem, um conjunto de taxas de fallback é usado para garantir que o serviço não pare.
