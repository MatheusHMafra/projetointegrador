import sqlite3
from database_utils import get_db

# Instruções SQL para criar as tabelas
SQL_CREATE_USUARIO = """
CREATE TABLE IF NOT EXISTS usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha_hash TEXT NOT NULL,
    nivel_acesso TEXT NOT NULL, -- 'admin', 'gerente', 'operador'
    manager_id INTEGER,          -- ID do gerente que criou este usuário (para hierarquia)
    ativo INTEGER DEFAULT 1,    -- 1 para True, 0 para False
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_acesso TIMESTAMP,
    FOREIGN KEY (manager_id) REFERENCES usuario (id)
);
"""

SQL_CREATE_CATEGORIA = """
CREATE TABLE IF NOT EXISTS categoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL,
    descricao TEXT,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SQL_CREATE_FORNECEDOR = """
CREATE TABLE IF NOT EXISTS fornecedores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cnpj TEXT UNIQUE,
    email TEXT,
    telefone TEXT,
    endereco TEXT,
    contato TEXT,
    observacoes TEXT,
    ativo INTEGER DEFAULT 1,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultima_atualizacao TIMESTAMP -- 'onupdate' precisa ser tratado na aplicação
);
"""

SQL_CREATE_PRODUTO = """
CREATE TABLE IF NOT EXISTS produto (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE, -- Índice será criado separadamente
    nome TEXT NOT NULL,
    descricao TEXT,
    categoria_id INTEGER NOT NULL,
    preco REAL NOT NULL,
    preco_compra REAL,
    estoque INTEGER NOT NULL DEFAULT 0,
    estoque_minimo INTEGER DEFAULT 5,
    ativo INTEGER DEFAULT 1,
    imagem_url TEXT,
    fornecedor_id INTEGER,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultima_atualizacao TIMESTAMP, -- 'onupdate' precisa ser tratado na aplicação
    FOREIGN KEY (categoria_id) REFERENCES categoria (id),
    FOREIGN KEY (fornecedor_id) REFERENCES fornecedores (id)
);
"""
SQL_CREATE_INDEX_PRODUTO_CODIGO = """
CREATE INDEX IF NOT EXISTS idx_produto_codigo ON produto(codigo);
"""

SQL_CREATE_ESTOQUE_MOVIMENTACAO = """
CREATE TABLE IF NOT EXISTS estoque_movimentacao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_id INTEGER NOT NULL,
    usuario_id INTEGER,
    venda_id INTEGER,
    tipo TEXT NOT NULL, -- 'entrada', 'saida', 'ajuste', 'venda'
    quantidade INTEGER NOT NULL,
    estoque_anterior INTEGER NOT NULL,
    estoque_atual INTEGER NOT NULL,
    observacao TEXT,
    data_movimento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (produto_id) REFERENCES produto (id),
    FOREIGN KEY (usuario_id) REFERENCES usuario (id),
    FOREIGN KEY (venda_id) REFERENCES venda (id)
);
"""

SQL_CREATE_GRUPO_PRODUTO = """
CREATE TABLE IF NOT EXISTS grupo_produto (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    descricao TEXT,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Tabela de associação para a relação muitos-para-muitos entre Produto e GrupoProduto
SQL_CREATE_PRODUTOS_GRUPOS = """
CREATE TABLE IF NOT EXISTS produtos_grupos (
    produto_id INTEGER NOT NULL,
    grupo_id INTEGER NOT NULL,
    PRIMARY KEY (produto_id, grupo_id),
    FOREIGN KEY (produto_id) REFERENCES produto (id),
    FOREIGN KEY (grupo_id) REFERENCES grupo_produto (id)
);
"""

SQL_CREATE_VENDA = """
CREATE TABLE IF NOT EXISTS venda (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE, -- Índice será criado separadamente
    data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_id INTEGER,
    cliente_nome TEXT,
    valor_total REAL DEFAULT 0.0,
    desconto REAL DEFAULT 0.0,
    valor_final REAL DEFAULT 0.0,
    forma_pagamento TEXT,
    observacao TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuario (id)
);
"""
SQL_CREATE_INDEX_VENDA_CODIGO = """
CREATE INDEX IF NOT EXISTS idx_venda_codigo ON venda(codigo);
"""

SQL_CREATE_ITEM_VENDA = """
CREATE TABLE IF NOT EXISTS item_venda (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venda_id INTEGER NOT NULL,
    produto_id INTEGER NOT NULL,
    quantidade INTEGER NOT NULL DEFAULT 1,
    preco_unitario REAL NOT NULL,
    subtotal REAL NOT NULL, -- Calculado na aplicação antes de inserir
    FOREIGN KEY (venda_id) REFERENCES venda (id) ON DELETE CASCADE, -- Adicionado ON DELETE CASCADE como no ORM
    FOREIGN KEY (produto_id) REFERENCES produto (id)
);
"""


# Função para inicializar o banco de dados com sqlite3
def init_db_sqlite():
    """
    Conecta ao banco de dados e cria as tabelas se elas não existirem.
    """
    db_conn = None  # Inicializa a variável de conexão
    try:
        # 1. Obter a conexão com o banco de dados
        db_conn = get_db()  # Sua função que retorna a conexão sqlite3
        cursor = db_conn.cursor()

        # 2. Habilitar suporte a chaves estrangeiras (importante no SQLite)
        cursor.execute("PRAGMA foreign_keys = ON;")

        # 3. Executar os comandos CREATE TABLE e CREATE INDEX
        print("Criando tabela usuario...")
        cursor.execute(SQL_CREATE_USUARIO)
        print("Criando tabela categoria...")
        cursor.execute(SQL_CREATE_CATEGORIA)
        print("Criando tabela fornecedor...")
        cursor.execute(
            SQL_CREATE_FORNECEDOR
        )  # Usa a constante que agora cria 'fornecedores'
        print("Criando tabela produto...")
        cursor.execute(
            SQL_CREATE_PRODUTO
        )  # Usa a constante que agora referencia 'fornecedores'

        # Migração leve para bases antigas sem coluna de status em produto.
        cursor.execute("PRAGMA table_info(produto)")
        produto_cols = [row[1] for row in cursor.fetchall()]
        if "ativo" not in produto_cols:
            print("Adicionando coluna ativo em produto...")
            cursor.execute(
                "ALTER TABLE produto ADD COLUMN ativo INTEGER DEFAULT 1"
            )
            cursor.execute("UPDATE produto SET ativo = 1 WHERE ativo IS NULL")

        print("Criando índice em produto.codigo...")
        cursor.execute(SQL_CREATE_INDEX_PRODUTO_CODIGO)
        print("Criando tabela estoque_movimentacao...")
        cursor.execute(
            SQL_CREATE_ESTOQUE_MOVIMENTACAO
        )  # Usa a constante com o nome corrigido

        # Migração leve para bases antigas sem vínculo opcional com venda.
        cursor.execute("PRAGMA table_info(estoque_movimentacao)")
        estoque_mov_cols = [row[1] for row in cursor.fetchall()]
        if "venda_id" not in estoque_mov_cols:
            print("Adicionando coluna venda_id em estoque_movimentacao...")
            cursor.execute(
                "ALTER TABLE estoque_movimentacao ADD COLUMN venda_id INTEGER"
            )

        print("Criando tabela grupo_produto...")
        cursor.execute(SQL_CREATE_GRUPO_PRODUTO)
        print("Criando tabela produtos_grupos...")
        cursor.execute(SQL_CREATE_PRODUTOS_GRUPOS)
        print("Criando tabela venda...")
        cursor.execute(SQL_CREATE_VENDA)
        print("Criando índice em venda.codigo...")
        cursor.execute(SQL_CREATE_INDEX_VENDA_CODIGO)
        print("Criando tabela item_venda...")
        cursor.execute(SQL_CREATE_ITEM_VENDA)

        # 4. Confirmar as alterações (commit)
        db_conn.commit()
        print("Banco de dados inicializado com sucesso!")

    except sqlite3.Error as e:
        print(f"Erro ao inicializar o banco de dados: {e}")
        # Opcional: fazer rollback em caso de erro
        if db_conn:
            db_conn.rollback()
    finally:
        # 5. Fechar a conexão (se get_db não gerencia isso)
        if db_conn:
            db_conn.close()
            print("Conexão com o banco de dados fechada.")
