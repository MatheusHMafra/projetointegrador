"""
Utilitários para operações de banco de dados
Versão compatível com Python 3.13
"""
import logging
import datetime
from flask import current_app
from werkzeug.security import generate_password_hash
import sqlite3
import os

logger = logging.getLogger(__name__)


def get_db():
    """Obtém uma conexão com o banco de dados"""
    conn = sqlite3.connect(database='estoque.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
    return conn


def init_db():
    """Inicializa o banco de dados com o esquema definido"""
    conn = get_db()
    cursor = conn.cursor()

    # Criar tabelas
    with current_app.open_resource('schema.sql') as f:
        conn.executescript(f.read().decode('utf8'))

    conn.commit()
    logger.info("Banco de dados inicializado com sucesso")


def criar_tabelas():
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Tabela Usuário
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT UNIQUE,
                senha_hash TEXT,
                nivel_acesso TEXT,
                ativo BOOLEAN DEFAULT 1,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabela Categoria
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                descricao TEXT,
                ativo BOOLEAN DEFAULT 1,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabela Fornecedores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fornecedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                cnpj TEXT UNIQUE,
                email TEXT,
                telefone TEXT,
                endereco TEXT,
                contato TEXT,
                observacoes TEXT,
                ativo BOOLEAN DEFAULT 1,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabela Produto (garantir que a chave estrangeira para fornecedor existe)
        # Se a tabela produto já existe, pode ser necessário um ALTER TABLE ou recriá-la
        # Aqui, assumimos que ela será criada *depois* ou já contém a coluna
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS produto (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE,
                nome TEXT NOT NULL,
                descricao TEXT,
                preco REAL NOT NULL,
                preco_compra REAL,
                estoque INTEGER DEFAULT 0,
                estoque_minimo INTEGER DEFAULT 0,
                imagem_url TEXT,
                categoria_id INTEGER,
                fornecedor_id INTEGER, -- Adicionado/Confirmado
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (categoria_id) REFERENCES categoria (id),
                FOREIGN KEY (fornecedor_id) REFERENCES fornecedores (id) -- Chave estrangeira
            )
        """)

        # Tabela Estoque_Movimentacao
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS estoque_movimentacao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto_id INTEGER,
                tipo TEXT CHECK(tipo IN ('entrada', 'saida')),
                quantidade INTEGER,
                usuario_id INTEGER,
                observacao TEXT,
                data_movimento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (produto_id) REFERENCES produto (id),
                FOREIGN KEY (usuario_id) REFERENCES usuario (id)
            )
        """)

        # Tabela Venda
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS venda (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE,
                usuario_id INTEGER,
                cliente_nome TEXT,
                desconto REAL DEFAULT 0,
                forma_pagamento TEXT,
                observacao TEXT,
                data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                valor_total REAL,
                valor_final REAL,
                FOREIGN KEY (usuario_id) REFERENCES usuario (id)
            )
        """)

        # Tabela Venda_Item
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS venda_item (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venda_id INTEGER,
                produto_id INTEGER,
                quantidade INTEGER,
                preco_unitario REAL,
                subtotal REAL,
                FOREIGN KEY (venda_id) REFERENCES venda (id),
                FOREIGN KEY (produto_id) REFERENCES produto (id)
            )
        """)

        conn.commit()
        print("Tabelas verificadas/criadas com sucesso.")
    except sqlite3.Error as e:
        print(f"Erro ao criar/verificar tabelas: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def inicializar_dados_exemplo():
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Verificar se já existem usuários para evitar duplicação
        cursor.execute("SELECT COUNT(*) FROM usuario")
        if cursor.fetchone()[0] == 0:
            print("Inserindo dados de exemplo...")
            # Inserir usuários padrão
            senha_hash1 = generate_password_hash("admin123")
            cursor.execute(
                "INSERT INTO usuario (nome, email, senha_hash, nivel_acesso) VALUES (?, ?, ?, ?)",
                ("Administrador", "admin@sistema.com", senha_hash1, "admin")
            )
            senha_hash2 = generate_password_hash("vendedor123")
            cursor.execute(
                "INSERT INTO usuario (nome, email, senha_hash, nivel_acesso) VALUES (?, ?, ?, ?)",
                ("Vendedor", "vendedor@sistema.com", senha_hash2, "vendedor")
            )

            # Inserir categorias padrão
            categorias = [
                ("Eletrônicos", "Produtos eletrônicos em geral"),
                ("Informática", "Equipamentos e peças para computadores"),
                ("Celulares", "Smartphones e acessórios"),
                ("Acessórios", "Acessórios em geral")
            ]
            cursor.executemany(
                "INSERT INTO categoria (nome, descricao) VALUES (?, ?)",
                categorias
            )

            # Inserir fornecedores padrão
            fornecedores = [
                ("Distribuidora Alfa", "11.222.333/0001-44", "contato@alfa.com", "11 9999-8888", "Rua Principal, 10", "João Silva", "Entrega rápida", 1),
                ("Componentes Beta", "44.555.666/0001-77", "vendas@beta.com", "21 8888-7777", "Avenida Central, 20", "Ana Costa", "Peças de qualidade", 1),
                ("Importados Gama", "77.888.999/0001-00", "import@gama.com", "31 7777-6666", "Praça da Matriz, 30", "Carlos Lima", None, 0), # Inativo
                ("Eletrônicos SA", "98.765.432/0001-21", "contato@eletronicos.com", "11 9888-7777", "Avenida Industrial, 200", "Maria Oliveira", "Bom prazo de entrega", 1),
                ("InfoTech", "54.321.678/0001-55", "vendas@infotech.com", "48 9777-6666", "Travessa do Comércio, 300", "Carlos Pereira", "Preços competitivos", 1)
            ]
            cursor.executemany("""
                INSERT INTO fornecedores (nome, cnpj, email, telefone, endereco, contato, observacoes, ativo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, fornecedores)

            # Inserir produtos de exemplo (ajustar para incluir fornecedor_id)
            # Exemplo: (codigo, nome, desc, preco, preco_compra, estoque, est_min, cat_id, forn_id)
            produtos = [
                ('LP001', 'Laptop Pro', 'Laptop de alta performance', 5500.00, 4800.00, 15, 5, 1, 1), # Cat: Eletrônicos, Forn: Alfa
                ('SM002', 'Smartphone X', 'Smartphone com câmera avançada', 3200.00, 2800.00, 25, 10, 1, 2), # Cat: Eletrônicos, Forn: Beta
                ('KB003', 'Teclado Mecânico', 'Teclado para gamers', 350.00, 280.00, 50, 15, 2, 1), # Cat: Acessórios, Forn: Alfa
                ('MS004', 'Mouse Gamer', 'Mouse óptico RGB', 150.00, 110.00, 60, 20, 2, 4), # Cat: Acessórios, Forn: Eletrônicos SA
                ('HD005', 'HD Externo 1TB', 'Disco rígido portátil USB 3.0', 250.00, 200.00, 30, 10, 3, 5), # Cat: Armazenamento, Forn: InfoTech
                ('SSD006', 'SSD 500GB', 'SSD SATA III rápido', 400.00, 350.00, 40, 10, 3, 5), # Cat: Armazenamento, Forn: InfoTech
                ('MN007', 'Monitor 24" LED', 'Monitor Full HD', 800.00, 700.00, 10, 3, 1, 4), # Cat: Eletrônicos, Forn: Eletrônicos SA
            ]
            cursor.executemany("""
                INSERT INTO produto (codigo, nome, descricao, preco, preco_compra, estoque, estoque_minimo, categoria_id, fornecedor_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, produtos)

            conn.commit()
            print("Dados de exemplo inseridos.")
        else:
            print("Banco de dados já contém dados. Nenhuma inserção realizada.")

    except sqlite3.Error as e:
        print(f"Erro ao inicializar dados de exemplo: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def obter_estatisticas():
    """
    Retorna estatísticas gerais do sistema para o dashboard
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        resultado = {}

        # Total de produtos
        cursor.execute("SELECT COUNT(*) FROM produto")
        resultado['total_produtos'] = cursor.fetchone()[0]

        # Total de categorias
        cursor.execute("SELECT COUNT(*) FROM categoria")
        resultado['total_categorias'] = cursor.fetchone()[0]

        # Total de fornecedores
        cursor.execute("SELECT COUNT(*) FROM fornecedor")
        resultado['total_fornecedores'] = cursor.fetchone()[0]

        # Total em estoque (quantidade)
        cursor.execute("SELECT SUM(estoque) FROM produto")
        resultado['total_estoque'] = cursor.fetchone()[0] or 0

        # Valor total em estoque
        cursor.execute("SELECT SUM(estoque * preco_compra) FROM produto")
        resultado['valor_estoque'] = cursor.fetchone()[0] or 0

        # Produtos com estoque baixo
        cursor.execute(
            "SELECT COUNT(*) FROM produto WHERE estoque <= estoque_minimo")
        resultado['produtos_estoque_baixo'] = cursor.fetchone()[0]

        # Movimentações de estoque nos últimos 30 dias
        trinta_dias_atras = datetime.datetime.now() - datetime.timedelta(days=30)
        cursor.execute(
            "SELECT COUNT(*) FROM movimento_estoque WHERE data_movimento >= ?",
            (trinta_dias_atras,)
        )
        resultado['movimentacoes_ultimos_30_dias'] = cursor.fetchone()[0]

        # Vendas nos últimos 30 dias
        cursor.execute(
            "SELECT COUNT(*), COALESCE(SUM(valor_final), 0) FROM venda WHERE data_venda >= ?",
            (trinta_dias_atras,)
        )
        venda_dados = cursor.fetchone()
        resultado['vendas_ultimos_30_dias'] = venda_dados[0]
        resultado['valor_vendas_ultimos_30_dias'] = venda_dados[1] or 0

        # Produtos mais vendidos
        cursor.execute(
            """
            SELECT p.id, p.nome, SUM(iv.quantidade) as total_vendido
            FROM produto p
            JOIN item_venda iv ON p.id = iv.produto_id
            JOIN venda v ON iv.venda_id = v.id
            WHERE v.data_venda >= ?
            GROUP BY p.id
            ORDER BY total_vendido DESC
            LIMIT 5
            """,
            (trinta_dias_atras,)
        )
        resultado['produtos_mais_vendidos'] = []
        for row in cursor.fetchall():
            resultado['produtos_mais_vendidos'].append({
                'id': row[0],
                'nome': row[1],
                'total_vendido': row[2]
            })

        # Movimentações recentes
        cursor.execute(
            """
            SELECT me.id, p.nome as produto_nome, me.tipo, me.quantidade, me.data_movimento
            FROM movimento_estoque me
            JOIN produto p ON me.produto_id = p.id
            ORDER BY me.data_movimento DESC
            LIMIT 10
            """
        )
        resultado['movimentacoes_recentes'] = []
        for row in cursor.fetchall():
            movimento = {}
            for idx, col in enumerate(cursor.description):
                if col[0] == 'data_movimento' and row[idx] is not None:
                    movimento[col[0]] = row[idx].strftime(
                        '%Y-%m-%d %H:%M:%S') if isinstance(row[idx], datetime.datetime) else row[idx]
                else:
                    movimento[col[0]] = row[idx]
            resultado['movimentacoes_recentes'].append(movimento)

        return resultado

    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {str(e)}")
        return {
            'error': str(e),
            'total_produtos': 0,
            'total_categorias': 0,
            'total_fornecedores': 0,
            'total_estoque': 0,
            'valor_estoque': 0,
            'produtos_estoque_baixo': 0,
            'movimentacoes_ultimos_30_dias': 0,
            'vendas_ultimos_30_dias': 0,
            'valor_vendas_ultimos_30_dias': 0,
            'produtos_mais_vendidos': [],
            'movimentacoes_recentes': []
        }


def registrar_movimento(produto_id, tipo, quantidade, usuario_id=None, observacao=None):
    """
    Registra um movimento de estoque e atualiza o estoque do produto

    Args:
        produto_id (int): ID do produto
        tipo (str): 'entrada' ou 'saida'
        quantidade (int): Quantidade a ser movimentada
        usuario_id (int, opcional): ID do usuário que está fazendo a movimentação
        observacao (str, opcional): Observação sobre a movimentação

    Returns:
        dict: Informações sobre o movimento realizado
    """
    try:
        if tipo not in ['entrada', 'saida']:
            raise ValueError(
                "Tipo de movimento inválido. Use 'entrada' ou 'saida'")

        if quantidade <= 0:
            raise ValueError("Quantidade deve ser maior que zero")

        conn = get_db()
        cursor = conn.cursor()

        # Buscar produto e estoque atual
        cursor.execute(
            "SELECT id, nome, estoque FROM produto WHERE id = ?", (produto_id,))
        produto = cursor.fetchone()

        if not produto:
            raise ValueError(f"Produto com ID {produto_id} não encontrado")

        estoque_anterior = produto[2]

        # Calcular novo estoque
        if tipo == 'entrada':
            estoque_novo = estoque_anterior + quantidade
        else:  # saída
            if estoque_anterior < quantidade:
                raise ValueError(
                    f"Estoque insuficiente. Disponível: {estoque_anterior}, Solicitado: {quantidade}")
            estoque_novo = estoque_anterior - quantidade

        # Atualizar estoque do produto
        cursor.execute(
            "UPDATE produto SET estoque = ? WHERE id = ?",
            (estoque_novo, produto_id)
        )

        # Registrar movimento
        cursor.execute(
            """
            INSERT INTO movimento_estoque
            (produto_id, usuario_id, tipo, quantidade, estoque_anterior, estoque_atual, observacao)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (produto_id, usuario_id, tipo, quantidade,
             estoque_anterior, estoque_novo, observacao)
        )

        movimento_id = cursor.lastrowid

        # Confirmar transação
        conn.commit()

        logger.info(
            f"Movimento de estoque registrado: {tipo} de {quantidade} unidades do produto {produto[1]}")

        return {
            'id': movimento_id,
            'produto_id': produto_id,
            'produto_nome': produto[1],
            'tipo': tipo,
            'quantidade': quantidade,
            'estoque_anterior': estoque_anterior,
            'estoque_atual': estoque_novo,
            'usuario_id': usuario_id,
            'observacao': observacao,
            'data_movimento': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    except Exception as e:
        conn.rollback() if 'conn' in locals() else None
        logger.error(f"Erro ao registrar movimento de estoque: {str(e)}")
        raise


def buscar_produtos(query=None, categoria=None, fornecedor=None, estoque_baixo=False, page=1, per_page=10):
    """
    Busca produtos com base em diferentes filtros

    Args:
        query (str, opcional): Busca por nome ou descrição
        categoria (int, opcional): ID da categoria
        fornecedor (int, opcional): ID do fornecedor
        estoque_baixo (bool): Se True, filtra produtos com estoque <= estoque_minimo
        page (int): Número da página
        per_page (int): Itens por página

    Returns:
        dict: Contém os produtos encontrados e informações de paginação
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Construir a query base
        base_query = """
        SELECT 
            p.id, 
            p.nome, 
            p.descricao, 
            p.preco, 
            p.preco_compra,
            p.estoque, 
            p.estoque_minimo,
            p.categoria_id, 
            c.nome as categoria_nome,
            p.fornecedor_id,
            f.nome as fornecedor_nome
        FROM 
            produto p
        JOIN 
            categoria c ON p.categoria_id = c.id
        JOIN 
            fornecedor f ON p.fornecedor_id = f.id
        WHERE 
            1=1
        """

        params = []

        # Adicionar filtros
        if query:
            base_query += " AND (p.nome LIKE ? OR p.descricao LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])

        if categoria:
            base_query += " AND p.categoria_id = ?"
            params.append(categoria)

        if fornecedor:
            base_query += " AND p.fornecedor_id = ?"
            params.append(fornecedor)

        if estoque_baixo:
            base_query += " AND p.estoque <= p.estoque_minimo"

        # Query para contar total de registros
        count_query = "SELECT COUNT(*) FROM (" + base_query + ")"
        cursor.execute(count_query, params)
        total_items = cursor.fetchone()[0]

        # Adicionar ordenação e paginação
        base_query += " ORDER BY p.nome"
        base_query += " LIMIT ? OFFSET ?"
        offset = (page - 1) * per_page
        params.extend([per_page, offset])

        # Executar query final
        cursor.execute(base_query, params)

        # Processar resultados
        produtos = []
        for row in cursor.fetchall():
            produto = {}
            for idx, col in enumerate(cursor.description):
                produto[col[0]] = row[idx]

            # Adicionar status de estoque
            produto['estoque_status'] = 'baixo' if produto['estoque'] <= produto['estoque_minimo'] else 'normal'
            produtos.append(produto)

        # Calcular páginas
        total_pages = (total_items + per_page -
                       1) // per_page  # Arredonda para cima

        return {
            'produtos': produtos,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_items': total_items,
                'total_pages': total_pages
            }
        }

    except Exception as e:
        logger.error(f"Erro ao buscar produtos: {str(e)}")
        return {
            'error': str(e),
            'produtos': [],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_items': 0,
                'total_pages': 0
            }
        }


def obter_dados_movimentacao(produto_id=None, tipo=None, data_inicio=None, data_fim=None, usuario_id=None, page=1, per_page=20):
    """
    Obtém dados de movimentação de estoque com diferentes filtros

    Args:
        produto_id (int, opcional): Filtrar por ID do produto
        tipo (str, opcional): Tipo de movimentação ('entrada' ou 'saida')
        data_inicio (str, opcional): Data de início no formato 'YYYY-MM-DD'
        data_fim (str, opcional): Data de fim no formato 'YYYY-MM-DD'
        usuario_id (int, opcional): Filtrar por ID do usuário
        page (int): Número da página (padrão: 1)
        per_page (int): Itens por página (padrão: 20)

    Returns:
        dict: Contém os movimentos encontrados e informações de paginação
    """
    conn = get_db()
    cursor = conn.cursor()

    # Construir a consulta
    sql_query = """
        SELECT m.*, p.nome as produto_nome, p.codigo as produto_codigo, u.nome as usuario_nome
        FROM movimento_estoque m
        LEFT JOIN produto p ON m.produto_id = p.id
        LEFT JOIN usuario u ON m.usuario_id = u.id
        WHERE 1=1
    """
    params = []

    # Adicionar filtros
    if produto_id:
        sql_query += " AND m.produto_id = ?"
        params.append(produto_id)

    if tipo:
        sql_query += " AND m.tipo = ?"
        params.append(tipo.lower())

    if data_inicio:
        sql_query += " AND m.data_movimento >= ?"
        # Converter string para datetime se necessário
        if isinstance(data_inicio, str):
            try:
                data_inicio = datetime.datetime.strptime(
                    data_inicio, '%Y-%m-%d')
            except ValueError:
                pass
        params.append(data_inicio)

    if data_fim:
        sql_query += " AND m.data_movimento <= ?"
        # Converter string para datetime se necessário
        if isinstance(data_fim, str):
            try:
                data_fim = datetime.datetime.strptime(data_fim, '%Y-%m-%d')
                # Ajustar para final do dia
                data_fim = data_fim.replace(hour=23, minute=59, second=59)
            except ValueError:
                pass
        params.append(data_fim)

    if usuario_id:
        sql_query += " AND m.usuario_id = ?"
        params.append(usuario_id)

    # Contar total para paginação
    count_query = """
        SELECT COUNT(*) FROM movimento_estoque m
        WHERE 1=1
    """
    count_params = params.copy()

    # Adicionar mesmos filtros na consulta de contagem
    if produto_id:
        count_query += " AND m.produto_id = ?"
    if tipo:
        count_query += " AND m.tipo = ?"
    if data_inicio:
        count_query += " AND m.data_movimento >= ?"
    if data_fim:
        count_query += " AND m.data_movimento <= ?"
    if usuario_id:
        count_query += " AND m.usuario_id = ?"

    # Adicionar ordenação e paginação
    sql_query += " ORDER BY m.data_movimento DESC LIMIT ? OFFSET ?"
    params.append(per_page)
    params.append((page - 1) * per_page)

    # Executar as consultas
    cursor.execute(count_query, count_params)
    total = cursor.fetchone()[0]

    cursor.execute(sql_query, params)
    movimentos = cursor.fetchall()

    # Formatar os resultados
    resultado = []
    for m in movimentos:
        movimento_dict = {}
        for idx, col in enumerate(cursor.description):
            movimento_dict[col[0]] = m[idx]
        resultado.append(movimento_dict)

    # Formatar a resposta
    return {
        "movimentos": resultado,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page  # Arredondar para cima
    }


def adicionar_venda(cliente_nome, itens, usuario_id, desconto=0, forma_pagamento=None, observacao=None):
    """
    Registra uma nova venda com múltiplos itens
    """
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Criar código único para a venda
        import uuid
        codigo = f"V{uuid.uuid4().hex[:8].upper()}"

        # Inserir a venda
        cursor.execute(
            """
            INSERT INTO venda 
            (codigo, usuario_id, cliente_nome, desconto, forma_pagamento, observacao, data_venda)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (codigo, usuario_id, cliente_nome, desconto,
             forma_pagamento, observacao, datetime.datetime.now())
        )

        # Obter o ID da venda inserida
        venda_id = cursor.lastrowid

        valor_total = 0

        # Processar cada item da venda
        for item in itens:
            produto_id = item.get('produto_id')
            quantidade = item.get('quantidade', 1)

            # Obter informações do produto
            cursor.execute(
                "SELECT preco, estoque FROM produto WHERE id = ?", (produto_id,))
            produto = cursor.fetchone()

            if not produto:
                conn.rollback()
                raise ValueError(f"Produto com ID {produto_id} não encontrado")

            # Se não especificado, usa o preço do produto
            preco = item.get('preco_unitario', produto[0])
            subtotal = preco * quantidade

            # Verificar estoque
            estoque = produto[1]
            if quantidade > estoque:
                conn.rollback()
                raise ValueError(
                    f"Estoque insuficiente para o produto ID {produto_id}")

            # Registrar o item da venda
            cursor.execute(
                """
                INSERT INTO item_venda
                (venda_id, produto_id, quantidade, preco_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?)
                """,
                (venda_id, produto_id, quantidade, preco, subtotal)
            )

            # Atualizar o total da venda
            valor_total += subtotal

            # Registrar a saída no estoque
            registrar_movimento(produto_id, 'venda', quantidade,
                                usuario_id, f"Venda #{codigo}")

        # Calcular valor final considerando o desconto
        valor_final = valor_total - desconto

        # Atualizar o valor total da venda
        cursor.execute(
            "UPDATE venda SET valor_total = ?, valor_final = ? WHERE id = ?",
            (valor_total, valor_final, venda_id)
        )

        conn.commit()
        logger.info(
            f"Venda registrada: #{codigo}, Cliente: {cliente_nome}, Total: {valor_final}")

        return {
            "id": venda_id,
            "codigo": codigo,
            "cliente_nome": cliente_nome,
            "valor_total": valor_total,
            "desconto": desconto,
            "valor_final": valor_final
        }

    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao registrar venda: {str(e)}")
        raise
