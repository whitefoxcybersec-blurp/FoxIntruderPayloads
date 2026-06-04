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
* **Correção (V.1):** Declaração explícita de
