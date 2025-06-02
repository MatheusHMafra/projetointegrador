import sqlite3
import os
import uuid  # Para gerar códigos de produto e nomes de arquivo únicos
import datetime  # Para manipulação de datas
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
from database_utils import (
    get_db,
    registrar_movimento,
    buscar_produtos,
)  # Funções de utilidade do banco
from auth import (
    login_required,
    acesso_requerido,
)  # Decoradores de autenticação/autorização
from werkzeug.utils import secure_filename  # Para segurança de nomes de arquivo

# Configuração para uploads de imagens
UPLOAD_FOLDER = os.path.join("static", "uploads", "produtos")  # Caminho mais robusto
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

# Criar Blueprint para produtos
produtos_bp = Blueprint("produtos", __name__, url_prefix="/produtos")


def allowed_file(filename):
    """Verifica se a extensão do arquivo é permitida."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# --- API para Categorias ---
@produtos_bp.route("/categorias", methods=["GET", "POST"])
@login_required
def gerenciar_categorias():
    """
    GET: Lista todas as categorias com contagem de produtos.
    POST: Adiciona uma nova categoria.
    """
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        if request.method == "GET":
            # Query otimizada para buscar categorias e contagem de produtos associados
            cursor.execute(
                """
                SELECT c.id, c.nome, c.descricao, COUNT(p.id) as total_produtos
                FROM categoria c
                LEFT JOIN produto p ON c.id = p.categoria_id
                GROUP BY c.id, c.nome, c.descricao
                ORDER BY c.nome
            """
            )
            categorias_rows = cursor.fetchall()
            resultado = [dict(row) for row in categorias_rows]
            return jsonify(resultado)

        elif request.method == "POST":
            if session.get("user_level") not in ["admin", "gerente"]:
                return (
                    jsonify({"error": "Permissão negada para adicionar categoria."}),
                    403,
                )

            data = request.json
            nome = data.get("nome", "").strip()
            descricao = data.get("descricao", "").strip()

            if not nome:
                return jsonify({"error": "Nome da categoria é obrigatório."}), 400

            cursor.execute("SELECT id FROM categoria WHERE nome = ?", (nome,))
            if cursor.fetchone():
                return (
                    jsonify({"error": "Já existe uma categoria com este nome."}),
                    409,
                )  # Conflict

            cursor.execute(
                "INSERT INTO categoria (nome, descricao) VALUES (?, ?)",
                (nome, descricao),
            )
            categoria_id = cursor.lastrowid
            conn.commit()

            return (
                jsonify(
                    {
                        "message": "Categoria adicionada com sucesso!",
                        "categoria": {
                            "id": categoria_id,
                            "nome": nome,
                            "descricao": descricao,
                            "total_produtos": 0,
                        },
                    }
                ),
                201,
            )

    except sqlite3.Error as e:
        if conn and request.method == "POST":
            conn.rollback()
        current_app.logger.error(
            f"Erro de banco de dados em categorias: {e}", exc_info=True
        )
        return jsonify({"error": "Erro no banco de dados."}), 500
    except Exception as e:
        if conn and request.method == "POST":
            conn.rollback()
        current_app.logger.error(f"Erro inesperado em categorias: {e}", exc_info=True)
        return jsonify({"error": "Erro inesperado no servidor."}), 500
    finally:
        if conn:
            conn.close()


@produtos_bp.route("/categorias/<int:categoria_id>", methods=["GET", "PUT", "DELETE"])
@login_required
def gerenciar_categoria_especifica(categoria_id):
    """
    GET: Retorna detalhes de uma categoria e seus produtos.
    PUT: Atualiza uma categoria.
    DELETE: Exclui uma categoria.
    """
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, nome, descricao FROM categoria WHERE id = ?", (categoria_id,)
        )
        categoria_data = cursor.fetchone()

        if not categoria_data:
            return jsonify({"error": "Categoria não encontrada."}), 404

        if request.method == "GET":
            cursor.execute(
                "SELECT id, nome, codigo, preco, estoque FROM produto WHERE categoria_id = ? ORDER BY nome",
                (categoria_id,),
            )
            produtos_rows = cursor.fetchall()
            return jsonify(
                {
                    "id": categoria_data["id"],
                    "nome": categoria_data["nome"],
                    "descricao": categoria_data["descricao"],
                    "produtos": [dict(p) for p in produtos_rows],
                }
            )

        elif request.method == "PUT":
            if session.get("user_level") not in ["admin", "gerente"]:
                return (
                    jsonify({"error": "Permissão negada para atualizar categoria."}),
                    403,
                )

            data = request.json
            novo_nome = data.get("nome", "").strip()
            nova_descricao = data.get("descricao", "").strip()

            if not novo_nome:
                return (
                    jsonify(
                        {"error": "Nome da categoria é obrigatório para atualização."}
                    ),
                    400,
                )

            if novo_nome != categoria_data["nome"]:
                cursor.execute(
                    "SELECT id FROM categoria WHERE nome = ? AND id != ?",
                    (novo_nome, categoria_id),
                )
                if cursor.fetchone():
                    return (
                        jsonify({"error": "Já existe outra categoria com este nome."}),
                        409,
                    )
            # Assuming 'ultima_atualizacao' column exists in 'categoria' table
            # If not, this part of the query will cause an error.
            # For now, let's assume it exists or will be added.
            # If it doesn't exist, remove ", ultima_atualizacao = CURRENT_TIMESTAMP"
            try:
                cursor.execute(
                    "UPDATE categoria SET nome = ?, descricao = ?, ultima_atualizacao = CURRENT_TIMESTAMP WHERE id = ?",
                    (novo_nome, nova_descricao, categoria_id),
                )
            except sqlite3.OperationalError as oe:
                 if "no such column: ultima_atualizacao" in str(oe):
                      cursor.execute(
                        "UPDATE categoria SET nome = ?, descricao = ? WHERE id = ?",
                        (novo_nome, nova_descricao, categoria_id),
                    )
                 else:
                      raise # re-raise other operational errors
            conn.commit()
            return jsonify(
                {
                    "message": "Categoria atualizada com sucesso!",
                    "categoria": {
                        "id": categoria_id,
                        "nome": novo_nome,
                        "descricao": nova_descricao,
                    },
                }
            )

        elif request.method == "DELETE":
            if session.get("user_level") not in ["admin"]:  # Apenas admin pode excluir
                return (
                    jsonify({"error": "Permissão negada para excluir categoria."}),
                    403,
                )

            cursor.execute(
                "SELECT COUNT(id) FROM produto WHERE categoria_id = ?", (categoria_id,)
            )
            if cursor.fetchone()[0] > 0:
                return (
                    jsonify(
                        {
                            "error": "Não é possível excluir. Existem produtos associados a esta categoria."
                        }
                    ),
                    400,
                )

            cursor.execute("DELETE FROM categoria WHERE id = ?", (categoria_id,))
            conn.commit()
            return jsonify({"message": "Categoria excluída com sucesso."})

    except sqlite3.Error as e:
        if conn and request.method in ["PUT", "DELETE"]:
            conn.rollback()
        current_app.logger.error(
            f"Erro de BD na categoria ID {categoria_id}: {e}", exc_info=True
        )
        return jsonify({"error": "Erro no banco de dados."}), 500
    except Exception as e:
        if conn and request.method in ["PUT", "DELETE"]:
            conn.rollback()
        current_app.logger.error(
            f"Erro inesperado na categoria ID {categoria_id}: {e}", exc_info=True
        )
        return jsonify({"error": "Erro inesperado no servidor."}), 500
    finally:
        if conn:
            conn.close()


# --- API para Produtos ---
@produtos_bp.route("/", methods=["GET", "POST"])
@login_required
def gerenciar_todos_produtos():
    """
    GET: Lista produtos com filtros, paginação e ordenação.
    POST: Adiciona um novo produto.
    """
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        if request.method == "GET":
            # Parâmetros da requisição GET
            page = request.args.get("page", 1, type=int)
            per_page = request.args.get("per_page", 15, type=int)  # Aumentado padrão
            categoria_id_filter = request.args.get("categoria_id", type=int)
            fornecedor_id_filter = request.args.get("fornecedor_id", type=int)
            termo_busca = request.args.get(
                "termo"
            )  # Para buscar por nome, código, descrição
            estoque_baixo_filter = (
                request.args.get("estoque_baixo", "").lower() == "true"
            )
            ordenar_por = request.args.get(
                "ordenar_por", "p.nome"
            )  # Ex: 'p.nome', 'p.preco', 'p.estoque'
            direcao_ordem = request.args.get("direcao", "asc").upper()  # ASC ou DESC

            # A função buscar_produtos de database_utils já lida com a lógica complexa de busca
            resultado_busca = buscar_produtos(
                termo=termo_busca,
                categoria_id=categoria_id_filter,
                fornecedor_id=fornecedor_id_filter,
                estoque_baixo=estoque_baixo_filter,
                page=page,
                per_page=per_page,
                ordenar_por=ordenar_por,
                direcao=direcao_ordem,
            )
            return jsonify(resultado_busca)

        elif request.method == "POST":
            if session.get("user_level") not in ["admin", "gerente"]:
                return (
                    jsonify({"error": "Permissão negada para adicionar produto."}),
                    403,
                )

            # Lida com 'multipart/form-data' (com arquivo) ou 'application/json'
            if request.content_type.startswith("multipart/form-data"):
                data = request.form
                file = request.files.get("imagem")
            elif request.content_type.startswith("application/json"):
                data = request.json
                file = None  # Imagem via URL no JSON, se houver
            else:
                return (
                    jsonify(
                        {
                            "error": "Content-Type não suportado. Use multipart/form-data ou application/json."
                        }
                    ),
                    415,
                )

            # Extração e validação de dados
            nome = data.get("nome", "").strip()
            codigo = (
                data.get("codigo", "").strip() or f"PROD-{uuid.uuid4().hex[:6].upper()}"
            )  # Gera código se não fornecido
            categoria_id_str = data.get("categoria_id")
            preco_str = data.get("preco")

            if not all([nome, categoria_id_str, preco_str]):
                return (
                    jsonify(
                        {"error": "Nome, Categoria e Preço de Venda são obrigatórios."}
                    ),
                    400,
                )

            try:
                categoria_id = int(categoria_id_str)
                preco = float(preco_str)
                preco_compra = (
                    float(data.get("preco_compra"))
                    if data.get("preco_compra")
                    else None
                )
                estoque = int(data.get("estoque", 0))
                estoque_minimo = int(data.get("estoque_minimo", 5))
                fornecedor_id = (
                    int(data.get("fornecedor_id"))
                    if data.get("fornecedor_id")
                    else None
                )
            except (ValueError, TypeError) as e:
                return jsonify({"error": f"Valores numéricos inválidos: {e}"}), 400

            descricao = data.get("descricao", "").strip()
            imagem_url = (
                data.get("imagem_url") if not file else None
            )  # Prioriza arquivo se ambos forem enviados

            # Validar existência de categoria e fornecedor
            cursor.execute("SELECT id FROM categoria WHERE id = ?", (categoria_id,))
            if not cursor.fetchone():
                return (
                    jsonify(
                        {"error": f"Categoria com ID {categoria_id} não encontrada."}
                    ),
                    404,
                )
            if fornecedor_id:
                # Corrected table name
                cursor.execute(
                    "SELECT id FROM fornecedores WHERE id = ?", (fornecedor_id,)
                )
                if not cursor.fetchone():
                    return (
                        jsonify(
                            {
                                "error": f"Fornecedor com ID {fornecedor_id} não encontrado."
                            }
                        ),
                        404,
                    )

            # Verificar se código do produto já existe
            cursor.execute("SELECT id FROM produto WHERE codigo = ?", (codigo,))
            if cursor.fetchone():
                return (
                    jsonify({"error": f"Código de produto '{codigo}' já existe."}),
                    409,
                )

            # Processar imagem, se houver
            if file and allowed_file(file.filename):
                os.makedirs(
                    UPLOAD_FOLDER, exist_ok=True
                )  # Garante que o diretório exista
                filename_secure = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename_secure}"
                filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
                try:
                    file.save(filepath)
                    imagem_url = f"/{filepath.replace(os.sep, '/')}"  # URL relativa
                except Exception as e_file:
                    current_app.logger.error(
                        f"Erro ao salvar imagem: {e_file}", exc_info=True
                    )
                    # Continuar sem imagem ou retornar erro? Decidido continuar sem.
                    imagem_url = None

            # Inserir produto
            sql_insert_prod = """
                INSERT INTO produto (codigo, nome, descricao, categoria_id, fornecedor_id, preco, preco_compra, estoque, estoque_minimo, imagem_url, data_criacao, ultima_atualizacao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
            params_insert = (
                codigo,
                nome,
                descricao,
                categoria_id,
                fornecedor_id,
                preco,
                preco_compra,
                estoque,
                estoque_minimo,
                imagem_url,
            )
            cursor.execute(sql_insert_prod, params_insert)
            produto_id = cursor.lastrowid
            conn.commit()

            # Registrar movimento de estoque inicial, se houver estoque
            if estoque > 0:
                try:
                    registrar_movimento(
                        produto_id=produto_id,
                        tipo="entrada",
                        quantidade=estoque,
                        usuario_id=session.get("user_id"),
                        observacao="Estoque inicial (cadastro de produto)",
                    )
                except Exception as e_mov:  # Captura erros de registrar_movimento
                    current_app.logger.warning(
                        f"Falha ao registrar movimento inicial para produto ID {produto_id}: {e_mov}"
                    )
                    # Não reverter a criação do produto, apenas logar o aviso.

            return (
                jsonify(
                    {
                        "message": "Produto adicionado com sucesso!",
                        "produto": {
                            "id": produto_id,
                            "codigo": codigo,
                            "nome": nome,
                            "estoque": estoque,
                        },
                    }
                ),
                201,
            )

    except sqlite3.Error as e:
        if conn and request.method == "POST":
            conn.rollback()
        current_app.logger.error(f"Erro de BD em produtos: {e}", exc_info=True)
        return jsonify({"error": "Erro no banco de dados."}), 500
    except Exception as e:
        if conn and request.method == "POST":
            conn.rollback()
        current_app.logger.error(f"Erro inesperado em produtos: {e}", exc_info=True)
        return jsonify({"error": "Erro inesperado no servidor."}), 500
    finally:
        if conn:
            conn.close()


@produtos_bp.route("/<int:produto_id>", methods=["GET", "PUT", "DELETE"])
@login_required
def gerenciar_produto_especifico(produto_id):
    """
    GET: Retorna detalhes de um produto.
    PUT: Atualiza um produto.
    DELETE: Exclui um produto.
    """
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Função auxiliar para buscar o produto com joins
        def fetch_produto_completo(pid):
            # Corrected table name for join
            cursor.execute(
                """
                SELECT p.*, c.nome as categoria_nome, f.nome as fornecedor_nome
                FROM produto p
                LEFT JOIN categoria c ON p.categoria_id = c.id
                LEFT JOIN fornecedores f ON p.fornecedor_id = f.id
                WHERE p.id = ?
            """,
                (pid,),
            )
            return cursor.fetchone()

        produto_data_row = fetch_produto_completo(produto_id)
        if not produto_data_row:
            return jsonify({"error": "Produto não encontrado."}), 404

        produto_dict_orig = dict(produto_data_row)  # Original para referência

        if request.method == "GET":
            # Formatar data para exibição
            try:
                # Ensure data_criacao is not None and is a string before formatting
                if produto_dict_orig.get("data_criacao"):
                    dt_obj = datetime.datetime.fromisoformat(
                        str(produto_dict_orig["data_criacao"])
                    )
                    produto_dict_orig["data_criacao_fmt"] = dt_obj.strftime(
                        "%d/%m/%Y %H:%M"
                    )
                else:
                    produto_dict_orig["data_criacao_fmt"] = "N/A"
            except (ValueError, TypeError): # Catch potential errors if data_criacao is not a valid ISO format string
                produto_dict_orig["data_criacao_fmt"] = str(
                    produto_dict_orig.get("data_criacao", "N/A") # Fallback
                )
            return jsonify(produto_dict_orig)

        elif request.method == "PUT":
            if session.get("user_level") not in ["admin", "gerente"]:
                return (
                    jsonify({"error": "Permissão negada para atualizar produto."}),
                    403,
                )

            if request.content_type.startswith("multipart/form-data"):
                data = request.form
                file = request.files.get("imagem")
            elif request.content_type.startswith("application/json"):
                data = request.json
                file = None
            else:
                return jsonify({"error": "Content-Type não suportado."}), 415

            update_fields_sql = []
            params_update = []

            # Campos permitidos para atualização
            # Estoque não é atualizado diretamente aqui, mas por movimentação.
            allowed_fields = [
                "nome",
                "codigo",
                "descricao",
                "categoria_id",
                "fornecedor_id",
                "preco",
                "preco_compra",
                "estoque_minimo",
                "imagem_url",
            ]

            for field in allowed_fields:
                if field in data:
                    value = data.get(field)
                    # Validação de código único se estiver sendo alterado
                    if field == "codigo" and value != produto_dict_orig["codigo"]:
                        cursor.execute(
                            "SELECT id FROM produto WHERE codigo = ? AND id != ?",
                            (value, produto_id),
                        )
                        if cursor.fetchone():
                            return (
                                jsonify(
                                    {"error": f"Código de produto '{value}' já existe."}
                                ),
                                409,
                            )

                    # Validação de IDs de categoria/fornecedor
                    if field == "categoria_id" and value:
                        cursor.execute(
                            "SELECT id FROM categoria WHERE id = ?", (int(value),)
                        )
                        if not cursor.fetchone():
                            return (
                                jsonify(
                                    {"error": f"Categoria ID {value} não encontrada."}
                                ),
                                404,
                            )
                    if field == "fornecedor_id" and value:  # Fornecedor pode ser None
                        # Corrected table name
                        cursor.execute(
                            "SELECT id FROM fornecedores WHERE id = ?", (int(value),)
                        )
                        if not cursor.fetchone():
                            return (
                                jsonify(
                                    {"error": f"Fornecedor ID {value} não encontrado."}
                                ),
                                404,
                            )

                    update_fields_sql.append(f"{field} = ?")
                    # Converter para tipos corretos antes de adicionar aos params
                    if field in ["preco", "preco_compra"] and value is not None:
                        try:
                            params_update.append(float(value))
                        except ValueError:
                             return jsonify({"error": f"Valor inválido para {field}."}), 400
                    elif (
                        field in ["categoria_id", "fornecedor_id", "estoque_minimo"]
                        and value is not None
                    ):
                        try:
                            params_update.append(int(value) if value else None)
                        except ValueError:
                            return jsonify({"error": f"Valor inválido para {field}."}), 400
                    else:
                        params_update.append(
                            value.strip() if isinstance(value, str) else value
                        )

            # Processar nova imagem, se enviada
            if file and allowed_file(file.filename):
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                filename_secure = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename_secure}"
                filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
                try:
                    file.save(filepath)
                    # Se uma imagem antiga existir e for diferente, excluí-la (opcional)
                    if produto_dict_orig.get("imagem_url"):
                        old_image_path_relative = produto_dict_orig["imagem_url"].lstrip("/")
                        old_image_path_full = os.path.join(current_app.root_path, old_image_path_relative)
                        if os.path.exists(old_image_path_full) and UPLOAD_FOLDER in old_image_path_full:
                            if (
                                produto_dict_orig["imagem_url"]
                                != f"/{filepath.replace(os.sep, '/')}"
                            ): 
                                try:
                                    os.remove(old_image_path_full)
                                    current_app.logger.info(f"Imagem antiga {old_image_path_full} excluída.")
                                except OSError as e_rm:
                                    current_app.logger.error(f"Erro ao remover imagem antiga {old_image_path_full}: {e_rm}")


                    update_fields_sql.append("imagem_url = ?")
                    params_update.append(f"/{filepath.replace(os.sep, '/')}")
                except Exception as e_file:
                    current_app.logger.error(
                        f"Erro ao salvar nova imagem para produto {produto_id}: {e_file}",
                        exc_info=True,
                    )
            elif (
                "imagem_url" in data
                and data["imagem_url"] is None
                and "imagem_url = ?" not in " ".join(update_fields_sql) # Check if not already set to be updated
            ): 
                update_fields_sql.append("imagem_url = ?")
                params_update.append(None)
                 # Excluir imagem antiga se a URL for definida como None
                if produto_dict_orig.get("imagem_url"):
                    old_image_path_relative = produto_dict_orig["imagem_url"].lstrip("/")
                    old_image_path_full = os.path.join(current_app.root_path, old_image_path_relative)
                    if os.path.exists(old_image_path_full) and UPLOAD_FOLDER in old_image_path_full:
                        try:
                            os.remove(old_image_path_full)
                            current_app.logger.info(f"Imagem antiga {old_image_path_full} excluída ao setar imagem_url para None.")
                        except OSError as e_rm:
                            current_app.logger.error(f"Erro ao remover imagem antiga {old_image_path_full}: {e_rm}")


            if not update_fields_sql:
                return jsonify({"message": "Nenhuma alteração válida fornecida."})

            update_fields_sql.append("ultima_atualizacao = CURRENT_TIMESTAMP")
            params_update.append(produto_id)  # Para a cláusula WHERE

            sql_update_prod = (
                f"UPDATE produto SET {', '.join(update_fields_sql)} WHERE id = ?"
            )
            cursor.execute(sql_update_prod, params_update)
            conn.commit()

            produto_atualizado_dict = dict(fetch_produto_completo(produto_id))
            return jsonify(
                {
                    "message": "Produto atualizado com sucesso!",
                    "produto": produto_atualizado_dict,
                }
            )

        elif request.method == "DELETE":
            if session.get("user_level") not in ["admin"]:
                return jsonify({"error": "Permissão negada para excluir produto."}), 403

            # Verificar movimentos de estoque ou vendas associadas
            cursor.execute(
                "SELECT COUNT(id) FROM estoque_movimentacao WHERE produto_id = ?", # Corrected table name
                (produto_id,),
            )
            if cursor.fetchone()[0] > 0:
                return (
                    jsonify(
                        {
                            "error": "Não é possível excluir. Produto possui histórico de movimentações."
                        }
                    ),
                    400,
                )

            # Adicional: Verificar se está em alguma venda (item_venda)
            try:
                cursor.execute(
                    "SELECT COUNT(id) FROM item_venda WHERE produto_id = ?",
                    (produto_id,),
                )
                if cursor.fetchone()[0] > 0:
                    return (
                        jsonify(
                            {
                                "error": "Não é possível excluir. Produto está associado a vendas."
                            }
                        ),
                        400,
                    )
            except sqlite3.OperationalError as e_item_venda:
                # Se a tabela item_venda não existir, ignora o erro e continua
                if "no such table" not in str(e_item_venda).lower():
                    raise  # Relança outros erros de SQL
                current_app.logger.warning(
                    "Tabela item_venda não encontrada, pulando verificação de vendas para exclusão de produto."
                )

            # Excluir imagem do disco se existir
            imagem_a_excluir = produto_dict_orig.get("imagem_url")
            if imagem_a_excluir:
                try:
                    path_relativa_app = imagem_a_excluir.lstrip("/")
                    caminho_completo_imagem = os.path.join(
                        current_app.root_path, path_relativa_app
                    )

                    if (
                        os.path.exists(caminho_completo_imagem)
                        and UPLOAD_FOLDER in caminho_completo_imagem # Security check
                    ):
                        os.remove(caminho_completo_imagem)
                        current_app.logger.info(
                            f"Imagem {caminho_completo_imagem} excluída para produto ID {produto_id}."
                        )
                except Exception as img_err:
                    current_app.logger.error(
                        f"Falha ao excluir imagem {imagem_a_excluir} para produto ID {produto_id}: {img_err}",
                        exc_info=True,
                    )

            cursor.execute("DELETE FROM produto WHERE id = ?", (produto_id,))
            conn.commit()
            return jsonify({"message": "Produto excluído com sucesso."})

    except sqlite3.Error as e:
        if conn and request.method in ["PUT", "DELETE", "POST"]:
            conn.rollback()
        current_app.logger.error(
            f"Erro de BD no produto ID {produto_id if request.method != 'POST' else 'novo'}: {e}",
            exc_info=True,
        )
        return jsonify({"error": "Erro no banco de dados."}), 500
    except Exception as e:
        if conn and request.method in ["PUT", "DELETE", "POST"]:
            conn.rollback()
        current_app.logger.error(
            f"Erro inesperado no produto ID {produto_id if request.method != 'POST' else 'novo'}: {e}",
            exc_info=True,
        )
        return jsonify({"error": "Erro inesperado no servidor."}), 500
    finally:
        if conn:
            conn.close()


