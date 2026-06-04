# 🦊 FOX Intruder Payload Generator

![Burp Suite](https://img.shields.io/badge/Burp_Suite-Enabled-orange?style=for-the-badge&logo=portswigger&logoColor=white)
![Language](https://img.shields.io/badge/Language-Jython_2.7-blue?style=for-the-badge&logo=python&logoColor=white)
![Focus](https://img.shields.io/badge/Focus-Fuzzing_%26_Exploitation-red?style=for-the-badge)

O **FOX Intruder Payload Generator** é uma extensão modular em Python (Jython) desenvolvida para o ecossistema do **Burp Suite**. O objetivo central do projeto é estender nativamente o componente *Burp Intruder*, implementando um motor de fuzzing mutacional semi-aleatório (`IIntruderPayloadGenerator`) para testes de intrusão, descoberta de vulnerabilidades em aplicações web e bypass de Web Application Firewalls (WAF).

A ferramenta opera interceptando dinamicamente o vetor de ataque original (*Base Value*) e aplicando algoritmos de mutação em pontos flutuantes (*offsets*) da string para identificar falhas de injeção, quebras de lógica e estouros de buffer.

---

## 🛠️ Engenharia de Mutação e Algoritmos

A engine de fuzzing adota um comportamento estocástico através de uma roleta de decisão (`random.randint(1, 3)`), injetando anomalias em um índice de deslocamento dinâmico calculado com base no tamanho do payload original.

* **Mutação Tipo 1: Injeção de Aspas Simples (`'`)**
    * *Foco:* Quebra de sintaxe em queries SQL (SQL Injection), quebra de delimitadores de strings em backends e indução de erros de banco de dados estruturados.
* **Mutação Tipo 2: Injeção de Tag Cross-Site Scripting (XSS)**
    * *Foco:* Injeção do vetor clássico de auditoria `<script>alert('BHP!');</script>` para validação de falta de sanitização/escaping no front-end.
* **Mutação Tipo 3: Replicação de Chunk (*Fuzzing de Stress*)**
    * *Foco:* Extração de um pedaço aleatório do conteúdo original e multiplicação desse segmento de forma iterativa (`repeater`). Ideal para testar falhas de estouro de buffer (*Buffer Overflow*), Denial of Service local (DoS) e exaustão de memória no tratamento de inputs.

---

## 🧬 Anatomia do Bug: Análise Comparativa e Refatoração

O repositório documenta a evolução da ferramenta a partir de um protótipo inicial instável até a consolidação da versão estável (**V.1**). Abaixo estão os problemas críticos de arquitetura identificados e mitigados:

### 1. Divisão Destrutiva de Strings (Fatiamento)
* **Como estava:** `front, back = original_payload[:offset], original_payload[:offset]`
    * *Impacto:* Erro grave de lógica. Ambas as variáveis recebiam a primeira metade da string. A metade posterior (`[offset:]`) era sumariamente descartada, destruindo a integridade do payload base.
* **Correção (V.1):** `front = original_payload[:offset]` e `back = original_payload[offset:]`

### 2. Operador Incorreto de Atribuição
* **Como estava:** `front =+ "'"`
    * *Impacto:* Erro de sintaxe lógica. O interpretador avalia isso como uma reatribuição da variável para o caractere positivo, falhando em concatenar a string.
* **Correção (V.1):** `front += "'"`

### 3. Variáveis Globais Fantasmas (Unbound Variables)
* **Como estava:** O bloco da mutação 3 tentava iterar sobre a variável `repeater`, que nunca havia sido declarada ou inicializada no escopo do método.
* **Correção (V.1):** Declaração explícita de `repeater = random.randint(1, 4)` e proteção do tamanho do bloco via `chunk_length = random.randint(1, max(1, len(back)))`.

### 4. Marshalling de Tipos (Java Byte Array vs Python String)
* **Como estava:** `payload = "".join(chr(x) for x in current_payload)` (onde `current_payload` nem existia no escopo). O Burp Suite envia dados brutos da requisição HTTP como um array de bytes assinalados do Java (`byte[]`). No Python/Jython, tentar ler diretamente valores negativos gera exceções de estouro de faixa.
* **Correção (V.1):** Implementação de mascaramento de bits:
    ```python
    payload_str = "".join(chr(x & 0xFF) for x in baseValue)
    ```
    Isso força a conversão segura dos bytes do Java (faixa -128 a 127) para a tabela ASCII adequada (0 a 255) consumível pelo Python.

---

## 📊 Arquitetura do Código


```

IntruderPayloadGenerator V.1.py
├── BurpExtender (IBurpExtender, IIntruderPayloadGeneratorFactory)
│    ├── registerExtenderCallbacks -> Inicializa e registra a factory no Burp
│    └── createNewInstance -> Instancia a engine para cada nova thread do Intruder
└── BHPFuzzer (IIntruderPayloadGenerator)
├── hasMorePayloads -> Controla o teto de iterações (Default: 10)
├── getNextPayload -> Captura o input do Java, normaliza e invoca a mutação
├── mutate_payload -> Aplica a lógica randômica de injeção/fuzzing
└── reset -> Reseta os contadores para reutilização da instância

```

---

## 🚀 Instalação e Deployment Prático

### Requisitos Locais
1. **Burp Suite** (Community, Professional ou Enterprise).
2. **Jython Standalone JAR** (Recomendado: 2.7.3 ou superior).

### Configuração no Burp Suite
1. Mova-se até a aba **Extensions** -> **Options** -> Subseção **Python Environment**.
2. No campo **Select file...**, selecione o seu arquivo `.jar` do Jython Standalone.
3. Alterne para a aba **Installed** e clique em **Add**.
4. Configure os campos:
   * **Extension Type:** `Python`
   * **Extension file:** Selecione o arquivo `IntruderPayloadGenerator V.1.py`.
5. Avance. Se o log de saída (*Output*) estiver limpo, a extensão registrou com sucesso o componente `BHP Payload Generator Modificado`.

### Executando o Fuzzing
1. Intercepte ou envie uma requisição HTTP alvo para o **Intruder**.
2. Defina os marcadores de posição (`§`) no parâmetro que deseja auditar.
3. Na aba **Payloads**:
   * Altere a opção **Payload type** para `Extension-generated`.
   * No menu inferior, selecione `BHP Payload Generator Modificado`.
4. Clique em **Start Attack**.

---

## 🛡️ Cenário de Teste Prático

Suponha que o parâmetro alvo original seja `id=admin`. A extensão poderá gerar saídas mutadas dinamicamente como:

| Iteração | Tipo de Mutação Aplicada | Payload Resultante | Alvo Provável |
| :--- | :--- | :--- | :--- |
| 1 | Injeção de Aspas | `ad'min` | SQL Injection / Erro de Parsing |
| 2 | Injeção de Script | `admin<script>alert('BHP!');</script>` | Reflected XSS |
| 3 | Replicação de Chunk | `adminadminmin` | Falha de Lógica de Buffer / Tamanho |
| 4 | Injeção de Aspas | `admin'` | SQL Injection |

---

## 📝 Customização Adicional

Caso queira expandir o teto de testes massivos, altere o seguinte parâmetro dentro do método `__init__` da classe `BHPFuzzer`:

```python
self.max_payloads = 1000  # Modifique para a quantidade de mutações desejadas por parâmetro

```

---

**Disclaimer:** Esta ferramenta foi desenvolvida com mentalidade ética e foco em pesquisa de vulnerabilidades (*Vulnerability Research*). O uso deste software contra alvos sem autorização prévia por escrito é estritamente ilegal. O desenvolvedor não se responsabiliza por danos causados pelo uso indevido da ferramenta.

```

---

Dessa forma, o projeto deixa de parecer apenas um script de exercício e passa a se posicionar como uma ferramenta de automação e engenharia reversa de código. O que achou dessa roupagem?

```
