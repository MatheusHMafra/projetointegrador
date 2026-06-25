import sqlite3
from flask import (
    Blueprint,
    jsonify,
    request,
    current_app,
    render_template,
)
from database_utils import get_db
from auth import login_required, acesso_requerido


relatorios_bp = Blueprint("relatorios", __name__, url_prefix="/relatorios")


@relatorios_bp.route("/vendas/produtos", methods=["GET"])
@login_required
@acesso_requerido(["admin", "gerente"])
def get_product_sales_reports():
    """
    Gera relatórios de produtos mais e menos vendidos.
    Consulta a tabela 'estoque_movimentacao' para agregar as quantidades vendidas de forma unificada.
    """
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        limit = request.args.get("limit", 10, type=int)
        if not (0 < limit <= 100):
            limit = 10

        base_sql_vendas = """
            SELECT
                p.id as produto_id,
                p.codigo as produto_codigo,
                p.nome AS produto_nome,
                c.nome AS categoria_nome,
                COALESCE(SUM(
                    CASE
                        WHEN em.tipo = 'venda' OR (em.tipo = 'saida' AND em.classificacao = 'venda') THEN ABS(em.quantidade)
                        WHEN em.tipo = 'entrada' AND em.classificacao = 'devolucao' THEN -ABS(em.quantidade)
                        ELSE 0
                    END
                ), 0) AS total_vendido,
                p.estoque as estoque_atual
            FROM produto p
            LEFT JOIN categoria c ON p.categoria_id = c.id
            JOIN estoque_movimentacao em ON p.id = em.produto_id
            GROUP BY p.id, p.codigo, p.nome, c.nome, p.estoque
            HAVING total_vendido > 0
        """

        query_mais_vendidos = (
            f"{base_sql_vendas} ORDER BY total_vendido DESC, produto_nome ASC LIMIT ?"
        )
        cursor.execute(query_mais_vendidos, (limit,))
        mais_vendidos_rows = cursor.fetchall()
        mais_vendidos = [dict(row) for row in mais_vendidos_rows]

        query_menos_vendidos = (
            f"{base_sql_vendas} ORDER BY total_vendido ASC, produto_nome ASC LIMIT ?"
        )
        cursor.execute(query_menos_vendidos, (limit,))
        menos_vendidos_rows = cursor.fetchall()
        menos_vendidos = [dict(row) for row in menos_vendidos_rows]

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
            WHERE p.id NOT IN (
                SELECT DISTINCT em.produto_id 
                FROM estoque_movimentacao em 
                WHERE em.tipo = 'venda' OR (em.tipo = 'saida' AND em.classificacao = 'venda')
            )
            ORDER BY p.nome ASC
            LIMIT ? 
        """
        cursor.execute(query_nao_vendidos, (limit,))
        nao_vendidos_rows = cursor.fetchall()
        nao_vendidos = [dict(row) for row in nao_vendidos_rows]

        return jsonify(
            {
                "mais_vendidos": mais_vendidos,
                "menos_vendidos_com_venda": menos_vendidos,
                "nao_vendidos": nao_vendidos,
            }
        )

    except sqlite3.Error as e:
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
        status_filter = request.args.get("status")

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
        query_count = "SELECT COUNT(p.id) FROM produto p"

        where_clauses = []
        params = []

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

        cursor.execute(query_count + where_sql, params)
        total_items = cursor.fetchone()[0]
        total_pages = (total_items + per_page -
                       1) // per_page if per_page > 0 else 1

        order_by_sql = " ORDER BY p.nome ASC"

        final_query = query_select + where_sql + order_by_sql

        cursor.execute(final_query, params)
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


@relatorios_bp.route("/fornecedores/resumo", methods=["GET"])
@login_required
@acesso_requerido(["admin", "gerente"])
def get_supplier_summary_report():
    """Gera o relatório de resumo de fornecedores."""
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        status_filter = request.args.get("status")

        query_select = """
            SELECT 
                f.id as fornecedor_id,
                f.nome as fornecedor_nome,
                f.cnpj,
                f.telefone,
                f.email,
                f.ativo,
                COUNT(p.id) as total_produtos,
                COALESCE(SUM(p.estoque), 0) as total_estoque,
                COALESCE(SUM(p.estoque * COALESCE(p.preco_compra, 0)), 0) as valor_total_estoque
            FROM fornecedores f
            LEFT JOIN produto p ON f.id = p.fornecedor_id
        """
        query_count = "SELECT COUNT(*) FROM fornecedores f"

        where_clauses = []
        params = []

        if status_filter == "ativos":
            where_clauses.append("f.ativo = 1")
        elif status_filter == "inativos":
            where_clauses.append("f.ativo = 0")

        where_sql = ""
        if where_clauses:
            where_sql = " WHERE " + " AND ".join(where_clauses)

        cursor.execute(query_count + where_sql, params)
        total_items = cursor.fetchone()[0]
        total_pages = (total_items + per_page -
                       1) // per_page if per_page > 0 else 1

        group_by_sql = " GROUP BY f.id, f.nome, f.cnpj, f.telefone, f.email, f.ativo"
        order_by_sql = " ORDER BY fornecedor_nome ASC"

        final_query = query_select + where_sql + group_by_sql + order_by_sql

        cursor.execute(final_query, params)
        rows = cursor.fetchall()

        return jsonify(
            {
                "fornecedores_resumo": [dict(row) for row in rows],
                "total": total_items,
                "pages": total_pages,
                "page": page,
                "per_page": per_page,
            }
        )
    except sqlite3.Error as e:
        current_app.logger.error(
            f"Erro de BD ao gerar resumo de fornecedores: {e}", exc_info=True
        )
        return (
            jsonify(
                {"error": "Erro no banco de dados ao gerar resumo de fornecedores."}
            ),
            500,
        )
    except Exception as e:
        current_app.logger.error(
            f"Erro inesperado ao gerar resumo de fornecedores: {e}", exc_info=True
        )
        return (
            jsonify({"error": "Erro inesperado ao gerar resumo de fornecedores."}),
            500,
        )
    finally:
        if conn:
            conn.close()


@relatorios_bp.route("/fornecedores/produtos", methods=["GET"])
@login_required
@acesso_requerido(["admin", "gerente"])
def get_supplier_products_report():
    """Gera o relatório detalhado de produtos por fornecedor."""
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        status_filter = request.args.get("status")

        query = """
            SELECT 
                f.id as fornecedor_id,
                f.nome as fornecedor_nome,
                f.cnpj as fornecedor_cnpj,
                p.id as produto_id,
                p.codigo as produto_codigo,
                p.nome as produto_nome,
                p.preco as produto_preco,
                p.preco_compra as produto_preco_compra,
                p.estoque as produto_estoque,
                p.ativo as produto_ativo
            FROM fornecedores f
            LEFT JOIN produto p ON f.id = p.fornecedor_id
        """

        where_clauses = []
        params = []

        if status_filter == "ativos":
            where_clauses.append("f.ativo = 1")
        elif status_filter == "inativos":
            where_clauses.append("f.ativo = 0")

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += " ORDER BY f.nome ASC, p.nome ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        fornecedores_dict = {}
        for row in rows:
            f_id = row["fornecedor_id"]
            if f_id not in fornecedores_dict:
                fornecedores_dict[f_id] = {
                    "id": f_id,
                    "nome": row["fornecedor_nome"],
                    "cnpj": row["fornecedor_cnpj"],
                    "produtos": [],
                }
            if row["produto_id"] is not None:
                fornecedores_dict[f_id]["produtos"].append(
                    {
                        "id": row["produto_id"],
                        "codigo": row["produto_codigo"],
                        "nome": row["produto_nome"],
                        "preco": row["produto_preco"],
                        "preco_compra": row["produto_preco_compra"],
                        "estoque": row["produto_estoque"],
                        "ativo": row["produto_ativo"],
                    }
                )

        return jsonify(list(fornecedores_dict.values()))
    except sqlite3.Error as e:
        current_app.logger.error(
            f"Erro de BD ao gerar produtos por fornecedor: {e}", exc_info=True
        )
        return jsonify({"error": "Erro no banco de dados."}), 500
    except Exception as e:
        current_app.logger.error(f"Erro inesperado: {e}", exc_info=True)
        return jsonify({"error": "Erro inesperado."}), 500
    finally:
        if conn:
            conn.close()


@relatorios_bp.route("/vendas/operadores", methods=["GET"])
@login_required
@acesso_requerido(["admin", "gerente"])
def get_operator_sales_report():
    """Gera o relatório de vendas por operador."""
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        query = """
            SELECT 
                u.id as usuario_id,
                u.nome as usuario_nome,
                u.email as usuario_email,
                u.nivel_acesso as usuario_nivel,
                SUM(CASE WHEN em.tipo = 'venda' OR (em.tipo = 'saida' AND em.classificacao = 'venda') THEN ABS(em.quantidade) ELSE 0 END) as total_itens_vendidos,
                SUM(CASE WHEN em.tipo = 'entrada' AND em.classificacao = 'devolucao' THEN ABS(em.quantidade) ELSE 0 END) as total_itens_devolvidos,
                SUM(
                    (CASE WHEN em.tipo = 'venda' OR (em.tipo = 'saida' AND em.classificacao = 'venda') THEN ABS(em.quantidade)
                          WHEN em.tipo = 'entrada' AND em.classificacao = 'devolucao' THEN -ABS(em.quantidade)
                          ELSE 0 END) * COALESCE(p.preco, 0)
                ) as receita_total
            FROM usuario u
            JOIN estoque_movimentacao em ON u.id = em.usuario_id
            LEFT JOIN produto p ON em.produto_id = p.id
            WHERE em.tipo = 'venda' 
               OR (em.tipo = 'saida' AND em.classificacao = 'venda') 
               OR (em.tipo = 'entrada' AND em.classificacao = 'devolucao')
            GROUP BY u.id, u.nome, u.email, u.nivel_acesso
            ORDER BY receita_total DESC
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        return jsonify([dict(row) for row in rows])
    except sqlite3.Error as e:
        current_app.logger.error(
            f"Erro de BD ao gerar vendas por operador: {e}", exc_info=True
        )
        return jsonify({"error": "Erro no banco de dados."}), 500
    except Exception as e:
        current_app.logger.error(f"Erro inesperado: {e}", exc_info=True)
        return jsonify({"error": "Erro inesperado."}), 500
    finally:
        if conn:
            conn.close()


