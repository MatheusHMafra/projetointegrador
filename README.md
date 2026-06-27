# GEP - Sistema de Gerenciamento de Estoque

## 📋 Sobre o Projeto

Trabalho de Conclusão de Curso (TCC) apresentado ao curso de Sistemas para Internet da UNIVALI - Universidade do Vale do Itajaí, como requisito parcial para obtenção de grau de Tecnólogo em Sistemas para Internet.

**Orientador(a):** Antonio Carlos Silva

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
git clone https://github.com/[seu-usuario]/projetointegrador.git
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

## 📝 Credenciais de Acesso (Desenvolvimento)

| Perfil | E-mail | Senha |
|--------|--------|-------|
| Admin | `admin@gep.com` | admin123 |
| Gerente | `gerente@gep.com` | gerente123 |
| Operador | `operador@gep.com` | operador123 |

## 📄 Licença

Projeto acadêmico - UNIVALI.
