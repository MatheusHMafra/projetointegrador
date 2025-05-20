"""
Utilitários para operações de banco de dados
Versão compatível com Python 3.13
"""

import logging
import datetime
from flask import current_app  # Import current_app for logging within app context
from werkzeug.security import generate_password_hash
import sqlite3
import os

# Configure logger for this module
logger = logging.getLogger(__name__)  # Use __name__ for module-specific logger
# If Flask app's logger is already configured, this will use that configuration.
# Otherwise, you might need to add basicConfig if running standalone.
# logging.basicConfig(level=logging.INFO) # Example basic config

DATABASE_NAME = "estoque.db"  # Define database name as a constant


def get_db():
    """Obtém uma conexão com o banco de dados."""
    # Using os.path.join for cross-platform compatibility if DB is in a specific subdir
    # For now, assuming it's in the root or Flask instance path handles it.
    conn = sqlite3.connect(database=DATABASE_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
    # Enable foreign key constraint enforcement for each connection
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# Removed init_db() and criar_tabelas() as schema initialization should be handled by models.py's init_db_sqlite


def inicializar_dados_exemplo():
    """Insere dados de exemplo no banco de dados, se não existirem."""
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM usuario")
        if cursor.fetchone()[0] == 0:
            logger.info("Inserindo dados de exemplo...")
            # Inserir usuários padrão
            senha_hash_admin = generate_password_hash("admin123")
            cursor.execute(
                "INSERT INTO usuario (nome, email, senha_hash, nivel_acesso, ativo) VALUES (?, ?, ?, ?, ?)",
                ("Administrador GEP", "admin@gep.com", senha_hash_admin, "admin", 1),
            )
            senha_hash_gerente = generate_password_hash("gerente123")
            cursor.execute(
                "INSERT INTO usuario (nome, email, senha_hash, nivel_acesso, ativo) VALUES (?, ?, ?, ?, ?)",
                ("Gerente Loja", "gerente@gep.com", senha_hash_gerente, "gerente", 1),
            )
            senha_hash_operador = generate_password_hash("operador123")
            cursor.execute(
                "INSERT INTO usuario (nome, email, senha_hash, nivel_acesso, ativo) VALUES (?, ?, ?, ?, ?)",
                (
                    "Operador Caixa",
                    "operador@gep.com",
                    senha_hash_operador,
                    "operador",
                    1,
                ),
            )

            # Inserir categorias padrão
            categorias = [
                ("Papelaria", "Itens de papelaria como cadernos, canetas, etc."),
                ("Escritório", "Material de escritório, organizadores."),
                ("Informática", "Acessórios de informática, mouses, teclados."),
                ("Artesanato", "Materiais para artesanato e pintura."),
                ("Presentes", "Itens para presentes e embalagens."),
            ]
            cursor.executemany(
                "INSERT INTO categoria (nome, descricao) VALUES (?, ?)", categorias
            )

            # Inserir fornecedores padrão
            fornecedores = [
                (
                    "Distribuidora Escolar Ltda",
                    "11.222.333/0001-44",
                    "contato@escolar.com",
                    "1133334444",
                    "Rua das Canetas, 123, São Paulo, SP",
                    "Carlos Dias",
                    "Entrega rápida",
                    1,
                ),
                (
                    "Papel & Cia Atacadista",
                    "44.555.666/0001-77",
                    "vendas@papelcia.com",
                    "2144445555",
                    "Avenida dos Cadernos, 456, Rio de Janeiro, RJ",
                    "Ana Lima",
                    "Grande variedade",
                    1,
                ),
                (
                    "Importados Criativos S.A.",
                    "77.888.999/0001-00",
                    "import@criativos.com",
                    "3155556666",
                    "Praça das Artes, 789, Belo Horizonte, MG",
                    "Sofia Mendes",
                    "Produtos diferenciados",
                    0,
                ),  # Inativo
                (
                    "Office Supplies Brasil",
                    "98.765.432/0001-21",
                    "contato@officesupplies.br",
                    "4166667777",
                    "Alameda dos Clips, 101, Curitiba, PR",
                    "Roberto Alves",
                    "Bom atendimento",
                    1,
                ),
            ]
            cursor.executemany(
                """
                INSERT INTO fornecedores (nome, cnpj, email, telefone, endereco, contato, observacoes, ativo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                fornecedores,
            )

            # Obter IDs das categorias e fornecedores para associar aos produtos
            cursor.execute("SELECT id FROM categoria WHERE nome = 'Papelaria'")
            cat_papelaria_id = cursor.fetchone()["id"]
            cursor.execute("SELECT id FROM categoria WHERE nome = 'Escritório'")
            cat_escritorio_id = cursor.fetchone()["id"]
            cursor.execute("SELECT id FROM categoria WHERE nome = 'Informática'")
            cat_informatica_id = cursor.fetchone()["id"]

            cursor.execute(
                "SELECT id FROM fornecedores WHERE nome = 'Distribuidora Escolar Ltda'"
            )
            forn_escolar_id = cursor.fetchone()["id"]
            cursor.execute(
                "SELECT id FROM fornecedores WHERE nome = 'Papel & Cia Atacadista'"
            )
            forn_papelcia_id = cursor.fetchone()["id"]
            cursor.execute(
                "SELECT id FROM fornecedores WHERE nome = 'Office Supplies Brasil'"
            )
            forn_office_id = cursor.fetchone()["id"]

            produtos = [
                (
                    "CAD001",
                    "Caderno Universitário Capa Dura 96fls",
                    "Caderno espiral com pauta azul.",
                    cat_papelaria_id,
                    15.90,
                    9.50,
                    150,
                    20,
                    forn_escolar_id,
                    "static/uploads/produtos/caderno_default.png",
                ),
                (
                    "CAN002",
                    "Caneta Esferográfica Azul BIC",
                    "Caneta esferográfica ponta média.",
                    cat_papelaria_id,
                    2.50,
                    1.20,
                    500,
                    50,
                    forn_papelcia_id,
                    "static/uploads/produtos/caneta_default.png",
                ),
                (
                    "LAP003",
                    "Lápis Preto Nº2 Faber-Castell",
                    "Caixa com 12 lápis grafite.",
                    cat_papelaria_id,
                    18.00,
                    10.00,
                    200,
                    30,
                    forn_escolar_id,
                    None,
                ),
                (
                    "ORG004",
                    "Organizador de Mesa Acrílico",
                    "Organizador com 3 compartimentos.",
                    cat_escritorio_id,
                    35.00,
                    22.00,
                    80,
                    10,
                    forn_office_id,
                    "static/uploads/produtos/organizador_default.png",
                ),
                (
                    "MOU005",
                    "Mouse Óptico USB Preto",
                    "Mouse com fio, design ergonômico.",
                    cat_informatica_id,
                    45.00,
                    28.00,
                    120,
                    15,
                    forn_office_id,
                    None,
                ),
            ]
            cursor.executemany(
                """
                INSERT INTO produto (codigo, nome, descricao, categoria_id, preco, preco_compra, estoque, estoque_minimo, fornecedor_id, imagem_url, data_criacao, ultima_atualizacao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
                produtos,
            )

            conn.commit()
            logger.info("Dados de exemplo inseridos com sucesso.")
        else:
            logger.info(
                "Banco de dados já contém dados. Nenhuma inserção de exemplo realizada."
            )
        return True  # Indica sucesso ou que dados já existiam
    except sqlite3.Error as e:
        logger.error(f"Erro ao inicializar dados de exemplo: {e}", exc_info=True)
        if conn:
            conn.rollback()
        return False  # Indica falha
    finally:
        if conn:
            conn.close()


def obter_estatisticas():
    """Retorna estatísticas gerais do sistema para o dashboard."""
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        resultado = {}

        # Total de produtos
        cursor.execute("SELECT COUNT(id) FROM produto")
        resultado["total_produtos"] = cursor.fetchone()[0]

        # Total de categorias
        cursor.execute("SELECT COUNT(id) FROM categoria")
        resultado["total_categorias"] = cursor.fetchone()[0]

        # Total de fornecedores ativos
        cursor.execute("SELECT COUNT(id) FROM fornecedores WHERE ativo = 1")
        resultado["total_fornecedores_ativos"] = cursor.fetchone()[0]

        # Valor total em estoque (baseado no preço de compra)
        cursor.execute(
            "SELECT SUM(estoque * preco_compra) FROM produto WHERE estoque > 0 AND preco_compra > 0"
        )
        resultado["valor_total_estoque"] = cursor.fetchone()[0] or 0.0

        # Produtos com estoque baixo
        cursor.execute(
            "SELECT COUNT(id) FROM produto WHERE estoque <= estoque_minimo AND estoque > 0"
        )
        resultado["produtos_estoque_baixo"] = cursor.fetchone()[0]

        # Produtos sem estoque
        cursor.execute("SELECT COUNT(id) FROM produto WHERE estoque = 0")
        resultado["produtos_sem_estoque"] = cursor.fetchone()[0]

        # Vendas nos últimos 30 dias (contagem e valor)
        trinta_dias_atras = (
            datetime.datetime.now() - datetime.timedelta(days=30)
        ).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "SELECT COUNT(id), COALESCE(SUM(valor_final), 0) FROM venda WHERE data_venda >= ?",
            (trinta_dias_atras,),
        )
        vendas_dados = cursor.fetchone()
        resultado["vendas_ultimos_30_dias_contagem"] = vendas_dados[0]
        resultado["vendas_ultimos_30_dias_valor"] = vendas_dados[1] or 0.0

        # Movimentações recentes (últimas 5)
        cursor.execute(
            """
            SELECT m.id, p.nome as produto_nome, m.tipo, m.quantidade, m.data_movimento, u.nome as usuario_nome
            FROM estoque_movimentacao m
            JOIN produto p ON m.produto_id = p.id
            LEFT JOIN usuario u ON m.usuario_id = u.id
            ORDER BY m.data_movimento DESC
            LIMIT 5
        """
        )
        mov_recentes_raw = cursor.fetchall()
        resultado["movimentacoes_recentes"] = []
        for row in mov_recentes_raw:
            mov_dict = dict(row)
            # Format date for display
            try:
                dt_obj = datetime.datetime.fromisoformat(mov_dict["data_movimento"])
                mov_dict["data_movimento_fmt"] = dt_obj.strftime("%d/%m/%y %H:%M")
            except:  # Catch any parsing error
                mov_dict["data_movimento_fmt"] = mov_dict["data_movimento"]  # fallback
            resultado["movimentacoes_recentes"].append(mov_dict)

        return resultado

    except sqlite3.Error as e:
        logger.error(f"Erro ao obter estatísticas: {e}", exc_info=True)
        # Return a default structure in case of error to prevent frontend issues
        return {
            "total_produtos": 0,
            "total_categorias": 0,
            "total_fornecedores_ativos": 0,
            "valor_total_estoque": 0.0,
            "produtos_estoque_baixo": 0,
            "produtos_sem_estoque": 0,
            "vendas_ultimos_30_dias_contagem": 0,
            "vendas_ultimos_30_dias_valor": 0.0,
            "movimentacoes_recentes": [],
            "error": str(e),
        }
    finally:
        if conn:
            conn.close()


def registrar_movimento(
    produto_id, tipo, quantidade, usuario_id=None, observacao=None, venda_id=None
):
    """
    Registra um movimento de estoque e atualiza o estoque do produto.
    Agora inclui transação e lida com 'ajuste' e 'venda'.

    Args:
        produto_id (int): ID do produto.
        tipo (str): 'entrada', 'saida', 'ajuste', 'venda'.
        quantidade (int): Quantidade a ser movimentada. Para 'ajuste', este é o NOVO valor do estoque.
        usuario_id (int, opcional): ID do usuário que está fazendo a movimentação.
        observacao (str, opcional): Observação sobre a movimentação.
        venda_id (int, opcional): ID da venda, se o movimento for originado de uma venda.

    Returns:
        dict: Informações sobre o movimento realizado.

    Raises:
        ValueError: Se os inputs forem inválidos ou estoque insuficiente.
        sqlite3.Error: Em caso de erro no banco de dados.
    """
    if not all([produto_id, tipo]):
        raise ValueError("Produto ID e Tipo são obrigatórios para registrar movimento.")

    # Para 'ajuste', quantidade é o novo estoque. Para outros, é a delta.
    if tipo not in ["entrada", "saida", "ajuste", "venda"]:
        raise ValueError(
            "Tipo de movimento inválido. Use 'entrada', 'saida', 'ajuste' ou 'venda'."
        )

    if tipo != "ajuste" and (not isinstance(quantidade, int) or quantidade <= 0):
        raise ValueError(
            "Quantidade (delta) deve ser um inteiro positivo para entradas, saídas ou vendas."
        )

    if tipo == "ajuste" and (not isinstance(quantidade, int) or quantidade < 0):
        raise ValueError(
            "Quantidade (novo estoque) para ajuste deve ser um inteiro não negativo."
        )

    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        conn.execute("BEGIN TRANSACTION")  # Iniciar transação

        cursor.execute(
            "SELECT id, nome, estoque FROM produto WHERE id = ?", (produto_id,)
        )
        produto = cursor.fetchone()

        if not produto:
            raise ValueError(f"Produto com ID {produto_id} não encontrado.")

        estoque_anterior = produto["estoque"]
        quantidade_movimentada = 0  # Delta real que foi movimentado

        if tipo == "entrada":
            estoque_novo = estoque_anterior + quantidade
            quantidade_movimentada = quantidade
        elif tipo == "saida" or tipo == "venda":
            if estoque_anterior < quantidade:
                raise ValueError(
                    f"Estoque insuficiente para '{produto['nome']}'. Disponível: {estoque_anterior}, Solicitado: {quantidade}."
                )
            estoque_novo = estoque_anterior - quantidade
            quantidade_movimentada = -quantidade  # Negativo para saida/venda
        elif tipo == "ajuste":
            estoque_novo = (
                quantidade  # 'quantidade' aqui é o novo valor absoluto do estoque
            )
            quantidade_movimentada = estoque_novo - estoque_anterior
        else:
            # Should not happen due to earlier check, but as a safeguard:
            raise ValueError(f"Tipo de movimento desconhecido: {tipo}")

        # Atualizar estoque do produto
        cursor.execute(
            "UPDATE produto SET estoque = ?, ultima_atualizacao = CURRENT_TIMESTAMP WHERE id = ?",
            (estoque_novo, produto_id),
        )

        # Registrar movimento
        # Nota: para 'ajuste', a 'quantidade' na tabela estoque_movimentacao registrará a DIFERENÇA.
        # Se o tipo for 'ajuste', a `quantidade_movimentada` calculada acima já é a diferença.
        # Se o tipo for 'entrada', 'saida', 'venda', `quantidade` é a delta.

        # A coluna 'quantidade' em estoque_movimentacao deve sempre refletir a variação.
        # Se o tipo é 'ajuste', a 'quantidade' que foi passada para a função era o *novo valor total*.
        # A variação é `estoque_novo - estoque_anterior`.

        # Se tipo for 'entrada', 'saida', 'venda', a 'quantidade' passada é a variação.
        # Para consistência na tabela estoque_movimentacao, a coluna 'quantidade' deve ser a variação.

        # Para 'entrada', 'saida', 'venda', a `quantidade` passada é a variação.
        # Para 'ajuste', a `quantidade_movimentada` é a variação.

        db_mov_quantidade = (
            quantidade_movimentada
            if tipo == "ajuste"
            else (quantidade if tipo == "entrada" else -quantidade)
        )

        cursor.execute(
            """
            INSERT INTO estoque_movimentacao
            (produto_id, usuario_id, tipo, quantidade, estoque_anterior, estoque_atual, observacao, venda_id, data_movimento)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                produto_id,
                usuario_id,
                tipo,
                db_mov_quantidade,
                estoque_anterior,
                estoque_novo,
                observacao,
                venda_id,
            ),
        )
        movimento_id = cursor.lastrowid
        conn.commit()  # Finalizar transação

        logger.info(
            f"Movimento de estoque ID {movimento_id} registrado: {tipo}, Produto ID {produto_id} ({produto['nome']}), "
            f"Qtd: {db_mov_quantidade}, Estoque: {estoque_anterior} -> {estoque_novo}, Usuário ID: {usuario_id}"
        )

        return {
            "id": movimento_id,
            "produto_id": produto_id,
            "produto_nome": produto["nome"],
            "tipo": tipo,
            "quantidade_movimentada": db_mov_quantidade,  # A variação efetiva
            "estoque_anterior": estoque_anterior,
            "estoque_atual": estoque_novo,
            "usuario_id": usuario_id,
            "observacao": observacao,
            "data_movimento": datetime.datetime.now().isoformat(),  # Padronizar formato de data
        }

    except (ValueError, sqlite3.Error) as e:
        if conn:
            conn.rollback()
        logger.error(
            f"Erro ao registrar movimento de estoque para produto ID {produto_id}: {e}",
            exc_info=True,
        )
        raise  # Re-raise a exceção para ser tratada pela rota que chamou
    finally:
        if conn:
            conn.close()


def buscar_produtos(
    termo=None,
    categoria_id=None,
    fornecedor_id=None,
    estoque_baixo=False,
    page=1,
    per_page=10,
    ordenar_por="p.nome",
    direcao="ASC",
):
    """
    Busca produtos com base em diferentes filtros, com ordenação e paginação.
    """
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Base da query
        query_select = """
            SELECT
                p.id, p.codigo, p.nome, p.descricao, p.preco, p.preco_compra,
                p.estoque, p.estoque_minimo, p.imagem_url,
                p.categoria_id, c.nome as categoria_nome,
                p.fornecedor_id, f.nome as fornecedor_nome
            FROM produto p
            LEFT JOIN categoria c ON p.categoria_id = c.id
            LEFT JOIN fornecedores f ON p.fornecedor_id = f.id
        """
        query_count = "SELECT COUNT(p.id) FROM produto p"  # Para contagem total

        where_clauses = []
        params = []

        if termo:
            # Busca por código, nome ou descrição
            where_clauses.append(
                "(p.codigo LIKE ? OR p.nome LIKE ? OR p.descricao LIKE ?)"
            )
            term_like = f"%{termo}%"
            params.extend([term_like, term_like, term_like])
        if categoria_id:
            where_clauses.append("p.categoria_id = ?")
            params.append(categoria_id)
        if fornecedor_id:
            where_clauses.append("p.fornecedor_id = ?")
            params.append(fornecedor_id)
        if estoque_baixo:
            where_clauses.append("p.estoque <= p.estoque_minimo")

        # Montar cláusula WHERE
        where_sql = ""
        if where_clauses:
            where_sql = " WHERE " + " AND ".join(where_clauses)

        # Executar query de contagem
        cursor.execute(query_count + where_sql, params)
        total_items = cursor.fetchone()[0]
        total_pages = (total_items + per_page - 1) // per_page if per_page > 0 else 1

        # Validar e montar cláusula ORDER BY
        allowed_sort_columns = [
            "p.nome",
            "p.preco",
            "p.estoque",
            "p.data_criacao",
        ]  # Adicionar mais se necessário
        if ordenar_por not in allowed_sort_columns:
            ordenar_por = "p.nome"  # Default seguro

        direcao_segura = (
            "DESC" if direcao.upper() == "DESC" else "ASC"
        )  # Default seguro

        order_by_sql = f" ORDER BY {ordenar_por} {direcao_segura}"

        # Montar query de paginação
        limit_offset_sql = " LIMIT ? OFFSET ?"
        pagination_params = [per_page, (page - 1) * per_page]

        # Executar query principal
        final_query = query_select + where_sql + order_by_sql + limit_offset_sql
        cursor.execute(final_query, params + pagination_params)
        produtos_rows = cursor.fetchall()

        produtos_list = [dict(row) for row in produtos_rows]

        return {
            "produtos": produtos_list,
            "total": total_items,
            "pages": total_pages,
            "page": page,
            "per_page": per_page,
        }

    except sqlite3.Error as e:
        logger.error(f"Erro ao buscar produtos: {e}", exc_info=True)
        return {
            "produtos": [],
            "total": 0,
            "pages": 0,
            "page": page,
            "per_page": per_page,
            "error": str(e),
        }
    finally:
        if conn:
            conn.close()


def obter_dados_movimentacao_grafico(dias=30):
    """
    Obtém dados agregados de movimentação de estoque para gráficos.
    Retorna entradas e saídas diárias nos últimos 'dias'.
    """
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        data_limite = (
            datetime.date.today() - datetime.timedelta(days=dias - 1)
        ).strftime("%Y-%m-%d")

        # Query para agrupar por dia e tipo
        # Usamos strftime('%Y-%m-%d', data_movimento) para agrupar por dia
        # Somamos 'quantidade' para entradas e subtraímos para saídas/vendas
        # Ajustes são mais complexos para um gráfico simples de entrada/saída,
        # então focaremos em entradas e saídas/vendas diretas.
        query = """
            SELECT
                strftime('%Y-%m-%d', data_movimento) as dia,
                SUM(CASE WHEN tipo = 'entrada' THEN quantidade ELSE 0 END) as total_entradas,
                SUM(CASE WHEN tipo IN ('saida', 'venda') THEN quantidade ELSE 0 END) as total_saidas
            FROM estoque_movimentacao
            WHERE data_movimento >= ?
            GROUP BY dia
            ORDER BY dia ASC
        """
        cursor.execute(query, (data_limite,))
        rows = cursor.fetchall()

        # Preparar dados para o gráfico
        labels = []
        entradas = []
        saidas = []

        # Criar um dicionário com todos os dias no período para garantir que todos apareçam
        # mesmo que não tenham movimentação.
        date_map = {}
        for i in range(dias):
            day = datetime.date.today() - datetime.timedelta(days=i)
            date_map[day.strftime("%Y-%m-%d")] = {"entradas": 0, "saidas": 0}

        for row in rows:
            dia_str = row["dia"]
            if dia_str in date_map:  # Adiciona apenas se estiver no range esperado
                date_map[dia_str]["entradas"] = (
                    row["total_entradas"] if row["total_entradas"] else 0
                )
                # Saídas são armazenadas como negativas na tabela, então pegamos o valor absoluto ou somamos se já for positivo
                date_map[dia_str]["saidas"] = (
                    abs(row["total_saidas"]) if row["total_saidas"] else 0
                )

        # Ordenar pela data para o gráfico
        sorted_dates = sorted(date_map.keys())

        for dia_str in sorted_dates:
            # Formatar data para DD/MM para o label
            try:
                dt_obj = datetime.datetime.strptime(dia_str, "%Y-%m-%d")
                labels.append(dt_obj.strftime("%d/%m"))
            except ValueError:
                labels.append(dia_str)  # Fallback

            entradas.append(date_map[dia_str]["entradas"])
            saidas.append(date_map[dia_str]["saidas"])

        return {"labels": labels, "entradas": entradas, "saidas": saidas}

    except sqlite3.Error as e:
        logger.error(
            f"Erro ao obter dados para gráfico de movimentação: {e}", exc_info=True
        )
        return {"labels": [], "entradas": [], "saidas": [], "error": str(e)}
    finally:
        if conn:
            conn.close()


def adicionar_venda(
    cliente_nome, itens, usuario_id, desconto=0.0, forma_pagamento=None, observacao=None
):
    """
    Registra uma nova venda com múltiplos itens, incluindo transação.
    """
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        conn.execute("BEGIN TRANSACTION")

        codigo_venda = f"V{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{os.urandom(2).hex().upper()}"
        data_venda_iso = datetime.datetime.now().isoformat()

        valor_total_bruto = 0.0

        # Primeiro, calcular o valor total bruto e validar itens
        for item_data in itens:
            if not all(
                k in item_data for k in ("produto_id", "quantidade", "preco_unitario")
            ):
                raise ValueError(
                    "Dados do item incompletos (produto_id, quantidade, preco_unitario)."
                )
            if (
                not isinstance(item_data["quantidade"], (int, float))
                or item_data["quantidade"] <= 0
            ):
                raise ValueError(
                    f"Quantidade inválida para produto ID {item_data['produto_id']}."
                )
            if (
                not isinstance(item_data["preco_unitario"], (int, float))
                or item_data["preco_unitario"] < 0
            ):
                raise ValueError(
                    f"Preço unitário inválido para produto ID {item_data['produto_id']}."
                )

            valor_total_bruto += item_data["quantidade"] * item_data["preco_unitario"]

        if (
            not isinstance(desconto, (int, float))
            or desconto < 0
            or desconto > valor_total_bruto
        ):
            raise ValueError("Valor de desconto inválido.")

        valor_final_venda = valor_total_bruto - desconto

        cursor.execute(
            """
            INSERT INTO venda (codigo, usuario_id, cliente_nome, valor_total, desconto, valor_final, forma_pagamento, observacao, data_venda)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                codigo_venda,
                usuario_id,
                cliente_nome,
                valor_total_bruto,
                desconto,
                valor_final_venda,
                forma_pagamento,
                observacao,
                data_venda_iso,
            ),
        )
        venda_id = cursor.lastrowid

        itens_processados = []
        for item_data in itens:
            produto_id = item_data["produto_id"]
            quantidade = item_data["quantidade"]
            preco_unitario = item_data["preco_unitario"]
            subtotal = quantidade * preco_unitario

            # Registrar movimento de estoque (saída por venda)
            # A função registrar_movimento já lida com a verificação de estoque
            mov_info = registrar_movimento(
                produto_id=produto_id,
                tipo="venda",
                quantidade=quantidade,
                usuario_id=usuario_id,
                observacao=f"Venda Cód: {codigo_venda}",
                venda_id=venda_id,  # Passa o venda_id para o movimento
            )  # registrar_movimento já faz commit interno se bem sucedida, ou rollback.
            # Para aninhar transações, o ideal é que registrar_movimento receba a conexão.
            # Por simplicidade aqui, assumimos que ela funciona atomicamente.
            # Se registrar_movimento falhar, a transação externa aqui fará rollback.

            cursor.execute(
                """
                INSERT INTO item_venda (venda_id, produto_id, quantidade, preco_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """,
                (venda_id, produto_id, quantidade, preco_unitario, subtotal),
            )

            itens_processados.append(
                {
                    "item_venda_id": cursor.lastrowid,
                    "produto_id": produto_id,
                    "quantidade": quantidade,
                    "preco_unitario": preco_unitario,
                    "subtotal": subtotal,
                }
            )

        conn.commit()
        logger.info(
            f"Venda ID {venda_id} (Cód: {codigo_venda}) registrada com sucesso. Valor: {valor_final_venda}, Itens: {len(itens)}."
        )

        return {
            "venda_id": venda_id,
            "codigo": codigo_venda,
            "cliente_nome": cliente_nome,
            "valor_total_bruto": valor_total_bruto,
            "desconto": desconto,
            "valor_final": valor_final_venda,
            "itens_registrados": itens_processados,
            "data_venda": data_venda_iso,
        }

    except (ValueError, sqlite3.Error) as e:
        if conn:
            conn.rollback()
        logger.error(f"Erro ao adicionar venda: {e}", exc_info=True)
        raise
    finally:
        if conn:
            conn.close()
