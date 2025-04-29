import sqlite3
from flask import Blueprint, jsonify, request
# Certifique-se que get_db, login_required, acesso_requerido estão acessíveis
from database_utils import get_db
from auth import login_required, acesso_requerido

# Criar um novo Blueprint para Relatórios
relatorios_bp = Blueprint('relatorios', __name__, url_prefix='/relatorios')


@relatorios_bp.route('/', methods=['GET'])
@login_required
# Restringir acesso a admin e gerente, ajuste conforme necessário
@acesso_requerido(['admin', 'gerente'])
def get_sales_reports():
    """
    Gera relatórios de produtos mais e menos vendidos.
    Consulta a tabela 'item_venda' para agregar as quantidades vendidas.
    """
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Define o limite de produtos a serem exibidos nos relatórios (pode ser parâmetro)
        limit = request.args.get('limit', 10, type=int)
        if limit <= 0:
            limit = 10  # Garante um limite positivo

        # --- Query Base para agregação ---
        # Seleciona o nome do produto, nome da categoria e a soma da quantidade vendida
        # Agrupa por produto para somar todas as vendas de cada um
        base_sql = """
            SELECT
                p.nome AS nome,
                c.nome AS categoria,
                SUM(iv.quantidade) AS quantidade
            FROM item_venda iv
            JOIN produto p ON iv.produto_id = p.id
            LEFT JOIN categoria c ON p.categoria_id = c.id
            WHERE iv.quantidade > 0  -- Considerar apenas itens com venda positiva?
            GROUP BY p.id, p.nome, c.nome
            HAVING SUM(iv.quantidade) > 0 -- Garante que apenas produtos vendidos apareçam
        """

        # --- Produtos Mais Vendidos ---
        # Ordena pela quantidade total vendida (descendente) e limita
        query_mais_vendidos = base_sql + " ORDER BY quantidade DESC LIMIT ?"
        cursor.execute(query_mais_vendidos, (limit,))
        mais_vendidos_rows = cursor.fetchall()
        # Converte as linhas (sqlite3.Row) em dicionários
        mais_vendidos = [dict(row) for row in mais_vendidos_rows]

        # --- Produtos Menos Vendidos ---
        # Ordena pela quantidade total vendida (ascendente) e limita
        # Isso pegará os produtos que tiveram pelo menos uma venda,
        # mas com as menores quantidades totais.
        query_menos_vendidos = base_sql + " ORDER BY quantidade ASC LIMIT ?"
        cursor.execute(query_menos_vendidos, (limit,))
        menos_vendidos_rows = cursor.fetchall()
        # Converte as linhas (sqlite3.Row) em dicionários
        menos_vendidos = [dict(row) for row in menos_vendidos_rows]

        # Retorna o JSON esperado pelo JavaScript
        return jsonify({
            "mais_vendidos": mais_vendidos,
            "menos_vendidos": menos_vendidos
        })

    except sqlite3.Error as e:
        # Em caso de erro no banco de dados (ex: tabela item_venda não existe)
        print(f"Erro SQLite ao gerar relatório: {e}")  # Log do erro
        return jsonify({"error": f"Erro no banco de dados ao gerar relatório: {e}"}), 500
    except Exception as e:
        # Captura outros erros inesperados
        print(f"Erro inesperado ao gerar relatório: {e}")  # Log do erro
        return jsonify({"error": f"Erro inesperado ao gerar relatório: {e}"}), 500
    # finally:
        # A conexão é geralmente fechada pelo teardown context do Flask
        # if conn:
        #     conn.close()
