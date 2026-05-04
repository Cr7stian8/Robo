# 🤖 Automação AVA-EFAPE com Playwright

Este projeto automatiza o acesso e a interação com a plataforma AVA-EFAPE:

* Login automático
* Navegação entre cursos
* Execução de aulas/vídeos
* Resolução de modais (perguntas, diagnósticos, pesquisas, etc.)

## 📦 Pré-requisitos

Antes de rodar o projeto, você precisa ter instalado:

* Python
* `pip` (gerenciador de pacotes do Python)

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

## 📊 Logs

O sistema exibe logs coloridos no terminal:

* ✅ Sucesso
* ❌ Erro
* ⚠️ Aviso
* 📚 Progresso
