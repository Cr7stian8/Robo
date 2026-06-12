🤖 Automação AVA-EFAPE com Playwright
Automatiza o acesso e a interação com a plataforma AVA-EFAPE: login, navegação entre cursos, execução de aulas/vídeos e resolução de modais (perguntas, diagnósticos, pesquisas, etc.).

📦 Pré-requisitos
Python 3.7 ou superior

pip (gerenciador de pacotes do Python)

Git (opcional, para clonar o repositório)

🐍 Ambiente virtual (recomendado)
Isolar as dependências evita conflitos com outros projetos.

Linux / macOS
bash
# Cria o ambiente virtual (pasta "venv")
python3 -m venv venv

# Ativa o ambiente
source venv/bin/activate
Windows (CMD/PowerShell)
cmd
python -m venv venv
venv\Scripts\activate
Após a ativação, o terminal mostrará (venv) no início da linha – isso confirma que o ambiente está ativo.

⚙️ Instalação
Clone ou baixe o projeto

bash
git clone <url-do-repositorio>
cd nome-da-pasta
Instale as dependências (com o ambiente virtual ativo)

bash
pip install playwright
Instale os navegadores do Playwright

bash
playwright install
▶️ Como executar
Com o ambiente virtual ativo, execute o script principal:

bash
python nome_do_arquivo.py
Substitua nome_do_arquivo.py pelo nome real do seu arquivo.
Se estiver no Linux sem o ambiente virtual, use python3.

📊 Logs
Durante a execução, o terminal exibe mensagens coloridas:

✅ Sucesso

❌ Erro

⚠️ Aviso

📚 Progresso

📌 Observações
As credenciais de acesso devem estar configuradas corretamente no código.

O Playwright pode rodar em modo headless (sem interface gráfica) dependendo da configuração do script.