# --- Rotas de Relatórios de Produtos (Mais/Menos Vendidos) ---
# Estas rotas dependem da existência da tabela 'item_venda'.


@produtos_bp.route("/mais-vendidos", methods=["GET"])
@login_required
@acesso_requerido(["admin", "gerente"])
def relatorio_produtos_mais_vendidos():
    """Retorna uma lista paginada dos produtos mais vendidos."""
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        # Query para contar o total de produtos distintos que foram vendidos
        count_query = "SELECT COUNT(DISTINCT p.id) FROM produto p JOIN item_venda iv ON p.id = iv.produto_id"
        cursor.execute(count_query)
        total_items = cursor.fetchone()[0]
        total_pages = (total_items + per_page - 1) // per_page if per_page > 0 else 1

        # Query principal
        query = """
            SELECT p.id, p.codigo, p.nome, c.nome as categoria_nome, SUM(iv.quantidade) as total_vendido
            FROM produto p
            LEFT JOIN categoria c ON p.categoria_id = c.id
            JOIN item_venda iv ON p.id = iv.produto_id
            GROUP BY p.id, p.codigo, p.nome, c.nome
            ORDER BY total_vendido DESC
            LIMIT ? OFFSET ?
        """
        params = (per_page, (page - 1) * per_page)
        cursor.execute(query, params)
        produtos_rows = cursor.fetchall()

        return jsonify(
            {
                "produtos": [dict(row) for row in produtos_rows],
                "total": total_items,
                "pages": total_pages,
                "page": page,
                "per_page": per_page,
            }
        )
    except sqlite3.OperationalError as e:
        if "no such table: item_venda" in str(e).lower():
            return (
                jsonify(
                    {
                        "error": "Funcionalidade indisponível: tabela 'item_venda' não encontrada."
                    }
                ),
                501,
            )  # Not Implemented
        current_app.logger.error(f"Erro de BD em mais-vendidos: {e}", exc_info=True)
        return jsonify({"error": "Erro no banco de dados."}), 500
    except Exception as e:
        current_app.logger.error(
            f"Erro inesperado em mais-vendidos: {e}", exc_info=True
        )
        return jsonify({"error": "Erro inesperado no servidor."}), 500
    finally:
        if conn:
            conn.close()


