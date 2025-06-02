import sqlite3
from flask import (
    Blueprint,
    jsonify,
    request,
    current_app,
    session,
)  # Added session and current_app
from database_utils import get_db  # Utility to get DB connection
from auth import login_required, acesso_requerido  # Auth decorators

# Criar um novo Blueprint para Relatórios
relatorios_bp = Blueprint("relatorios", __name__, url_prefix="/relatorios")


@relatorios_bp.route("/vendas/produtos", methods=["GET"])
@login_required
@acesso_requerido(["admin", "gerente"])  # Restringir acesso
def get_product_sales_reports():
    """
    Gera relatórios de produtos mais e menos vendidos.
    Consulta a tabela 'item_venda' para agregar as quantidades vendidas.
    """
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        limit = request.args.get("limit", 10, type=int)
        if not (0 < limit <= 100):  # Adicionar um limite máximo razoável
            limit = 10

        # --- Query Base para agregação de vendas de produtos ---
        # Seleciona o ID, código, nome do produto, nome da categoria e a soma da quantidade vendida.
        # Agrupa por produto para somar todas as vendas de cada um.
        # Usa LEFT JOIN para categoria para incluir produtos sem categoria (se existirem).
        # Usa INNER JOIN para item_venda para considerar apenas produtos que foram vendidos.
        base_sql_vendas = """
            SELECT
                p.id as produto_id,
                p.codigo as produto_codigo,
                p.nome AS produto_nome,
                c.nome AS categoria_nome,
                SUM(iv.quantidade) AS total_vendido,
                p.estoque as estoque_atual
            FROM produto p
            LEFT JOIN categoria c ON p.categoria_id = c.id
            INNER JOIN item_venda iv ON p.id = iv.produto_id
            GROUP BY p.id, p.codigo, p.nome, c.nome, p.estoque
            HAVING SUM(iv.quantidade) > 0
        """

        # --- Produtos Mais Vendidos ---
        query_mais_vendidos = (
            f"{base_sql_vendas} ORDER BY total_vendido DESC, produto_nome ASC LIMIT ?"
        )
        cursor.execute(query_mais_vendidos, (limit,))
        mais_vendidos_rows = cursor.fetchall()
        mais_vendidos = [dict(row) for row in mais_vendidos_rows]

        # --- Produtos Menos Vendidos (dentre os que foram vendidos) ---
        # Ordena pela quantidade total vendida (ascendente) e limita.
        query_menos_vendidos = (
            f"{base_sql_vendas} ORDER BY total_vendido ASC, produto_nome ASC LIMIT ?"
        )
        cursor.execute(query_menos_vendidos, (limit,))
        menos_vendidos_rows = cursor.fetchall()
        menos_vendidos = [dict(row) for row in menos_vendidos_rows]

        # --- Produtos Não Vendidos (Opcional, mas útil) ---
        # Produtos que existem na tabela 'produto' mas não em 'item_venda'
        query_nao_vendidos = """
            SELECT
                p.id as produto_id,
                p.codigo as produto_codigo,
                p.nome as produto_nome,
                c.nome as categoria_nome,
                p.estoque as estoque_atual,
                0 as total_vendido
            FROM produto p
            LEFT JOIN categoria c ON p.categoria_id = c.id
            WHERE p.id NOT IN (SELECT DISTINCT iv.produto_id FROM item_venda iv)
            ORDER BY p.nome ASC
            LIMIT ? 
        """
        # Se quiser listar todos não vendidos, remova o LIMIT ou ajuste-o.
        # Para consistência, usando o mesmo limit.
        cursor.execute(query_nao_vendidos, (limit,))
        nao_vendidos_rows = cursor.fetchall()
        nao_vendidos = [dict(row) for row in nao_vendidos_rows]

        return jsonify(
            {
                "mais_vendidos": mais_vendidos,
                "menos_vendidos_com_venda": menos_vendidos,  # Clarifica que são os menos vendidos *que tiveram vendas*
                "nao_vendidos": nao_vendidos,  # Produtos que nunca foram vendidos
            }
        )

    except sqlite3.OperationalError as e:
        # Tratar especificamente o erro de tabela não existente
        if "no such table: item_venda" in str(e).lower():
            current_app.logger.warning(
                "Tabela 'item_venda' não encontrada ao gerar relatórios de vendas de produtos."
            )
            return (
                jsonify(
                    {
                        "error": "Funcionalidade de relatório de vendas de produtos indisponível: dados de vendas não encontrados."
                    }
                ),
                501,
            )  # Not Implemented
        current_app.logger.error(
            f"Erro de banco de dados ao gerar relatório de vendas de produtos: {e}",
            exc_info=True,
        )
        return jsonify({"error": "Erro no banco de dados ao gerar relatório."}), 500
    except Exception as e:
        current_app.logger.error(
            f"Erro inesperado ao gerar relatório de vendas de produtos: {e}",
            exc_info=True,
        )
        return jsonify({"error": "Erro inesperado ao gerar relatório."}), 500
    finally:
        if conn:
            conn.close()


