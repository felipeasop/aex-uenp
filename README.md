# 🧶 Lua e Flor · Ateliê de Amigurumis

Sistema web para catálogo, controle de encomendas artesanais, fluxo de compras e fila de produção da **Loja Lua e Flor**, desenvolvido em **Python** e **Django** com banco de dados **PostgreSQL**.

---

## 📋 Pré-requisitos Globais

Antes de iniciar, certifique-se de ter instalado no seu sistema operacional:

1. **Python 3.10 ou superior** (com `pip` e suporte a `venv`):
   - **Linux (Debian/Ubuntu):**
     ```bash
     sudo apt update
     sudo apt install python3 python3-pip python3-venv libpq-dev
     ```
   - **Windows:** Baixe o instalador oficial em [python.org](https://www.python.org/) (marque a opção *"Add Python to PATH"*).

2. **PostgreSQL** (servidor e utilitários de linha de comando):
   - **Linux (Debian/Ubuntu):**
     ```bash
     sudo apt install postgresql postgresql-contrib
     sudo systemctl enable --now postgresql
     ```
   - **Windows:** Baixe e instale pelo instalador oficial do [postgresql.org](https://www.postgresql.org/download/windows/).

---

## 🐘 1. Configurando o Banco de Dados (PostgreSQL)

O sistema espera por padrão as credenciais abaixo (definidas em `config/settings.py`, via `DATABASE_URL`):
- **Nome do Banco:** `luaeflor`
- **Usuário:** `luaeflor`
- **Senha:** `luaeflor`
- **Host / Porta:** `localhost` / `5432`

Para criar o usuário e o banco de dados no PostgreSQL via terminal:

### No Linux:
```bash
# Entrar no prompt do PostgreSQL como superusuário postgres
sudo -u postgres psql
```

Dentro do `psql`, execute:
```sql
CREATE DATABASE luaeflor;
CREATE USER luaeflor WITH PASSWORD 'luaeflor';
ALTER ROLE luaeflor SET client_encoding TO 'utf8';
ALTER ROLE luaeflor SET default_transaction_isolation TO 'read committed';
ALTER ROLE luaeflor SET timezone TO 'America/Sao_Paulo';
GRANT ALL PRIVILEGES ON DATABASE luaeflor TO luaeflor;
ALTER DATABASE luaeflor OWNER TO luaeflor;
\q
```

*(Opcional: caso utilize credenciais diferentes, defina a variável de ambiente `DATABASE_URL` antes de rodar os comandos do Django.)*

```bash
# Linux / macOS
export DATABASE_URL=postgresql://usuario:senha@localhost:5432/nome_do_banco
```
```powershell
# Windows (PowerShell)
$env:DATABASE_URL="postgresql://usuario:senha@localhost:5432/nome_do_banco"
```

---

## 💻 2. Clonando e Preparando o Ambiente Virtual (venv)

1. **Clone o repositório e acesse a pasta do projeto:**
   ```bash
   git clone https://github.com/felipeasop/aex-uenp.git
   cd aex-uenp
   ```

2. **Crie o ambiente virtual (`venv`):**
   ```bash
   python -m venv venv
   ```

3. **Ative o ambiente virtual:**
   - **Linux / macOS:**
     ```bash
     source venv/bin/activate
     ```
   - **Windows (PowerShell):**
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows (Prompt de Comando - CMD):**
     ```cmd
     .\venv\Scripts\activate.bat
     ```

4. **Instale as dependências do projeto:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🗄️ 3. Migrações e População Inicial do Banco

Com o PostgreSQL ativo e a `venv` habilitada:

1. **Gere as tabelas no banco de dados:**
   ```bash
   python manage.py migrate
   ```

2. **Popule o banco com dados de teste e usuários iniciais:**
   O script `populate_db.py` cadastra tags, tipos de produtos, fofurinhos com fotos, ciclo de encomendas, cupom de desconto e contas de acesso:
   ```bash
   python populate_db.py
   ```

---

## 👥 Contas Cadastradas para Testes

O script `populate_db.py` cria automaticamente as seguintes contas:

| Tipo | Usuário / Login | Senha | Acesso / Papel |
| :--- | :--- | :--- | :--- |
| **Administrador** | `admin` | `admin123` | Acesso total ao Django Admin e painel da loja |
| **Operador** | `operador` | `operador123` | Permissão para cadastrar fofurinhos e gerenciar catálogo |
| **Cliente** | `cliente@exemplo.com` | `cliente123` | Simulação de compras, encomendas e favoritos |

---

## 🚀 4. Executando o Servidor de Desenvolvimento

Inicie o servidor do Django:

```bash
python manage.py runserver 0.0.0.0:8000
```

### Onde Acessar:
- **Acesso local na máquina:**
  👉 **`http://localhost:8000/`** ou **`http://127.0.0.1:8000/`**
- **Painel Administrativo do Django:**
  👉 **`http://localhost:8000/admin/`**
- **Acesso via rede local (outros computadores/celulares na mesma rede):**
  👉 **`http://<SEU-IP-LOCAL>:8000/`**  
  *(Exemplo: `http://192.168.1.15:8000/`)*

> **Dica para descobrir seu IP local:**  
> - No Linux: `ip addr` ou `hostname -I`  
> - No Windows: `ipconfig`

---

## 🛠️ Problemas Comuns

- **`connection failed ... banco de dados "..." não existe` / `password authentication failed`:** o banco ou o usuário do PostgreSQL não foram criados como no passo 1, ou as credenciais são diferentes. Crie-os ou defina a `DATABASE_URL` correta.
- **Windows: `UnicodeDecodeError: 'utf-8' codec can't decode byte ...` em `base.py`:** acontecia com o driver antigo (`psycopg2`) quando o PostgreSQL em português recusava a conexão; a mensagem real ficava escondida. O projeto agora usa o `psycopg` 3, que mostra o erro corretamente. Se ainda aparecer, apague a `venv`, recrie-a e rode `pip install -r requirements.txt` de novo.

---

## 📁 Estrutura dos Módulos da Aplicação

- **`apps/catalogo/`**: Gerencia produtos (fofurinhos), tags, coleções, fotos e o controle de capacidade do `CicloEncomenda`.
- **`apps/vendas/`**: Controla o carrinho de compras, checkout, cupons, pedidos e a `FilaProducao`.
- **`apps/usuarios/`**: Gerencia perfis de usuários (`Cliente`, `Operador`, `Administrador`).
- **`templates/`** e **`static/`**: Interface web responsiva com visualização em modal dinâmico e filtros interativos.

---

## ☁️ Deploy (produção)

O script `build.sh` instala as dependências, coleta os arquivos estáticos (servidos pelo WhiteNoise) e aplica as migrações. No serviço de hospedagem, configure as variáveis de ambiente:

| Variável | Valor |
| :--- | :--- |
| `DATABASE_URL` | URL de conexão do PostgreSQL de produção |
| `DEBUG` | `False` (no Render já é o padrão) |

---

Feito com 🧶 e carinho para a **Lua e Flor**.
