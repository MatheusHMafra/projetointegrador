import sqlite3
from flask import (
    Blueprint,
    request,
    jsonify,
    render_template,
    session,
    flash,
    redirect,
    url_for,
    current_app,
)
from database_utils import get_db  # Assuming get_db is correctly configured
from auth import login_required, acesso_requerido  # Auth decorators

# Blueprint para fornecedores
# Adicionado url_prefix para consistência e para evitar colisões de nome de rota
fornecedores_bp = Blueprint("fornecedores", __name__, url_prefix="/fornecedores")


# --- Rotas da API ---


@fornecedores_bp.route("/", methods=["GET", "POST"])
@login_required  # Requer login para todas as operações neste endpoint
def gerenciar_todos_fornecedores():
    """
    GET: Lista fornecedores com paginação, filtros e contagem de produtos.
    POST: Adiciona um novo fornecedor.
    """
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        if request.method == "GET":
            # Verificar permissão para listar
            # (Pode ser ajustado se operadores também puderem ver)
            if session.get("user_level") not in ["admin", "gerente", "operador"]:
                return (
                    jsonify(
                        {"error": "Permissão negada para visualizar fornecedores."}
                    ),
                    403,
                )

            page = request.args.get("page", 1, type=int)
            per_page = request.args.get("per_page", 10, type=int)
            ativo_filter_str = request.args.get("ativo")  # 'true', 'false', ou None
            busca_termo = request.args.get("busca")
            ordenar_por = request.args.get("ordenar", "f.nome")  # Coluna de ordenação
            direcao_ordem = request.args.get("direcao", "asc").upper()  # ASC ou DESC

            # Validação da ordenação para segurança
            colunas_permitidas_ordem = [
                "f.nome",
                "f.cnpj",
                "f.email",
                "f.data_cadastro",
                "total_produtos_agg",
            ]
            if ordenar_por not in colunas_permitidas_ordem:
                ordenar_por = "f.nome"  # Padrão seguro
            if direcao_ordem not in ["ASC", "DESC"]:
                direcao_ordem = "ASC"  # Padrão seguro

            params_where = []

            # Subquery para contagem de produtos por fornecedor
            # Esta subquery será usada tanto na contagem total quanto na listagem principal
            # para evitar N+1 queries.
            produtos_count_subquery = """
                (SELECT COUNT(p.id) FROM produto p WHERE p.fornecedor_id = f.id)
            """

            # Base da query de listagem
            query_select_base = f"""
                SELECT f.id, f.nome, f.cnpj, f.telefone, f.email, f.contato, f.ativo,
                       {produtos_count_subquery} as total_produtos
                FROM fornecedores f
            """
            # Base da query de contagem total de fornecedores
            query_count_base = "SELECT COUNT(f.id) FROM fornecedores f"

            where_clauses = []

            if ativo_filter_str is not None:
                where_clauses.append("f.ativo = ?")
                params_where.append(1 if ativo_filter_str.lower() == "true" else 0)

            if busca_termo:
                busca_like = f"%{busca_termo}%"
                where_clauses.append(
                    "(f.nome LIKE ? OR f.cnpj LIKE ? OR f.email LIKE ? OR f.contato LIKE ?)"
                )
                params_where.extend([busca_like] * 4)

            where_sql = ""
            if where_clauses:
                where_sql = " WHERE " + " AND ".join(where_clauses)

            # Executar query de contagem total de fornecedores
            cursor.execute(query_count_base + where_sql, params_where)
            total_fornecedores = cursor.fetchone()[0]
            total_pages = (
                (total_fornecedores + per_page - 1) // per_page if per_page > 0 else 1
            )

            # Montar query final de listagem com ordenação e paginação
            # Se ordenar por 'total_produtos_agg', precisamos usar o alias da subquery
            # SQLite pode ter limitações com alias de subquery na cláusula ORDER BY diretamente.
            # Uma forma é usar a subquery completa ou garantir que o alias é reconhecido.
            # Para simplificar, se for ordenar por total_produtos, podemos usar a subquery no ORDER BY.
            order_by_clause = f"ORDER BY {ordenar_por if ordenar_por != 'total_produtos_agg' else produtos_count_subquery} {direcao_ordem}"

            limit_offset_sql = " LIMIT ? OFFSET ?"
            params_paginated = params_where + [per_page, (page - 1) * per_page]

            final_query_select = (
                query_select_base + where_sql + order_by_clause + limit_offset_sql
            )

            cursor.execute(final_query_select, params_paginated)
            fornecedores_rows = cursor.fetchall()

            fornecedores_list = [dict(row) for row in fornecedores_rows]

            return jsonify(
                {
                    "fornecedores": fornecedores_list,
                    "total": total_fornecedores,
                    "pages": total_pages,
                    "page": page,
                    "per_page": per_page,
                }
            )

        elif request.method == "POST":
            # Verificar permissão para adicionar
            if session.get("user_level") not in ["admin", "gerente"]:
                return (
                    jsonify({"error": "Permissão negada para adicionar fornecedor."}),
                    403,
                )

            data = request.json
            if not data or not data.get("nome"):
                return jsonify({"error": "Nome do fornecedor é obrigatório."}), 400

            nome = data["nome"].strip()
            cnpj = (
                data.get("cnpj", "").strip() or None
            )  # CNPJ é opcional, mas se fornecido, deve ser único
            email = data.get("email", "").strip() or None
            telefone = data.get("telefone", "").strip() or None
            endereco = data.get("endereco", "").strip() or None
            contato = data.get("contato", "").strip() or None
            observacoes = data.get("observacoes", "").strip() or None
            ativo = bool(data.get("ativo", True))  # Padrão para ativo

            # Verificar se CNPJ já existe, se fornecido
            if cnpj:
                cursor.execute("SELECT id FROM fornecedor WHERE cnpj = ?", (cnpj,))
                if cursor.fetchone():
                    return (
                        jsonify({"error": "CNPJ já cadastrado."}),
                        409,
                    )  # 409 Conflict

            # Inserir novo fornecedor
            sql_insert = """
                INSERT INTO fornecedor 
                (nome, cnpj, email, telefone, endereco, contato, observacoes, ativo, data_cadastro, ultima_atualizacao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
            params_insert = (
                nome,
                cnpj,
                email,
                telefone,
                endereco,
                contato,
                observacoes,
                ativo,
            )

            cursor.execute(sql_insert, params_insert)
            new_id = cursor.lastrowid
            conn.commit()

            return (
                jsonify(
                    {
                        "message": "Fornecedor cadastrado com sucesso!",
                        "fornecedor": {"id": new_id, "nome": nome, "ativo": ativo},
                    }
                ),
                201,
            )  # 201 Created

    except sqlite3.Error as e:
        if conn and request.method == "POST":
            conn.rollback()
        current_app.logger.error(
            f"Erro de banco de dados em fornecedores: {e}", exc_info=True
        )
        return jsonify({"error": "Erro no banco de dados."}), 500
    except Exception as e:
        if conn and request.method == "POST":
            conn.rollback()
        current_app.logger.error(f"Erro inesperado em fornecedores: {e}", exc_info=True)
        return jsonify({"error": "Erro inesperado no servidor."}), 500
    finally:
        if conn:
            conn.close()


@fornecedores_bp.route("/<int:fornecedor_id>", methods=["GET", "PUT", "DELETE"])
@login_required
def gerenciar_fornecedor_especifico(fornecedor_id):
    """
    GET: Retorna detalhes de um fornecedor específico.
    PUT: Atualiza um fornecedor específico.
    DELETE: Exclui um fornecedor específico.
    """
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Buscar fornecedor para todas as operações
        cursor.execute("SELECT * FROM fornecedor WHERE id = ?", (fornecedor_id,))
        fornecedor_row = cursor.fetchone()

        if not fornecedor_row:
            return jsonify({"error": "Fornecedor não encontrado."}), 404

        fornecedor_dict = dict(fornecedor_row)

        if request.method == "GET":
            # Opcional: Adicionar contagem de produtos ou lista resumida de produtos
            cursor.execute(
                "SELECT COUNT(id) as total_produtos FROM produto WHERE fornecedor_id = ?",
                (fornecedor_id,),
            )
            fornecedor_dict["total_produtos"] = cursor.fetchone()["total_produtos"]
            return jsonify(fornecedor_dict)

        elif request.method == "PUT":
            if session.get("user_level") not in ["admin", "gerente"]:
                return (
                    jsonify({"error": "Permissão negada para atualizar fornecedor."}),
                    403,
                )

            data = request.json
            if not data:
                return (
                    jsonify({"error": "Nenhum dado fornecido para atualização."}),
                    400,
                )

            update_fields = []
            params_update = []

            # Campos permitidos para atualização
            allowed_to_update = [
                "nome",
                "cnpj",
                "email",
                "telefone",
                "endereco",
                "contato",
                "observacoes",
                "ativo",
            ]

            for field in allowed_to_update:
                if field in data:
                    # Validação específica para CNPJ (se diferente do atual)
                    if (
                        field == "cnpj"
                        and data[field] != fornecedor_dict["cnpj"]
                        and data[field]
                    ):
                        cursor.execute(
                            "SELECT id FROM fornecedor WHERE cnpj = ? AND id != ?",
                            (data[field], fornecedor_id),
                        )
                        if cursor.fetchone():
                            return (
                                jsonify(
                                    {
                                        "error": f"CNPJ '{data[field]}' já está em uso por outro fornecedor."
                                    }
                                ),
                                409,
                            )

                    update_fields.append(f"{field} = ?")
                    params_update.append(
                        data[field] if data[field] is not None else None
                    )  # Permite setar para NULL se o campo aceitar

            if not update_fields:
                return jsonify({"message": "Nenhuma alteração detectada."}), 200

            update_fields.append("ultima_atualizacao = CURRENT_TIMESTAMP")
            params_update.append(fornecedor_id)  # Para a cláusula WHERE

            sql_update = (
                f"UPDATE fornecedor SET {', '.join(update_fields)} WHERE id = ?"
            )

            cursor.execute(sql_update, params_update)
            conn.commit()

            # Buscar dados atualizados para retornar
            cursor.execute("SELECT * FROM fornecedor WHERE id = ?", (fornecedor_id,))
            fornecedor_atualizado = dict(cursor.fetchone())

            return jsonify(
                {
                    "message": "Fornecedor atualizado com sucesso!",
                    "fornecedor": fornecedor_atualizado,
                }
            )

        elif request.method == "DELETE":
            if session.get("user_level") not in ["admin"]:  # Apenas admin pode excluir
                return (
                    jsonify({"error": "Permissão negada para excluir fornecedor."}),
                    403,
                )

            # Verificar se existem produtos associados a este fornecedor
            cursor.execute(
                "SELECT COUNT(id) FROM produto WHERE fornecedor_id = ?",
                (fornecedor_id,),
            )
            if cursor.fetchone()[0] > 0:
                return (
                    jsonify(
                        {
                            "error": "Não é possível excluir. Existem produtos associados a este fornecedor."
                        }
                    ),
                    400,
                )

            cursor.execute("DELETE FROM fornecedor WHERE id = ?", (fornecedor_id,))
            conn.commit()

            return jsonify({"message": "Fornecedor excluído com sucesso."})

    except sqlite3.Error as e:
        if conn and request.method in ["PUT", "DELETE"]:
            conn.rollback()
        current_app.logger.error(
            f"Erro de banco de dados em fornecedor ID {fornecedor_id}: {e}",
            exc_info=True,
        )
        return jsonify({"error": "Erro no banco de dados."}), 500
    except Exception as e:
        if conn and request.method in ["PUT", "DELETE"]:
            conn.rollback()
        current_app.logger.error(
            f"Erro inesperado em fornecedor ID {fornecedor_id}: {e}", exc_info=True
        )
        return jsonify({"error": "Erro inesperado no servidor."}), 500
    finally:
        if conn:
            conn.close()


@fornecedores_bp.route("/<int:fornecedor_id>/produtos", methods=["GET"])
@login_required
def listar_produtos_do_fornecedor(fornecedor_id):
    """Lista produtos associados a um fornecedor específico, com paginação."""
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Verificar se o fornecedor existe
        cursor.execute("SELECT id, nome FROM fornecedor WHERE id = ?", (fornecedor_id,))
        fornecedor_info = cursor.fetchone()
        if not fornecedor_info:
            return jsonify({"error": "Fornecedor não encontrado."}), 404

        page = request.args.get("page", 1, type=int)
        per_page = request.args.get(
            "per_page", 5, type=int
        )  # Menos produtos por página no modal

        # Contar total de produtos do fornecedor
        cursor.execute(
            "SELECT COUNT(id) FROM produto WHERE fornecedor_id = ?", (fornecedor_id,)
        )
        total_produtos = cursor.fetchone()[0]
        total_pages = (total_produtos + per_page - 1) // per_page if per_page > 0 else 1

        # Buscar produtos paginados com nome da categoria
        sql_produtos = """
            SELECT p.id, p.codigo, p.nome, p.preco, p.preco_compra, p.estoque, c.nome as categoria_nome
            FROM produto p
            LEFT JOIN categoria c ON p.categoria_id = c.id
            WHERE p.fornecedor_id = ?
            ORDER BY p.nome ASC
            LIMIT ? OFFSET ?
        """
        params_produtos = (fornecedor_id, per_page, (page - 1) * per_page)
        cursor.execute(sql_produtos, params_produtos)
        produtos_rows = cursor.fetchall()
        produtos_list = [dict(p) for p in produtos_rows]

        return jsonify(
            {
                "fornecedor": dict(fornecedor_info),
                "produtos": produtos_list,
                "total": total_produtos,
                "pages": total_pages,
                "page": page,
                "per_page": per_page,
            }
        )

    except sqlite3.Error as e:
        current_app.logger.error(
            f"Erro ao buscar produtos do fornecedor {fornecedor_id}: {e}", exc_info=True
        )
        return (
            jsonify(
                {"error": "Erro no banco de dados ao buscar produtos do fornecedor."}
            ),
            500,
        )
    except Exception as e:
        current_app.logger.error(
            f"Erro inesperado ao buscar produtos do fornecedor {fornecedor_id}: {e}",
            exc_info=True,
        )
        return jsonify({"error": "Erro inesperado no servidor."}), 500
    finally:
        if conn:
            conn.close()


@fornecedores_bp.route("/<int:fornecedor_id>/alternar-status", methods=["POST"])
@login_required
@acesso_requerido(["admin", "gerente"])
def alternar_status_fornecedor(fornecedor_id):
    """Alterna o status (ativo/inativo) de um fornecedor."""
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT ativo FROM fornecedor WHERE id = ?", (fornecedor_id,))
        fornecedor_status = cursor.fetchone()
        if not fornecedor_status:
            return jsonify({"error": "Fornecedor não encontrado."}), 404

        novo_status = not fornecedor_status["ativo"]

        cursor.execute(
            "UPDATE fornecedor SET ativo = ?, ultima_atualizacao = CURRENT_TIMESTAMP WHERE id = ?",
            (novo_status, fornecedor_id),
        )
        conn.commit()

        return jsonify(
            {
                "message": f"Status do fornecedor alterado para {'ativo' if novo_status else 'inativo'}.",
                "ativo": novo_status,
            }
        )

    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        current_app.logger.error(
            f"Erro ao alternar status do fornecedor {fornecedor_id}: {e}", exc_info=True
        )
        return jsonify({"error": "Erro no banco de dados ao alternar status."}), 500
    except Exception as e:
        if conn:
            conn.rollback()
        current_app.logger.error(
            f"Erro inesperado ao alternar status do fornecedor {fornecedor_id}: {e}",
            exc_info=True,
        )
        return jsonify({"error": "Erro inesperado no servidor."}), 500
    finally:
        if conn:
            conn.close()


# --- Rotas de Página HTML (se aplicável) ---
# Geralmente, a listagem e formulários são carregados via JS que consome as APIs acima.
# Estas rotas apenas servem o template base.


@fornecedores_bp.route("/page", methods=["GET"])
@login_required
def fornecedores_page_html():
    """Renderiza a página principal de fornecedores."""
    return render_template("fornecedores.html")


# Se você tiver páginas separadas para adicionar/editar (não apenas modais):
@fornecedores_bp.route("/adicionar/page", methods=["GET"])
@login_required
@acesso_requerido(["admin", "gerente"])
def adicionar_fornecedor_page_html():
    """Renderiza a página/formulário para adicionar um novo fornecedor."""
    # Esta rota pode não ser necessária se a adição for feita via modal na página principal.
    return render_template(
        "adicionar_fornecedor.html"
    )  # Exemplo, crie este template se necessário


@fornecedores_bp.route("/editar/<int:fornecedor_id>/page", methods=["GET"])
@login_required
@acesso_requerido(["admin", "gerente"])
def editar_fornecedor_page_html(fornecedor_id):
    """Renderiza a página/formulário para editar um fornecedor."""
    # Esta rota pode não ser necessária se a edição for feita via modal.
    # Se usada, buscaria os dados do fornecedor aqui para passar ao template.
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM fornecedor WHERE id = ?", (fornecedor_id,))
        fornecedor = cursor.fetchone()
        if not fornecedor:
            flash("Fornecedor não encontrado.", "danger")
            return redirect(url_for("fornecedores.fornecedores_page_html_html"))
        return render_template(
            "editar_fornecedor.html", fornecedor=dict(fornecedor)
        )  # Exemplo
    except Exception as e:
        flash("Erro ao carregar dados do fornecedor para edição.", "danger")
        current_app.logger.error(
            f"Erro ao carregar fornecedor {fornecedor_id} para edição: {e}",
            exc_info=True,
        )
        return redirect(url_for("fornecedores.fornecedores_page_html_html"))
    finally:
        if conn:
            conn.close()