@produtos_bp.route("/menos-vendidos", methods=["GET"])
@login_required
@acesso_requerido(["admin", "gerente"])
def relatorio_produtos_menos_vendidos():
    """Retorna uma lista paginada dos produtos menos vendidos (incluindo os não vendidos)."""
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        count_query = "SELECT COUNT(id) FROM produto"  # Todos os produtos
        cursor.execute(count_query)
        total_items = cursor.fetchone()[0]
        total_pages = (total_items + per_page - 1) // per_page if per_page > 0 else 1

        query = """
            SELECT p.id, p.codigo, p.nome, c.nome as categoria_nome, COALESCE(SUM(iv.quantidade), 0) as total_vendido
            FROM produto p
            LEFT JOIN categoria c ON p.categoria_id = c.id
            LEFT JOIN item_venda iv ON p.id = iv.produto_id
            GROUP BY p.id, p.codigo, p.nome, c.nome
            ORDER BY total_vendido ASC, p.nome ASC
            LIMIT ? OFFSET ?
        """
        params = (per_page, (page - 1) * per_page)
        cursor.execute(query, params)
        produtos_rows = cursor.fetchall()

        return jsonify(
            {
                "produtos": [dict(row) for row in produtos_rows],
                "total": total_items,
                "pages": total_pages,
                "page": page,
                "per_page": per_page,
            }
        )
    except sqlite3.OperationalError as e:
        if "no such table: item_venda" in str(e).lower():
            # Se item_venda não existe, ainda podemos listar produtos, mas total_vendido será sempre 0.
            # Adaptar a query para não depender de item_venda ou retornar erro.
            # Por ora, retornando erro para indicar que a funcionalidade completa não está disponível.
            return (
                jsonify(
                    {
                        "error": "Funcionalidade de menos vendidos (com contagem) indisponível: tabela 'item_venda' não encontrada."
                    }
                ),
                501,
            )
        current_app.logger.error(f"Erro de BD em menos-vendidos: {e}", exc_info=True)
        return jsonify({"error": "Erro no banco de dados."}), 500
    except Exception as e:
        current_app.logger.error(
            f"Erro inesperado em menos-vendidos: {e}", exc_info=True
        )
        return jsonify({"error": "Erro inesperado no servidor."}), 500
    finally:
        if conn:
            conn.close()


