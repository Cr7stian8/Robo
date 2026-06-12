# 🤖 Automação AVA-EFAPE com Playwright

Automatiza o acesso e a interação com a plataforma AVA-EFAPE, incluindo:

- Login automático
- Navegação entre cursos
- Execução de aulas e vídeos
- Resolução de modais (perguntas, diagnósticos, pesquisas etc.)

---

## 📦 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- Python 3.7 ou superior
- Pip (gerenciador de pacotes do Python)
- Git (opcional, para clonar o repositório)

---

## 🐍 Ambiente Virtual (Recomendado)

Utilizar um ambiente virtual ajuda a evitar conflitos de dependências com outros projetos.

### Linux / macOS

```bash
# Cria o ambiente virtual (pasta "venv")
python3 -m venv venv

# Ativa o ambiente
source venv/bin/activate
```

### Windows (CMD ou PowerShell)

```cmd
python -m venv venv
venv\Scripts\activate
```

Após a ativação, o terminal exibirá `(venv)` no início da linha, indicando que o ambiente virtual está ativo.

---

## ⚙️ Instalação

### 1. Clone ou baixe o projeto

```bash
git clone <url-do-repositorio>
cd nome-da-pasta
```

### 2. Instale as dependências

Com o ambiente virtual ativo:

```bash
pip install playwright
```

### 3. Instale os navegadores do Playwright

```bash
playwright install
```

---

## ▶️ Como Executar

Com o ambiente virtual ativo, execute o script principal:

```bash
python nome_do_arquivo.py
```

Substitua `nome_do_arquivo.py` pelo nome real do arquivo.

No Linux, caso não esteja utilizando ambiente virtual, utilize:

```bash
python3 nome_do_arquivo.py
```

---

## 📊 Logs

Durante a execução, o terminal exibe mensagens de status:

| Símbolo | Significado |
|----------|-------------|
| ✅ | Sucesso |
| ❌ | Erro |
| ⚠️ | Aviso |
| 📚 | Progresso |

---

## 📌 Observações

- As credenciais de acesso devem estar configuradas corretamente no código.
- O Playwright pode ser executado em modo **headless** (sem interface gráfica), dependendo da configuração do script.
- Recomenda-se manter as dependências atualizadas para garantir compatibilidade com a plataforma.

---

## 🛠️ Tecnologias Utilizadas

- Python
- Playwright

---

## 📄 Licença

Este projeto é disponibilizado para fins educacionais e de automação. Verifique as políticas de uso da plataforma antes de utilizá-lo.
