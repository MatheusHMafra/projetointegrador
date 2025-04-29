from flask import Blueprint, request, jsonify, render_template, session, current_app
from database_utils import get_db, registrar_movimento, buscar_produtos, obter_dados_movimentacao
from auth import login_required, acesso_requerido
from datetime import datetime
import uuid

# Criar Blueprint para estoque e vendas
estoque_bp = Blueprint('estoque', __name__)

# API para entrada de produtos no estoque


@estoque_bp.route('/entrada', methods=['POST'])
@login_required
def entrada_produto():
    data = request.json
    produto_id = data.get('produto_id')
    quantidade = data.get('quantidade')
    observacao = data.get('observacao', '')

    if not produto_id or not quantidade or quantidade <= 0:
        return jsonify({"error": "Produto e quantidade válida são obrigatórios"}), 400

    try:
        resultado = registrar_movimento(
            produto_id=produto_id,
            tipo='entrada',
            quantidade=quantidade,
            usuario_id=session.get('user_id'),
            observacao=observacao
        )

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nome, codigo, estoque FROM produto WHERE id = ?", (produto_id,))
        produto = cursor.fetchone()

        return jsonify({
            "message": "Entrada registrada com sucesso",
            "produto": {
                "id": produto['id'],
                "nome": produto['nome'],
                "codigo": produto['codigo'],
                "estoque_atual": produto['estoque']
            }
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Erro ao registrar entrada: {str(e)}"}), 500

# API para saída de produtos do estoque


@estoque_bp.route('/saida', methods=['POST'])
@login_required
def saida_produto():
    data = request.json
    produto_id = data.get('produto_id')
    quantidade = data.get('quantidade')
    observacao = data.get('observacao', '')

    if not produto_id or not quantidade or quantidade <= 0:
        return jsonify({"error": "Produto e quantidade válida são obrigatórios"}), 400

    try:
        resultado = registrar_movimento(
            produto_id=produto_id,
            tipo='saida',
            quantidade=quantidade,
            usuario_id=session.get('user_id'),
            observacao=observacao
        )

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nome, codigo, estoque FROM produto WHERE id = ?", (produto_id,))
        produto = cursor.fetchone()

        return jsonify({
            "message": "Saída registrada com sucesso",
            "produto": {
                "id": produto['id'],
                "nome": produto['nome'],
                "codigo": produto['codigo'],
                "estoque_atual": produto['estoque']
            }
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Erro ao registrar saída: {str(e)}"}), 500

# API para ajuste de estoque


@estoque_bp.route('/ajuste', methods=['POST'])
@login_required
@acesso_requerido(['admin', 'gerente'])
def ajuste_estoque():
    data = request.json
    produto_id = data.get('produto_id')
    novo_estoque = data.get('novo_estoque')
    observacao = data.get('observacao', 'Ajuste manual de estoque')

    if not produto_id or novo_estoque is None or novo_estoque < 0:
        return jsonify({"error": "Produto e novo valor de estoque válido são obrigatórios"}), 400

    try:
        resultado = registrar_movimento(
            produto_id=produto_id,
            tipo='ajuste',
            quantidade=novo_estoque,
            usuario_id=session.get('user_id'),
            observacao=observacao
        )

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nome, codigo, estoque FROM produto WHERE id = ?", (produto_id,))
        produto = cursor.fetchone()

        return jsonify({
            "message": "Estoque ajustado com sucesso",
            "produto": {
                "id": produto['id'],
                "nome": produto['nome'],
                "codigo": produto['codigo'],
                "estoque_atual": produto['estoque']
            }
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Erro ao ajustar estoque: {str(e)}"}), 500

# API para obter histórico de movimentações


@estoque_bp.route('/movimentacoes', methods=['GET'])
@login_required
def movimentacoes():
    """
    Retorna o histórico de movimentações de estoque com filtros e paginação.
    Query Params:
        page (int, opcional): Número da página (default: 1).
        per_page (int, opcional): Itens por página (default: 20).
        produto_id (int, opcional): ID do produto para filtrar.
        tipo (str, opcional): Tipo de movimentação para filtrar (ex: 'entrada', 'saida').
    Returns:
        JSON: Dicionário com a lista de movimentações e metadados de paginação.
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    produto_id = request.args.get('produto_id', type=int)
    tipo = request.args.get('tipo')

    conn = None  # Inicializa conn como None para garantir que sempre terá um valor
    try:
        conn = get_db()
        cursor = conn.cursor()

        # --- Construção da Query Principal ---
        query_base = """
            SELECT m.id, m.produto_id, m.tipo, m.quantidade, m.estoque_anterior,
                   m.estoque_atual, m.observacao, m.data_movimento, m.usuario_id,
                   p.nome as produto_nome, p.codigo as produto_codigo,
                   u.nome as usuario_nome
            FROM movimento_estoque m
            LEFT JOIN produto p ON m.produto_id = p.id
            LEFT JOIN usuario u ON m.usuario_id = u.id
            WHERE 1=1
        """
        params = []
        conditions = []

        # Adicionar filtros dinamicamente
        if produto_id:
            conditions.append("m.produto_id = ?")
            params.append(produto_id)

        if tipo:
            conditions.append("m.tipo = ?")
            params.append(tipo)

        # Montar a query final com filtros
        query = query_base
        if conditions:
            query += " AND " + " AND ".join(conditions)

        # --- Construção da Query de Contagem (para paginação) ---
        count_query_base = """
            SELECT COUNT(*) as total
            FROM movimento_estoque m
            WHERE 1=1
        """
        count_params = []
        count_conditions = []

        if produto_id:
            count_conditions.append("m.produto_id = ?")
            count_params.append(produto_id)

        if tipo:
            count_conditions.append("m.tipo = ?")
            count_params.append(tipo)

        count_query = count_query_base
        if count_conditions:
            count_query += " AND " + " AND ".join(count_conditions)

        # Executar a query de contagem
        cursor.execute(count_query, count_params)
        total_result = cursor.fetchone()
        total = total_result['total'] if total_result else 0
        pages = (total + per_page - 1) // per_page if per_page > 0 else 1

        # --- Adicionar Ordenação e Paginação à Query Principal ---
        query += " ORDER BY m.data_movimento DESC"
        offset = (page - 1) * per_page
        query += " LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        # Executar a query principal
        cursor.execute(query, params)
        movimentos = cursor.fetchall()

        # --- Formatação dos Resultados ---
        resultados = []
        for m in movimentos:
            # CORREÇÃO APLICADA AQUI: Adicionado .%f ao formato strptime
            try:
                data_formatada = datetime.strptime(
                    str(m['data_movimento']), '%Y-%m-%d %H:%M:%S.%f').strftime('%d/%m/%Y %H:%M:%S')
            except ValueError:
                # Fallback caso não tenha microssegundos (ou outro erro de formato)
                try:
                    data_formatada = datetime.strptime(
                        str(m['data_movimento']), '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M:%S')
                except Exception as e:
                    # Log do erro ou valor padrão se a data for crucial
                    current_app.logger.error(
                        f"Erro ao formatar data {m['data_movimento']}: {e}")
                    # Ou None, ou uma string de erro
                    data_formatada = str(m['data_movimento'])

            resultados.append({
                "id": m['id'],
                "produto": {
                    "id": m['produto_id'],
                    "nome": m['produto_nome'],
                    "codigo": m['produto_codigo']
                } if m['produto_id'] else None,
                "usuario": {
                    "id": m['usuario_id'],
                    "nome": m['usuario_nome']
                } if m['usuario_id'] else None,
                "tipo": m['tipo'],
                "quantidade": m['quantidade'],
                "estoque_anterior": m['estoque_anterior'],
                "estoque_atual": m['estoque_atual'],
                "observacao": m['observacao'],
                "data": data_formatada  # Usar a data formatada
            })

        # Fechar cursor (boa prática, embora o 'finally' cuide da conexão)
        cursor.close()

        return jsonify({
            "movimentacoes": resultados,
            "total": total,
            "pages": pages,
            "page": page
        })

    except Exception as e:
        # Logar o erro para diagnóstico
        current_app.logger.error(
            f"Erro na rota /movimentacoes: {e}", exc_info=True)
        # Retornar um erro genérico para o cliente
        return jsonify({"message": "Erro ao buscar movimentações", "error": str(e)}), 500
    finally:
        # Garantir que a conexão seja fechada mesmo se ocorrer um erro
        if conn:
            conn.close()

# API para obter dados para gráfico de movimentação


@estoque_bp.route('/movimentacoes/grafico', methods=['GET'])
@login_required
def movimentacoes_grafico():
    dias = request.args.get('dias', 30, type=int)

    dados = obter_dados_movimentacao(dias)

    return jsonify(dados)

# API para gerenciar vendas (Criar nova venda)


@estoque_bp.route('/vendas', methods=['GET', 'POST'])
@login_required
def vendas():
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        conn = get_db()
        cursor = conn.cursor()

        # Buscar as vendas paginadas
        query = """
            SELECT v.id, v.codigo, v.cliente_nome, v.valor_total, 
                   v.valor_final, v.usuario_id, v.data_venda,
                   u.nome as usuario_nome
            FROM venda v
            LEFT JOIN usuario u ON v.usuario_id = u.id
            ORDER BY v.data_venda DESC
            LIMIT ? OFFSET ?
        """
        offset = (page - 1) * per_page
        cursor.execute(query, [per_page, offset])
        vendas = cursor.fetchall()

        # Contar total
        cursor.execute("SELECT COUNT(*) as total FROM venda")
        total = cursor.fetchone()['total']
        pages = (total + per_page - 1) // per_page

        # Formatar resultados
        resultados = []
        for v in vendas:
            resultados.append({
                "id": v['id'],
                "codigo": v['codigo'],
                "cliente_nome": v['cliente_nome'],
                "valor_total": v['valor_total'],
                "valor_final": v['valor_final'],
                "usuario": v['usuario_nome'] if v['usuario_id'] else "Sistema",
                "data": datetime.strptime(v['data_venda'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
            })

        return jsonify({
            "vendas": resultados,
            "total": total,
            "pages": pages,
            "page": page
        })

    elif request.method == 'POST':
        data = request.json

        # Validar os dados
        if 'itens' not in data or not data['itens']:
            return jsonify({"error": "É necessário incluir pelo menos um item na venda"}), 400

        itens = data['itens']

        # Calcular valor total dos itens
        valor_total = 0
        for item_data in itens:
            if not all(k in item_data for k in ('produto_id', 'quantidade', 'preco_unitario')):
                return jsonify({"error": "Dados do item incompletos"}), 400
            valor_total += item_data['quantidade'] * \
                item_data['preco_unitario']

        # Aplicar desconto se houver
        desconto = data.get('desconto', 0)
        valor_final = valor_total - desconto

        conn = get_db()
        cursor = conn.cursor()

        # Código único para a venda
        codigo = f"V{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:4].upper()}"

        try:
            conn.execute("BEGIN TRANSACTION")

            # Inserir venda
            cursor.execute("""
                INSERT INTO venda (
                    codigo, usuario_id, cliente_nome, valor_total, 
                    desconto, valor_final, forma_pagamento, observacao, data_venda
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                codigo,
                session.get('user_id'),
                data.get('cliente_nome', ''),
                valor_total,
                desconto,
                valor_final,
                data.get('forma_pagamento', ''),
                data.get('observacao', ''),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))

            # Obter o ID da venda inserida
            venda_id = cursor.lastrowid

            # Adicionar itens e baixar estoque
            for item_data in itens:
                subtotal = item_data['quantidade'] * \
                    item_data['preco_unitario']

                # Inserir item
                cursor.execute("""
                    INSERT INTO item_venda (
                        venda_id, produto_id, quantidade, preco_unitario, subtotal
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    venda_id,
                    item_data['produto_id'],
                    item_data['quantidade'],
                    item_data['preco_unitario'],
                    subtotal
                ))

                # Baixar estoque
                registrar_movimento(
                    produto_id=item_data['produto_id'],
                    tipo='venda',
                    quantidade=item_data['quantidade'],
                    usuario_id=session.get('user_id'),
                    observacao=f"Venda {codigo}"
                )

            conn.execute("COMMIT")

            return jsonify({
                "message": "Venda realizada com sucesso!",
                "venda": {
                    "id": venda_id,
                    "codigo": codigo,
                    "valor_final": valor_final
                }
            })

        except Exception as e:
            conn.execute("ROLLBACK")
            return jsonify({"error": f"Erro ao registrar venda: {str(e)}"}), 500

# API para detalhes de uma venda


@estoque_bp.route('/vendas/<int:id>', methods=['GET'])
@login_required
def detalhes_venda(id):
    conn = get_db()
    cursor = conn.cursor()

    # Buscar informações da venda
    cursor.execute("""
        SELECT v.id, v.codigo, v.cliente_nome, v.valor_total, v.desconto,
               v.valor_final, v.forma_pagamento, v.observacao, v.data_venda,
               v.usuario_id, u.nome as usuario_nome
        FROM venda v
        LEFT JOIN usuario u ON v.usuario_id = u.id
        WHERE v.id = ?
    """, (id,))

    venda = cursor.fetchone()
    if not venda:
        return jsonify({"error": "Venda não encontrada"}), 404

    # Buscar itens da venda
    cursor.execute("""
        SELECT i.id, i.produto_id, i.quantidade, i.preco_unitario, i.subtotal,
               p.nome as produto_nome, p.codigo as produto_codigo
        FROM item_venda i
        LEFT JOIN produto p ON i.produto_id = p.id
        WHERE i.venda_id = ?
    """, (id,))

    itens = cursor.fetchall()

    return jsonify({
        "id": venda['id'],
        "codigo": venda['codigo'],
        "cliente_nome": venda['cliente_nome'],
        "valor_total": venda['valor_total'],
        "desconto": venda['desconto'],
        "valor_final": venda['valor_final'],
        "forma_pagamento": venda['forma_pagamento'],
        "observacao": venda['observacao'],
        "data_venda": datetime.strptime(venda['data_venda'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M'),
        "usuario": venda['usuario_nome'] if venda['usuario_id'] else "Sistema",
        "itens": [{
            "id": item['id'],
            "produto_id": item['produto_id'],
            "produto_nome": item['produto_nome'],
            "produto_codigo": item['produto_codigo'],
            "quantidade": item['quantidade'],
            "preco_unitario": item['preco_unitario'],
            "subtotal": item['subtotal']
        } for item in itens]
    })

# API para cancelar uma venda (apenas admin e gerente)


@estoque_bp.route('/vendas/<int:id>/cancelar', methods=['POST'])
@login_required
@acesso_requerido(['admin', 'gerente'])
def cancelar_venda(id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, codigo FROM venda WHERE id = ?", (id,))
    venda = cursor.fetchone()
    if not venda:
        return jsonify({"error": "Venda não encontrada"}), 404

    try:
        conn.execute("BEGIN TRANSACTION")

        # Buscar itens da venda
        cursor.execute(
            "SELECT produto_id, quantidade FROM item_venda WHERE venda_id = ?", (id,))
        itens = cursor.fetchall()

        # Retornar os itens ao estoque
        for item in itens:
            registrar_movimento(
                produto_id=item['produto_id'],
                tipo='entrada',
                quantidade=item['quantidade'],
                usuario_id=session.get('user_id'),
                observacao=f"Cancelamento de venda {venda['codigo']}"
            )

        # Excluir itens da venda
        cursor.execute("DELETE FROM item_venda WHERE venda_id = ?", (id,))

        # Excluir a venda
        cursor.execute("DELETE FROM venda WHERE id = ?", (id,))

        conn.execute("COMMIT")

        return jsonify({"message": "Venda cancelada com sucesso!"})

    except Exception as e:
        conn.execute("ROLLBACK")
        return jsonify({"error": f"Erro ao cancelar venda: {str(e)}"}), 500

# Página de movimentações


@estoque_bp.route('/movimentacoes/page', methods=['GET'])
@login_required
def movimentacoes_page():
    return render_template('movimentacoes.html')

# Página de vendas


@estoque_bp.route('/vendas/page', methods=['GET'])
@login_required
def vendas_page():
    return render_template('vendas.html')

# Página de realizar venda


@estoque_bp.route('/vendas/nova', methods=['GET'])
@login_required
def nova_venda_page():
    return render_template('nova_venda.html')
