"""
Utilitários para operações de banco de dados
Versão compatível com Python 3.13
"""

import logging
import datetime
from werkzeug.security import generate_password_hash
import sqlite3
import os


logger = logging.getLogger(__name__)


DATABASE_NAME = "estoque.db"


def get_db():
    """Obtém uma conexão com o banco de dados."""

    conn = sqlite3.connect(database=DATABASE_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA cache_size = -2000;")
    conn.execute("PRAGMA temp_store = MEMORY;")
    return conn


def inicializar_dados_exemplo():
    """Insere dados de exemplo no banco de dados, se não existirem."""
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM usuario")
        if cursor.fetchone()[0] == 0:
            logger.info("Inserindo dados de exemplo...")

            senha_hash_admin = generate_password_hash("admin123")
            cursor.execute(
                "INSERT INTO usuario (nome, email, senha_hash, nivel_acesso, ativo) VALUES (?, ?, ?, ?, ?)",
                ("Administrador GEP", "admin@gep.com",
                 senha_hash_admin, "admin", 1),
            )
            senha_hash_gerente = generate_password_hash("gerente123")
            cursor.execute(
                "INSERT INTO usuario (nome, email, senha_hash, nivel_acesso, ativo) VALUES (?, ?, ?, ?, ?)",
                ("Gerente Loja", "gerente@gep.com",
                 senha_hash_gerente, "gerente", 1),
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

            categorias = [
                ("Escritório e Papelaria", "Itens de escritório e papelaria como cadernos, canetas, etc."),
                ("Informática", "Acessórios de informática, mouses, teclados."),
                ("Artesanato", "Materiais para artesanato e pintura."),
                ("Presentes", "Itens para presentes e embalagens."),
            ]
            cursor.executemany(
                "INSERT INTO categoria (nome, descricao) VALUES (?, ?)", categorias
            )

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
                    "Atacadista Central Ltda",
                    "44.555.666/0001-77",
                    "vendas@atacadistacentral.com",
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
                ),
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

            cursor.execute("SELECT id FROM categoria WHERE nome = 'Escritório e Papelaria'")
            cat_papelaria_id = cursor.fetchone()["id"]
            cursor.execute(
                "SELECT id FROM categoria WHERE nome = 'Escritório'")
            cat_escritorio_id = cursor.fetchone()["id"]
            cursor.execute(
                "SELECT id FROM categoria WHERE nome = 'Informática'")
            cat_informatica_id = cursor.fetchone()["id"]

            cursor.execute(
                "SELECT id FROM fornecedores WHERE nome = 'Distribuidora Escolar Ltda'"
            )
            forn_escolar_id = cursor.fetchone()["id"]
            cursor.execute(
                "SELECT id FROM fornecedores WHERE nome = 'Atacadista Central Ltda'"
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
        return True
    except sqlite3.Error as e:
        logger.error(
            f"Erro ao inicializar dados de exemplo: {e}", exc_info=True)
        if conn:
            conn.rollback()
        return False
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

        cursor.execute(
            "SELECT COUNT(id) FROM produto WHERE COALESCE(ativo, 1) = 1")
        resultado["total_produtos"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(id) FROM categoria")
        resultado["total_categorias"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(id) FROM fornecedores WHERE ativo = 1")
        resultado["total_fornecedores_ativos"] = cursor.fetchone()[0]

        cursor.execute(
            "SELECT SUM(estoque * preco_compra) FROM produto WHERE estoque > 0 AND preco_compra > 0 AND COALESCE(ativo, 1) = 1"
        )
        resultado["valor_total_estoque"] = cursor.fetchone()[0] or 0.0

        cursor.execute(
            "SELECT COUNT(id) FROM produto WHERE estoque <= estoque_minimo AND estoque > 0 AND COALESCE(ativo, 1) = 1"
        )
        resultado["produtos_estoque_baixo"] = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(id) FROM produto WHERE estoque = 0 AND COALESCE(ativo, 1) = 1"
        )
        resultado["produtos_sem_estoque"] = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(id) FROM produto WHERE COALESCE(ativo, 1) = 0")
        resultado["produtos_inativos"] = cursor.fetchone()[0]

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

        cursor.execute(
            """
            SELECT m.id, p.nome as produto_nome, m.tipo, m.quantidade, m.data_movimento, u.nome as usuario_nome
            FROM estoque_movimentacao m
            JOIN produto p ON m.produto_id = p.id
            LEFT JOIN usuario u ON m.usuario_id = u.id
            WHERE COALESCE(p.ativo, 1) = 1
            ORDER BY m.data_movimento DESC
            LIMIT 5
        """
        )
        mov_recentes_raw = cursor.fetchall()
        resultado["movimentacoes_recentes"] = []
        for row in mov_recentes_raw:
            mov_dict = dict(row)

            try:
                dt_obj = datetime.datetime.fromisoformat(
                    mov_dict["data_movimento"])
                mov_dict["data_movimento_fmt"] = dt_obj.strftime(
                    "%d/%m/%y %H:%M")
            except Exception:

                mov_dict["data_movimento_fmt"] = mov_dict["data_movimento"]
            resultado["movimentacoes_recentes"].append(mov_dict)

        cursor.execute(
            """
            SELECT COALESCE(classificacao, 'outro') as classif, SUM(ABS(quantidade)) as total
            FROM estoque_movimentacao
            WHERE tipo = 'entrada'
            GROUP BY classif
            """
        )
        entradas_rows = cursor.fetchall()
        resultado["entradas_por_classificacao"] = {
            row["classif"]: row["total"] for row in entradas_rows
        }

        cursor.execute(
            """
            SELECT COALESCE(classificacao, 'outro') as classif, SUM(ABS(quantidade)) as total
            FROM estoque_movimentacao
            WHERE tipo IN ('saida', 'venda')
            GROUP BY classif
            """
        )
        saidas_rows = cursor.fetchall()
        resultado["saidas_por_classificacao"] = {
            row["classif"]: row["total"] for row in saidas_rows
        }

        return resultado

    except sqlite3.Error as e:
        logger.error(f"Erro ao obter estatísticas: {e}", exc_info=True)

        return {
            "total_produtos": 0,
            "total_categorias": 0,
            "total_fornecedores_ativos": 0,
            "valor_total_estoque": 0.0,
            "produtos_estoque_baixo": 0,
            "produtos_sem_estoque": 0,
            "produtos_inativos": 0,
            "vendas_ultimos_30_dias_contagem": 0,
            "vendas_ultimos_30_dias_valor": 0.0,
            "movimentacoes_recentes": [],
            "entradas_por_classificacao": {},
            "saidas_por_classificacao": {},
            "error": str(e),
        }
    finally:
        if conn:
            conn.close()


def registrar_movimento(
    produto_id,
    tipo,
    quantidade,
    usuario_id=None,
    observacao=None,
    venda_id=None,
    classificacao=None,
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
        raise ValueError(
            "Produto ID e Tipo são obrigatórios para registrar movimento.")

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
        conn.execute("BEGIN TRANSACTION")

        cursor.execute(
            "SELECT id, nome, estoque FROM produto WHERE id = ?", (produto_id,)
        )
        produto = cursor.fetchone()

        if not produto:
            raise ValueError(f"Produto com ID {produto_id} não encontrado.")

        estoque_anterior = produto["estoque"]
        quantidade_movimentada = 0

        if tipo == "entrada":
            estoque_novo = estoque_anterior + quantidade
            quantidade_movimentada = quantidade
        elif tipo == "saida" or tipo == "venda":
            if estoque_anterior < quantidade:
                raise ValueError(
                    f"Estoque insuficiente para '{produto['nome']}'. Disponível: {estoque_anterior}, Solicitado: {quantidade}."
                )
            estoque_novo = estoque_anterior - quantidade
            quantidade_movimentada = -quantidade
        elif tipo == "ajuste":
            estoque_novo = quantidade
            quantidade_movimentada = estoque_novo - estoque_anterior
        else:

            raise ValueError(f"Tipo de movimento desconhecido: {tipo}")

        cursor.execute(
            "UPDATE produto SET estoque = ?, ultima_atualizacao = CURRENT_TIMESTAMP WHERE id = ?",
            (estoque_novo, produto_id),
        )

        db_mov_quantidade = (
            quantidade_movimentada
            if tipo == "ajuste"
            else (quantidade if tipo == "entrada" else -quantidade)
        )

        cursor.execute(
            """
            INSERT INTO estoque_movimentacao
            (produto_id, usuario_id, tipo, quantidade, estoque_anterior, estoque_atual, observacao, venda_id, data_movimento, classificacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
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
                classificacao,
            ),
        )
        movimento_id = cursor.lastrowid
        conn.commit()

        logger.info(
            f"Movimento de estoque ID {movimento_id} registrado: {tipo}, Produto ID {produto_id} ({produto['nome']}), "
            f"Qtd: {db_mov_quantidade}, Estoque: {estoque_anterior} -> {estoque_novo}, Usuário ID: {usuario_id}"
        )

        return {
            "id": movimento_id,
            "produto_id": produto_id,
            "produto_nome": produto["nome"],
            "tipo": tipo,
            "quantidade_movimentada": db_mov_quantidade,
            "estoque_anterior": estoque_anterior,
            "estoque_atual": estoque_novo,
            "usuario_id": usuario_id,
            "observacao": observacao,
            "data_movimento": datetime.datetime.now().isoformat(),
        }

    except (ValueError, sqlite3.Error) as e:
        if conn:
            conn.rollback()
        logger.error(
            f"Erro ao registrar movimento de estoque para produto ID {produto_id}: {e}",
            exc_info=True,
        )
        raise
    finally:
        if conn:
            conn.close()


def buscar_produtos(
    termo=None,
    categoria_id=None,
    fornecedor_id=None,
    estoque_baixo=False,
    incluir_inativos=False,
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
        if isinstance(estoque_baixo, str):
            estoque_baixo = estoque_baixo.lower() == "true"
        if isinstance(incluir_inativos, str):
            incluir_inativos = incluir_inativos.lower() == "true"

        conn = get_db()
        cursor = conn.cursor()

        query_select = """
            SELECT
                p.id, p.codigo, p.nome, p.descricao, p.preco, p.preco_compra,
                p.estoque, p.estoque_minimo, p.ativo, p.imagem_url,
                p.categoria_id, c.nome as categoria_nome,
                p.fornecedor_id, f.nome as fornecedor_nome
            FROM produto p
            LEFT JOIN categoria c ON p.categoria_id = c.id
            LEFT JOIN fornecedores f ON p.fornecedor_id = f.id
        """
        query_count = "SELECT COUNT(p.id) FROM produto p"

        where_clauses = []
        params = []

        if incluir_inativos:
            where_clauses.append("COALESCE(p.ativo, 1) = 0")
        else:
            where_clauses.append("COALESCE(p.ativo, 1) = 1")

        if termo:

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

        where_sql = ""
        if where_clauses:
            where_sql = " WHERE " + " AND ".join(where_clauses)

        cursor.execute(query_count + where_sql, params)
        total_items = cursor.fetchone()[0]
        total_pages = (total_items + per_page -
                       1) // per_page if per_page > 0 else 1

        allowed_sort_columns = [
            "p.nome",
            "p.preco",
            "p.estoque",
            "p.data_criacao",
        ]
        if ordenar_por not in allowed_sort_columns:
            ordenar_por = "p.nome"

        direcao_segura = "DESC" if direcao.upper() == "DESC" else "ASC"

        order_by_sql = f" ORDER BY {ordenar_por} {direcao_segura}"

        limit_offset_sql = " LIMIT ? OFFSET ?"
        pagination_params = [per_page, (page - 1) * per_page]

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

        labels = []
        entradas = []
        saidas = []

        date_map = {}
        for i in range(dias):
            day = datetime.date.today() - datetime.timedelta(days=i)
            date_map[day.strftime("%Y-%m-%d")] = {"entradas": 0, "saidas": 0}

        for row in rows:
            dia_str = row["dia"]
            if dia_str in date_map:
                date_map[dia_str]["entradas"] = (
                    row["total_entradas"] if row["total_entradas"] else 0
                )

                date_map[dia_str]["saidas"] = (
                    abs(row["total_saidas"]) if row["total_saidas"] else 0
                )

        sorted_dates = sorted(date_map.keys())

        for dia_str in sorted_dates:

            try:
                dt_obj = datetime.datetime.strptime(dia_str, "%Y-%m-%d")
                labels.append(dt_obj.strftime("%d/%m"))
            except ValueError:
                labels.append(dia_str)

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

            valor_total_bruto += item_data["quantidade"] * \
                item_data["preco_unitario"]

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

            registrar_movimento(
                produto_id=produto_id,
                tipo="venda",
                quantidade=quantidade,
                usuario_id=usuario_id,
                observacao=f"Venda Cód: {codigo_venda}",
                venda_id=venda_id,
            )

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
