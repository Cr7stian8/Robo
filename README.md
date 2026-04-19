# 🤖 Automação AVA-EFAPE com Playwright

Este projeto automatiza o acesso e a interação com a plataforma AVA-EFAPE, incluindo:

* Login automático
* Navegação entre cursos
* Execução de aulas/vídeos
* Resolução de modais (perguntas, diagnósticos, pesquisas, etc.)
* Salvamento de screenshots para debug

---

## 📦 Pré-requisitos

Antes de rodar o projeto, você precisa ter instalado:

* Python **3.9 ou superior**
* `pip` (gerenciador de pacotes do Python)

---

## ⚙️ Instalação

### 1. Clone ou baixe o projeto

```bash
git clone <seu-repositorio>
cd <pasta-do-projeto>
```

### 2. Instale as dependências

```bash
pip install playwright
```

### 3. Instale os navegadores do Playwright

```bash
playwright install
```

---

## ▶️ Como rodar

### 🪟 Windows

No Prompt de Comando (CMD) ou PowerShell:

```bash
python nome_do_arquivo.py
```

Se tiver múltiplas versões do Python:

```bash
python3 nome_do_arquivo.py
```

---

### 🐧 Linux

No terminal:

```bash
python3 nome_do_arquivo.py
```

Se necessário, dê permissão:

```bash
chmod +x nome_do_arquivo.py
```

---

## 🔐 Configuração

No início do código, configure suas credenciais:

```python
CPF = "SEU_CPF"
SENHA = "SUA_SENHA"
```

⚠️ **Importante:** Evite subir suas credenciais para repositórios públicos.

---

## 🧠 Como funciona

O fluxo principal:

1. Inicia o navegador
2. Faz login na plataforma
3. Acessa "Meus Cursos"
4. Identifica cursos pendentes
5. Para cada curso:

   * Abre aulas não concluídas
   * Reproduz vídeos automaticamente
   * Detecta e resolve modais
6. Marca cursos como concluídos
7. Remove cursos da visualização

---

## 🪟 Tratamento de Modais

O sistema detecta automaticamente o tipo de modal:

* Pergunta (quiz)
* Diagnóstico
* Plano de aula
* Pesquisa
* Reflexão
* Popup genérico

### 🔁 Lógica de fallback

* Se o mesmo modal aparecer **3 vezes**, pode indicar:

  * Travamento
  * Identificação incorreta do tipo

Então o sistema:

1. Tenta resolver como outro tipo de modal
2. Se repetir 3 vezes novamente:

   * Testa todos os tipos possíveis
3. Se voltar ao tipo inicial e falhar:

   * Exibe mensagem de erro
   * Solicita reinício do script
   * Salva screenshot em `/debug`

---

## 🐞 Debug

* Screenshots são salvos automaticamente na pasta:

```
/debug
```

* Ativado por:

```python
SALVAR_SCREENSHOTS = True
```

---

## ⏱️ Configurações importantes

```python
TEMPO_MAXIMO_VIDEO = 300000  # tempo máximo por vídeo
TEMPO_MINIMO_VIDEO = 30      # tempo mínimo antes de validar conclusão
```

---

## 📊 Logs

O sistema exibe logs coloridos no terminal:

* ✅ Sucesso
* ❌ Erro
* ⚠️ Aviso
* 📚 Progresso

---

## 🛑 Interromper execução

Você pode parar a automação a qualquer momento com:

```
CTRL + C
```

---

## 📌 Observações

* O navegador abre em modo **não-headless** (visível)
* Pode ser necessário ajustar seletores caso o site mude
* Ideal rodar em ambiente estável (evitar travamentos do sistema)

---

## 🚀 Execução

Basta rodar:

```bash
python nome_do_arquivo.py
```

E o bot fará todo o processo automaticamente.

---

Se quiser, posso melhorar esse README com:

* `.env` para credenciais (mais seguro)
* Docker
* Logs em arquivo
* Interface simples (GUI)

Só falar 👍