# Outras rotas de relatório podem ser adicionadas aqui
# Exemplo: Relatório de Níveis de Estoque
@relatorios_bp.route("/estoque/niveis", methods=["GET"])
@login_required
@acesso_requerido(["admin", "gerente"])
def get_stock_level_reports():
    """Gera relatórios sobre níveis de estoque (baixo, adequado, excessivo - exemplo)."""
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        status_filter = request.args.get("status")  # 'baixo', 'ok', 'excesso'

        # Query base
        # Corrected table name for join
        query_select = """
            SELECT p.id, p.codigo, p.nome, p.estoque, p.estoque_minimo,
                   c.nome as categoria_nome, f.nome as fornecedor_nome,
                   CASE
                       WHEN p.estoque <= p.estoque_minimo THEN 'baixo'
                       WHEN p.estoque > p.estoque_minimo AND p.estoque <= (p.estoque_minimo * 2) THEN 'ok' -- Exemplo de 'ok'
                       ELSE 'excesso' -- Exemplo de 'excesso'
                   END as status_estoque
            FROM produto p
            LEFT JOIN categoria c ON p.categoria_id = c.id
            LEFT JOIN fornecedores f ON p.fornecedor_id = f.id
        """
        query_count = "SELECT COUNT(p.id) FROM produto p" # Base count, filters will be added

        where_clauses = []
        params = [] # Parameters for the WHERE clauses

        # Build WHERE clause for the main query and count query
        # Need to join with fornecedores if filtering by it, but here we only filter by status_estoque
        # The status_estoque is a calculated field, so we might need a subquery or filter after fetching
        # For simplicity with SQLite, let's fetch all and filter in Python if status_filter is complex,
        # or adjust the CASE statement and WHERE clause carefully.
        # A more direct SQL way for status_filter:
        
        status_condition_sql = ""
        if status_filter:
            if status_filter == "baixo":
                status_condition_sql = "p.estoque <= p.estoque_minimo"
            elif status_filter == "ok":
                status_condition_sql = "p.estoque > p.estoque_minimo AND p.estoque <= (p.estoque_minimo * 2)"
            elif status_filter == "excesso":
                status_condition_sql = "p.estoque > (p.estoque_minimo * 2)"
            
            if status_condition_sql:
                 where_clauses.append(status_condition_sql)


        where_sql = ""
        if where_clauses:
            where_sql = " WHERE " + " AND ".join(where_clauses)
        
        # Contagem
        # The count query also needs the WHERE clause
        cursor.execute(query_count + where_sql, params)
        total_items = cursor.fetchone()[0]
        total_pages = (total_items + per_page - 1) // per_page if per_page > 0 else 1

        # Listagem
        order_by_sql = " ORDER BY p.nome ASC" 
        limit_offset_sql = " LIMIT ? OFFSET ?"

        final_query = query_select + where_sql + order_by_sql + limit_offset_sql
        
        # Add pagination params to the existing params for WHERE clause
        params_paginated = params + [per_page, (page - 1) * per_page]

        cursor.execute(final_query, params_paginated)
        produtos_rows = cursor.fetchall()

        return jsonify(
            {
                "produtos_niveis_estoque": [dict(row) for row in produtos_rows],
                "total": total_items,
                "pages": total_pages,
                "page": page,
                "per_page": per_page,
            }
        )

    except sqlite3.Error as e:
        current_app.logger.error(
            f"Erro de BD ao gerar relatório de níveis de estoque: {e}", exc_info=True
        )
        return (
            jsonify(
                {
                    "error": "Erro no banco de dados ao gerar relatório de níveis de estoque."
                }
            ),
            500,
        )
    except Exception as e:
        current_app.logger.error(
            f"Erro inesperado ao gerar relatório de níveis de estoque: {e}",
            exc_info=True,
        )
        return (
            jsonify(
                {"error": "Erro inesperado ao gerar relatório de níveis de estoque."}
            ),
            500,
        )
    finally:
        if conn:
            conn.close()
