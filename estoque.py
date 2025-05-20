from flask import Blueprint, request, jsonify, render_template, session, current_app
from database_utils import (
    adicionar_venda,
    get_db,
    registrar_movimento,
    obter_dados_movimentacao_grafico,
)  # Renomeado obter_dados_movimentacao para obter_dados_movimentacao_grafico
from auth import (
    login_required,
    acesso_requerido,
)  # Funções de autenticação e autorização
from datetime import datetime
import uuid  # Para gerar códigos únicos de venda
import sqlite3  # Para tratar exceções específicas do SQLite

# Criar Blueprint para estoque e vendas
estoque_bp = Blueprint(
    "estoque", __name__, url_prefix="/estoque"
)  # Adicionado url_prefix


# API para entrada de produtos no estoque
@estoque_bp.route("/entrada", methods=["POST"])
@login_required  # Requer que o usuário esteja logado
def entrada_produto():
    """Registra uma entrada de produto no estoque."""
    data = request.json
    produto_id = data.get("produto_id")
    quantidade_str = data.get("quantidade")  # Quantidade pode vir como string
    observacao = data.get(
        "observacao", "Entrada manual de estoque"
    )  # Observação padrão

    # Validação dos dados de entrada
    if not produto_id:
        return jsonify({"error": "ID do produto é obrigatório."}), 400

    try:
        quantidade = int(quantidade_str)  # Tenta converter quantidade para inteiro
        if quantidade <= 0:
            raise ValueError("Quantidade deve ser um número positivo.")
    except (ValueError, TypeError):
        return (
            jsonify(
                {"error": "Quantidade inválida. Deve ser um número inteiro positivo."}
            ),
            400,
        )

    try:
        # Registrar o movimento de entrada
        movimento_info = registrar_movimento(
            produto_id=produto_id,
            tipo="entrada",
            quantidade=quantidade,
            usuario_id=session.get("user_id"),  # ID do usuário logado
            observacao=observacao,
        )

        # Retornar sucesso com informações do produto atualizado
        return (
            jsonify(
                {
                    "message": "Entrada registrada com sucesso!",
                    "movimento": movimento_info,  # Inclui detalhes do movimento e estoque atual
                }
            ),
            201,
        )  # 201 Created

    except (
        ValueError
    ) as e:  # Erros de validação (ex: produto não encontrado, estoque insuficiente)
        return jsonify({"error": str(e)}), 400
    except sqlite3.Error as e:  # Erros específicos do banco de dados
        current_app.logger.error(
            f"Erro de banco de dados ao registrar entrada: {e}", exc_info=True
        )
        return jsonify({"error": "Erro no banco de dados ao registrar entrada."}), 500
    except Exception as e:  # Outros erros inesperados
        current_app.logger.error(
            f"Erro inesperado ao registrar entrada: {e}", exc_info=True
        )
        return jsonify({"error": "Erro inesperado ao processar a solicitação."}), 500


# API para saída de produtos do estoque
@estoque_bp.route("/saida", methods=["POST"])
@login_required
def saida_produto():
    """Registra uma saída de produto do estoque."""
    data = request.json
    produto_id = data.get("produto_id")
    quantidade_str = data.get("quantidade")
    observacao = data.get("observacao", "Saída manual de estoque")

    if not produto_id:
        return jsonify({"error": "ID do produto é obrigatório."}), 400

    try:
        quantidade = int(quantidade_str)
        if quantidade <= 0:
            raise ValueError("Quantidade deve ser um número positivo.")
    except (ValueError, TypeError):
        return (
            jsonify(
                {"error": "Quantidade inválida. Deve ser um número inteiro positivo."}
            ),
            400,
        )

    try:
        movimento_info = registrar_movimento(
            produto_id=produto_id,
            tipo="saida",
            quantidade=quantidade,
            usuario_id=session.get("user_id"),
            observacao=observacao,
        )
        return (
            jsonify(
                {
                    "message": "Saída registrada com sucesso!",
                    "movimento": movimento_info,
                }
            ),
            200,
        )  # 200 OK (ou 201 se considerar um novo recurso 'movimento')

    except ValueError as e:
        return jsonify({"error": str(e)}), 400  # Ex: Estoque insuficiente
    except sqlite3.Error as e:
        current_app.logger.error(
            f"Erro de banco de dados ao registrar saída: {e}", exc_info=True
        )
        return jsonify({"error": "Erro no banco de dados ao registrar saída."}), 500
    except Exception as e:
        current_app.logger.error(
            f"Erro inesperado ao registrar saída: {e}", exc_info=True
        )
        return jsonify({"error": "Erro inesperado ao processar a solicitação."}), 500