# --- Rota para busca de produtos (delegada para database_utils.buscar_produtos) ---
@produtos_bp.route("/busca", methods=["GET"])
@login_required
def api_busca_produto():
    """Endpoint de API para busca avançada de produtos."""
    try:
        # Coleta e validação de parâmetros de busca
        termo = request.args.get("termo")
        categoria_id = request.args.get("categoria_id", type=int)
        fornecedor_id = request.args.get("fornecedor_id", type=int)
        estoque_baixo = request.args.get("estoque_baixo", "false").lower() == "true"
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 15, type=int)
        ordenar_por = request.args.get("ordenar_por", "p.nome")
        direcao = request.args.get("direcao", "ASC")

        # Chama a função de utilidade que contém a lógica de busca
        resultado = buscar_produtos(
            termo=termo,
            categoria_id=categoria_id,
            fornecedor_id=fornecedor_id,
            estoque_baixo=estoque_baixo,
            page=page,
            per_page=per_page,
            ordenar_por=ordenar_por,
            direcao=direcao,
        )
        return jsonify(resultado)
    except Exception as e:
        current_app.logger.error(
            f"Erro na API de busca de produtos: {e}", exc_info=True
        )
        return jsonify({"error": "Erro ao processar a busca de produtos."}), 500


# --- Rotas de Página HTML (se necessário) ---
@produtos_bp.route("/page", methods=["GET"])
@login_required
def produtos_page_html():
    """Renderiza a página principal de produtos."""
    return render_template("produtos.html")


# Rota para adicionar produto (página HTML, se for separada do modal)
@produtos_bp.route('/adicionar', methods=['GET']) # Removido POST, pois o POST é para a API /produtos/
@login_required
@acesso_requerido(['admin', 'gerente'])
def adicionar_produto(): # Renomeado para evitar conflito com a API
    # Esta rota renderiza o formulário. A submissão do formulário deve ir para a API /produtos (POST)
    # Se o formulário estiver em um modal na página principal de produtos, esta rota pode não ser necessária.
    # Se for uma página separada:
    # return render_template('adicionar_produto_form.html') # Certifique-se que este template existe
    # Por enquanto, vamos assumir que a adição é via modal em produtos.html, então esta rota pode ser redundante
    # ou redirecionar para a página principal de produtos se não houver um form dedicado.
    flash("Para adicionar produtos, use o modal na página de listagem.", "info")
    return redirect(url_for('produtos.produtos_page_html'))