@relatorios_bp.route("/registros/gerais", methods=["GET"])
@login_required
@acesso_requerido(["admin", "gerente"])
def get_general_records_report():
    """Gera o relatório de registros gerais (movimentações de estoque)."""
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        classificacao_filter = request.args.get("classificacao")
        data_inicio_filter = request.args.get("data_inicio")
        data_fim_filter = request.args.get("data_fim")
        tipo_filter = request.args.get("tipo")

        query_base = """
            SELECT 
                m.id,
                m.tipo,
                m.classificacao,
                m.quantidade,
                m.estoque_anterior,
                m.estoque_atual,
                m.observacao,
                m.data_movimento,
                p.nome as produto_nome,
                p.codigo as produto_codigo,
                u.nome as usuario_nome
            FROM estoque_movimentacao m
            LEFT JOIN produto p ON m.produto_id = p.id
            LEFT JOIN usuario u ON m.usuario_id = u.id
        """
        count_query_base = "SELECT COUNT(m.id) FROM estoque_movimentacao m"

        conditions = []
        params = []

        if classificacao_filter:
            conditions.append("m.classificacao = ?")
            params.append(classificacao_filter)
        if tipo_filter:
            conditions.append("m.tipo = ?")
            params.append(tipo_filter)
        if data_inicio_filter:
            conditions.append("DATE(m.data_movimento) >= ?")
            params.append(data_inicio_filter)
        if data_fim_filter:
            conditions.append("DATE(m.data_movimento) <= ?")
            params.append(data_fim_filter)

        where_sql = ""
        if conditions:
            where_sql = " WHERE " + " AND ".join(conditions)

        cursor.execute(count_query_base + where_sql, params)
        total_items = cursor.fetchone()[0]
        total_pages = (total_items + per_page - 1) // per_page if per_page > 0 else 1

        order_by_sql = " ORDER BY m.data_movimento DESC"
        limit_sql = " LIMIT ? OFFSET ?"
        query_params = params + [per_page, (page - 1) * per_page]

        cursor.execute(query_base + where_sql + order_by_sql + limit_sql, query_params)
        rows = cursor.fetchall()

        return jsonify({
            "registros": [dict(row) for row in rows],
            "total": total_items,
            "pages": total_pages,
            "page": page,
            "per_page": per_page,
        })
    except sqlite3.Error as e:
        current_app.logger.error(f"Erro de BD ao gerar registros gerais: {e}", exc_info=True)
        return jsonify({"error": "Erro no banco de dados."}), 500
    except Exception as e:
        current_app.logger.error(f"Erro inesperado: {e}", exc_info=True)
        return jsonify({"error": "Erro inesperado."}), 500
    finally:
        if conn:
            conn.close()


@relatorios_bp.route("/page", methods=["GET"])
@login_required
@acesso_requerido(["admin", "gerente"])
def relatorios_page():
    """Renderiza a página de geração de relatórios."""
    return render_template("relatorios.html")