# API para ajuste de estoque
@estoque_bp.route("/ajuste", methods=["POST"])
@login_required
@acesso_requerido(["admin", "gerente"])  # Apenas admin ou gerente podem ajustar
def ajuste_estoque():
    """Ajusta o estoque de um produto para um novo valor."""
    data = request.json
    produto_id = data.get("produto_id")
    novo_estoque_str = data.get("novo_estoque")
    observacao = data.get("observacao", "Ajuste manual de estoque")

    if not produto_id:
        return jsonify({"error": "ID do produto é obrigatório."}), 400

    try:
        novo_estoque = int(novo_estoque_str)
        if novo_estoque < 0:  # Estoque não pode ser negativo
            raise ValueError("Novo valor de estoque não pode ser negativo.")
    except (ValueError, TypeError):
        return (
            jsonify(
                {
                    "error": "Novo valor de estoque inválido. Deve ser um número inteiro não negativo."
                }
            ),
            400,
        )

    try:
        # A função registrar_movimento agora lida com tipo='ajuste'
        # onde 'quantidade' é o novo valor absoluto do estoque.
        movimento_info = registrar_movimento(
            produto_id=produto_id,
            tipo="ajuste",
            quantidade=novo_estoque,  # Passa o novo valor total do estoque
            usuario_id=session.get("user_id"),
            observacao=observacao,
        )
        return (
            jsonify(
                {
                    "message": "Estoque ajustado com sucesso!",
                    "movimento": movimento_info,
                }
            ),
            200,
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except sqlite3.Error as e:
        current_app.logger.error(
            f"Erro de banco de dados ao ajustar estoque: {e}", exc_info=True
        )
        return jsonify({"error": "Erro no banco de dados ao ajustar estoque."}), 500
    except Exception as e:
        current_app.logger.error(
            f"Erro inesperado ao ajustar estoque: {e}", exc_info=True
        )
        return jsonify({"error": "Erro inesperado ao processar a solicitação."}), 500


# API para obter histórico de movimentações
@estoque_bp.route("/movimentacoes", methods=["GET"])
@login_required
def listar_movimentacoes():
    """Retorna o histórico de movimentações de estoque com filtros e paginação."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    produto_id_filter = request.args.get("produto_id", type=int)
    tipo_filter = request.args.get("tipo")
    data_inicio_filter = request.args.get("data_inicio")  # Formato YYYY-MM-DD
    data_fim_filter = request.args.get("data_fim")  # Formato YYYY-MM-DD

    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Construção da Query Principal e de Contagem
        query_base = """
            SELECT m.id, m.produto_id, m.tipo, m.quantidade, m.estoque_anterior,
                   m.estoque_atual, m.observacao, m.data_movimento, m.usuario_id,
                   p.nome as produto_nome, p.codigo as produto_codigo,
                   u.nome as usuario_nome, v.codigo as venda_codigo
            FROM movimento_estoque m
            LEFT JOIN produto p ON m.produto_id = p.id
            LEFT JOIN usuario u ON m.usuario_id = u.id
            LEFT JOIN venda v ON m.venda_id = v.id
        """
        count_query_base = "SELECT COUNT(m.id) FROM movimento_estoque m"

        conditions = []
        params = []

        if produto_id_filter:
            conditions.append("m.produto_id = ?")
            params.append(produto_id_filter)
        if tipo_filter:
            conditions.append("m.tipo = ?")
            params.append(tipo_filter)
        if data_inicio_filter:
            try:
                # Adicionar T00:00:00 para incluir o dia inteiro
                datetime.strptime(data_inicio_filter, "%Y-%m-%d")
                conditions.append("m.data_movimento >= ?")
                params.append(data_inicio_filter + " 00:00:00")
            except ValueError:
                return (
                    jsonify(
                        {"error": "Formato de data_inicio inválido. Use YYYY-MM-DD."}
                    ),
                    400,
                )
        if data_fim_filter:
            try:
                # Adicionar T23:59:59 para incluir o dia inteiro
                datetime.strptime(data_fim_filter, "%Y-%m-%d")
                conditions.append("m.data_movimento <= ?")
                params.append(data_fim_filter + " 23:59:59")
            except ValueError:
                return (
                    jsonify({"error": "Formato de data_fim inválido. Use YYYY-MM-DD."}),
                    400,
                )

        where_clause = ""
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)

        # Executar a query de contagem
        cursor.execute(count_query_base + where_clause, params)
        total_result = cursor.fetchone()
        total = total_result[0] if total_result else 0
        pages = (total + per_page - 1) // per_page if per_page > 0 else 1

        # Adicionar Ordenação e Paginação à Query Principal
        query_final = query_base + where_clause + " ORDER BY m.data_movimento DESC"
        offset = (page - 1) * per_page
        query_final += " LIMIT ? OFFSET ?"
        params_paginated = params + [per_page, offset]

        cursor.execute(query_final, params_paginated)
        movimentos_raw = cursor.fetchall()

        # Formatação dos Resultados
        resultados = []
        for m_row in movimentos_raw:
            m = dict(m_row)  # Converter sqlite3.Row para dict
            try:
                # Tenta formatar a data, que deve ser string ISO do SQLite
                data_dt = datetime.fromisoformat(str(m["data_movimento"]))
                data_formatada = data_dt.strftime("%d/%m/%Y %H:%M:%S")
            except (ValueError, TypeError):
                data_formatada = str(m["data_movimento"])  # Fallback

            resultados.append(
                {
                    "id": m["id"],
                    "produto": (
                        {
                            "id": m["produto_id"],
                            "nome": m["produto_nome"],
                            "codigo": m["produto_codigo"],
                        }
                        if m["produto_id"]
                        else None
                    ),
                    "usuario": (
                        {"id": m["usuario_id"], "nome": m["usuario_nome"]}
                        if m["usuario_id"]
                        else {"id": None, "nome": "Sistema"}
                    ),  # Nome "Sistema" se não houver usuário
                    "tipo": m["tipo"],
                    "quantidade": m["quantidade"],  # Esta é a variação
                    "estoque_anterior": m["estoque_anterior"],
                    "estoque_atual": m["estoque_atual"],
                    "observacao": m["observacao"],
                    "data": data_formatada,
                    "venda_codigo": m.get(
                        "venda_codigo"
                    ),  # Adiciona código da venda se houver
                }
            )

        return jsonify(
            {
                "movimentacoes": resultados,
                "total": total,
                "pages": pages,
                "page": page,
                "per_page": per_page,
            }
        )

    except sqlite3.Error as e:
        current_app.logger.error(
            f"Erro de banco de dados ao listar movimentações: {e}", exc_info=True
        )
        return (
            jsonify({"error": "Erro no banco de dados ao listar movimentações."}),
            500,
        )
    except Exception as e:
        current_app.logger.error(
            f"Erro inesperado ao listar movimentações: {e}", exc_info=True
        )
        return jsonify({"error": "Erro inesperado ao processar a solicitação."}), 500
    finally:
        if conn:
            conn.close()


# API para obter dados para gráfico de movimentação
@estoque_bp.route("/movimentacoes/grafico", methods=["GET"])
@login_required
def movimentacoes_grafico_endpoint():
    """Retorna dados agregados de movimentação para gráficos."""
    dias = request.args.get("dias", 30, type=int)
    if dias <= 0 or dias > 365:  # Limitar o período para evitar sobrecarga
        return jsonify({"error": "Período de dias inválido (1-365)."}), 400

    try:
        # Chama a função de database_utils que prepara os dados para o gráfico
        dados_grafico = obter_dados_movimentacao_grafico(dias)
        return jsonify(dados_grafico)
    except Exception as e:
        current_app.logger.error(
            f"Erro ao gerar dados do gráfico de movimentações: {e}", exc_info=True
        )
        return jsonify({"error": "Erro ao gerar dados para o gráfico."}), 500


# API para gerenciar vendas (Criar nova venda)
@estoque_bp.route("/vendas", methods=["GET", "POST"])
@login_required
def gerenciar_vendas():
    """Lista vendas (GET) ou registra uma nova venda (POST)."""
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        if request.method == "GET":
            page = request.args.get("page", 1, type=int)
            per_page = request.args.get(
                "per_page", 15, type=int
            )  # Aumentado per_page padrão

            # Buscar as vendas paginadas
            query = """
                SELECT v.id, v.codigo, v.cliente_nome, v.valor_total, 
                       v.desconto, v.valor_final, v.usuario_id, v.data_venda,
                       u.nome as usuario_nome,
                       (SELECT COUNT(iv.id) FROM item_venda iv WHERE iv.venda_id = v.id) as total_itens
                FROM venda v
                LEFT JOIN usuario u ON v.usuario_id = u.id
                ORDER BY v.data_venda DESC
                LIMIT ? OFFSET ?
            """
            offset = (page - 1) * per_page
            cursor.execute(query, (per_page, offset))
            vendas_raw = cursor.fetchall()

            # Contar total de vendas
            cursor.execute("SELECT COUNT(id) as total FROM venda")
            total = cursor.fetchone()["total"]
            pages = (total + per_page - 1) // per_page if per_page > 0 else 1

            # Formatar resultados
            resultados = []
            for v_row in vendas_raw:
                v = dict(v_row)
                try:
                    data_dt = datetime.fromisoformat(str(v["data_venda"]))
                    data_formatada = data_dt.strftime("%d/%m/%Y %H:%M")
                except (ValueError, TypeError):
                    data_formatada = str(v["data_venda"])

                resultados.append(
                    {
                        "id": v["id"],
                        "codigo": v["codigo"],
                        "cliente_nome": (
                            v["cliente_nome"] if v["cliente_nome"] else "N/A"
                        ),
                        "valor_total_bruto": v["valor_total"],  # Renomeado para clareza
                        "desconto": v["desconto"],
                        "valor_final": v["valor_final"],
                        "usuario_nome": (
                            v["usuario_nome"] if v["usuario_id"] else "Sistema"
                        ),
                        "data_venda": data_formatada,
                        "total_itens": v["total_itens"],
                    }
                )

            return jsonify(
                {
                    "vendas": resultados,
                    "total": total,
                    "pages": pages,
                    "page": page,
                    "per_page": per_page,
                }
            )

        elif request.method == "POST":
            # A lógica de registrar venda foi movida para database_utils.adicionar_venda
            data = request.json

            cliente_nome = data.get("cliente_nome", "Consumidor Final")  # Nome padrão
            itens = data.get("itens")
            desconto = data.get("desconto", 0.0)
            forma_pagamento = data.get("forma_pagamento")
            observacao = data.get("observacao")
            usuario_id = session.get("user_id")

            if not itens or not isinstance(itens, list):
                return jsonify({"error": "Lista de itens é obrigatória."}), 400
            if not usuario_id:  # Deve ser pego da sessão
                return (
                    jsonify({"error": "Usuário não autenticado para registrar venda."}),
                    401,
                )

            try:
                # Chamar a função de utilitário para adicionar a venda
                # Esta função agora lida com a transação e o registro de movimentos
                venda_registrada = adicionar_venda(
                    cliente_nome=cliente_nome,
                    itens=itens,
                    usuario_id=usuario_id,
                    desconto=float(desconto),
                    forma_pagamento=forma_pagamento,
                    observacao=observacao,
                )

                return (
                    jsonify(
                        {
                            "message": "Venda realizada com sucesso!",
                            "venda": venda_registrada,  # Retorna os detalhes da venda criada
                        }
                    ),
                    201,
                )  # 201 Created

            except ValueError as e:  # Erros de validação de dados ou estoque
                return jsonify({"error": str(e)}), 400
            except sqlite3.Error as e:
                current_app.logger.error(
                    f"Erro de banco de dados ao registrar venda: {e}", exc_info=True
                )
                return (
                    jsonify({"error": "Erro no banco de dados ao registrar venda."}),
                    500,
                )
            except Exception as e:
                current_app.logger.error(
                    f"Erro inesperado ao registrar venda: {e}", exc_info=True
                )
                return jsonify({"error": "Erro inesperado ao processar a venda."}), 500

    except sqlite3.Error as e:
        current_app.logger.error(
            f"Erro de banco de dados em gerenciar_vendas: {e}", exc_info=True
        )
        return jsonify({"error": "Erro no banco de dados."}), 500
    except Exception as e:
        current_app.logger.error(
            f"Erro inesperado em gerenciar_vendas: {e}", exc_info=True
        )
        return jsonify({"error": "Erro inesperado."}), 500
    finally:
        if conn:
            conn.close()


# API para detalhes de uma venda
@estoque_bp.route("/vendas/<int:venda_id>", methods=["GET"])
@login_required
def detalhes_venda(venda_id):
    """Retorna os detalhes de uma venda específica, incluindo seus itens."""
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Buscar informações da venda
        cursor.execute(
            """
            SELECT v.id, v.codigo, v.cliente_nome, v.valor_total, v.desconto,
                   v.valor_final, v.forma_pagamento, v.observacao, v.data_venda,
                   v.usuario_id, u.nome as usuario_nome
            FROM venda v
            LEFT JOIN usuario u ON v.usuario_id = u.id
            WHERE v.id = ?
        """,
            (venda_id,),
        )
        venda_raw = cursor.fetchone()

        if not venda_raw:
            return jsonify({"error": "Venda não encontrada."}), 404

        venda = dict(venda_raw)
        try:
            data_dt = datetime.fromisoformat(str(venda["data_venda"]))
            venda["data_venda_fmt"] = data_dt.strftime("%d/%m/%Y %H:%M:%S")
        except:
            venda["data_venda_fmt"] = str(venda["data_venda"])

        # Buscar itens da venda
        cursor.execute(
            """
            SELECT i.id as item_venda_id, i.produto_id, i.quantidade, i.preco_unitario, i.subtotal,
                   p.nome as produto_nome, p.codigo as produto_codigo
            FROM item_venda i
            JOIN produto p ON i.produto_id = p.id
            WHERE i.venda_id = ?
        """,
            (venda_id,),
        )
        itens_raw = cursor.fetchall()
        itens_list = [dict(item_row) for item_row in itens_raw]

        return jsonify(
            {
                "id": venda["id"],
                "codigo": venda["codigo"],
                "cliente_nome": venda["cliente_nome"],
                "valor_total_bruto": venda["valor_total"],
                "desconto": venda["desconto"],
                "valor_final": venda["valor_final"],
                "forma_pagamento": venda["forma_pagamento"],
                "observacao": venda["observacao"],
                "data_venda": venda["data_venda_fmt"],
                "usuario_nome": (
                    venda["usuario_nome"] if venda["usuario_id"] else "Sistema"
                ),
                "itens": itens_list,
            }
        )

    except sqlite3.Error as e:
        current_app.logger.error(
            f"Erro de banco de dados ao buscar detalhes da venda {venda_id}: {e}",
            exc_info=True,
        )
        return (
            jsonify({"error": "Erro no banco de dados ao buscar detalhes da venda."}),
            500,
        )
    except Exception as e:
        current_app.logger.error(
            f"Erro inesperado ao buscar detalhes da venda {venda_id}: {e}",
            exc_info=True,
        )
        return jsonify({"error": "Erro inesperado ao processar a solicitação."}), 500
    finally:
        if conn:
            conn.close()


# API para cancelar uma venda (apenas admin e gerente)
@estoque_bp.route("/vendas/<int:venda_id>/cancelar", methods=["POST"])
@login_required
@acesso_requerido(["admin", "gerente"])
def cancelar_venda(venda_id):
    """Cancela uma venda, retornando os itens ao estoque e excluindo a venda."""
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        conn.execute("BEGIN TRANSACTION")

        cursor.execute("SELECT id, codigo FROM venda WHERE id = ?", (venda_id,))
        venda = cursor.fetchone()
        if not venda:
            conn.rollback()  # Importante reverter se a venda não existe
            return jsonify({"error": "Venda não encontrada."}), 404

        # Buscar itens da venda para retornar ao estoque
        cursor.execute(
            "SELECT produto_id, quantidade FROM item_venda WHERE venda_id = ?",
            (venda_id,),
        )
        itens_da_venda = cursor.fetchall()

        for item in itens_da_venda:
            # registrar_movimento já lida com a transação interna e erros de estoque
            # Para aninhar corretamente, idealmente passaria a `conn` para `registrar_movimento`
            # ou faria a lógica de estoque aqui. Por simplicidade, chamamos como está.
            # Se `registrar_movimento` falhar, a transação externa aqui fará rollback.
            registrar_movimento(
                produto_id=item["produto_id"],
                tipo="entrada",  # Devolvendo ao estoque
                quantidade=item["quantidade"],
                usuario_id=session.get("user_id"),
                observacao=f"Cancelamento da Venda Cód: {venda['codigo']}",
                venda_id=venda_id,  # Referencia a venda cancelada
            )

        # Excluir itens da venda e a venda em si
        # ON DELETE CASCADE na tabela item_venda (se definido no schema) poderia simplificar,
        # mas excluir explicitamente é mais claro.
        cursor.execute("DELETE FROM item_venda WHERE venda_id = ?", (venda_id,))
        cursor.execute("DELETE FROM venda WHERE id = ?", (venda_id,))

        conn.commit()
        current_app.logger.info(
            f"Venda ID {venda_id} (Cód: {venda['codigo']}) cancelada por usuário ID {session.get('user_id')}."
        )
        return jsonify({"message": "Venda cancelada com sucesso!"})

    except ValueError as e:  # Erros de registrar_movimento
        if conn:
            conn.rollback()
        current_app.logger.warning(
            f"Erro de validação ao cancelar venda {venda_id}: {e}", exc_info=True
        )
        return jsonify({"error": str(e)}), 400
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        current_app.logger.error(
            f"Erro de banco de dados ao cancelar venda {venda_id}: {e}", exc_info=True
        )
        return jsonify({"error": "Erro no banco de dados ao cancelar venda."}), 500
    except Exception as e:
        if conn:
            conn.rollback()
        current_app.logger.error(
            f"Erro inesperado ao cancelar venda {venda_id}: {e}", exc_info=True
        )
        return jsonify({"error": "Erro inesperado ao processar o cancelamento."}), 500
    finally:
        if conn:
            conn.close()


# --- Rotas de Página HTML ---
# Estas rotas apenas renderizam os templates. A lógica de dados é via API.


@estoque_bp.route("/movimentacoes/page", methods=["GET"])
@login_required
def movimentacoes_page():
    """Renderiza a página de visualização de movimentações de estoque."""
    return render_template(
        "movimentacoes.html"
    )  # Certifique-se que este template existe


@estoque_bp.route("/vendas/page", methods=["GET"])
@login_required
def vendas_page():
    """Renderiza a página de listagem de vendas."""
    return render_template("vendas.html")  # Certifique-se que este template existe


@estoque_bp.route("/vendas/nova", methods=["GET"])
@login_required
@acesso_requerido(
    ["admin", "gerente", "operador"]
)  # Definir quem pode criar nova venda
def nova_venda_page():
    """Renderiza a página para registrar uma nova venda."""
    return render_template("nova_venda.html")  # Certifique-se que este template existe
