# GEP - Sistema de Gerenciamento de Estoque de Papelarias

## 📋 Sobre o Projeto

O GEP é um sistema web completo para gerenciamento de estoque. O sistema permite o controle de produtos, categorias, fornecedores e movimentações de estoque em uma interface intuitiva e moderna.

## ✨ Funcionalidades

- **Dashboard**: Visão geral do estoque com estatísticas e gráficos
- **Produtos**: Cadastro, edição, exclusão e busca de produtos
- **Categorias**: Organização de produtos por categorias
- **Fornecedores**: Gerenciamento completo de fornecedores
- **Estoque**: Controle de entrada, saída e ajuste de produtos
- **Relatórios**: Geração de relatórios de vendas, produtos mais/menos vendidos
- **Tema Dark/Light**: Interface adaptável com suporte a temas claro e escuro

## 🔧 Tecnologias Utilizadas

- **Backend**: Python com Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Banco de Dados**: SQLite3
- **Libs**: Bootstrap 5, Axios, Chart.js, FontAwesome
- **Arquitetura**: MVC (Model-View-Controller)

## 📦 Requisitos

- Python 3.9+
- Pip (Gerenciador de pacotes do Python)
- SQLite3
- Navegador moderno (Chrome, Firefox, Edge, Safari)

## 🚀 Instalação e Configuração

### 1. Clonar o Repositório

```bash
git clone https://github.com/MatheusHMafra/projetointegrador.git
cd projetointegrador
```

### 2. Configurar Ambiente Virtual

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Executar a Aplicação

```bash
python app.py
```

O sistema estará disponível em `http://localhost:5000`

## 🏗️ Estrutura do Projeto

```txt
projetointegrador/
├── app/                  # Diretório principal da aplicação Flask
│   ├── __init__.py       # Inicialização da aplicação
│   ├── models.py         # Modelos do banco de dados (SQLAlchemy/SQLite)
│   ├── routes.py         # Definição das rotas/views
│   ├── forms.py          # Formulários (WTForms)
│   └── static/           # Arquivos estáticos (CSS, JS, Imagens)
│       ├── css/
│       ├── js/
│       └── img/
│   └── templates/        # Templates HTML (Jinja2)
│       ├── base.html
│       ├── auth/
│       ├── dashboard/
│       ├── products/
│       └── ...
├── migrations/           # Migrações do banco de dados (se usar Flask-Migrate)
├── tests/                # Testes unitários/integração
├── .venv/                # Ambiente virtual Python
├── config.py             # Configurações da aplicação
├── requirements.txt      # Dependências Python
├── run.py                # Script para iniciar a aplicação (opcional)
└── README.md             # Este arquivo
```
