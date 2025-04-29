import sqlite3
import os
import uuid
import datetime
from flask import Blueprint, request, jsonify, render_template, session, flash, redirect, url_for
from database_utils import buscar_produtos, get_db, registrar_movimento
from auth import login_required, acesso_requerido
from werkzeug.utils import secure_filename

from fornecedores import dict_factory

# Configuração para uploads de imagens
UPLOAD_FOLDER = 'static/uploads/produtos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Criar Blueprint para produtos e categorias
# Adicionado url_prefix
produtos_bp = Blueprint('produtos', __name__, url_prefix='/produtos')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- API para categorias ---


@produtos_bp.route('/categorias', methods=['GET', 'POST'])
@login_required
def categorias():
    conn = None  # Inicializa conn para garantir que exista no finally
    try:
        conn = get_db()
        cursor = conn.cursor()

        if request.method == 'GET':
            cursor.execute(
                "SELECT id, nome, descricao FROM categoria ORDER BY nome")
            categorias_rows = cursor.fetchall()

            resultado = []
            for c in categorias_rows:
                # Contar número de produtos nesta categoria
                cursor.execute(
                    "SELECT COUNT(*) FROM produto WHERE categoria_id = ?", (c['id'],))
                total_produtos = cursor.fetchone()[0]

                resultado.append({
                    'id': c['id'],
                    'nome': c['nome'],
                    'descricao': c['descricao'],
                    'total_produtos': total_produtos
                })

            return jsonify(resultado)

        elif request.method == 'POST':
            # Verificar permissão
            if session.get('user_level') not in ['admin', 'gerente']:
                return jsonify({"error": "Permissão negada"}), 403

            data = request.json
            nome = data.get('nome')
            descricao = data.get('descricao', '')

            if not nome:
                return jsonify({"error": "Nome da categoria é obrigatório"}), 400

            # Verificar se já existe uma categoria com este nome
            cursor.execute("SELECT id FROM categoria WHERE nome = ?", (nome,))
            if cursor.fetchone():
                return jsonify({"error": "Já existe uma categoria com este nome"}), 400

            cursor.execute(
                "INSERT INTO categoria (nome, descricao) VALUES (?, ?)",
                (nome, descricao)
            )

            categoria_id = cursor.lastrowid
            conn.commit()

            return jsonify({
                "message": "Categoria adicionada com sucesso",
                "categoria": {
                    "id": categoria_id,
                    "nome": nome,
                    "descricao": descricao
                }
            }), 201

    except sqlite3.Error as e:
        if conn:  # Faz rollback apenas se a operação for de escrita e der erro
            if request.method == 'POST':
                conn.rollback()
        # Considerar logar o erro e retornar uma mensagem genérica
        return jsonify({"error": f"Erro no banco de dados: {e}"}), 500
    # finally:
    #     # O fechamento da conexão deve ser gerenciado pelo teardown_appcontext geralmente
    #     pass


# --- API para uma categoria específica ---


@produtos_bp.route('/categorias/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def categoria(id):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Verificar se a categoria existe
        cursor.execute(
            "SELECT id, nome, descricao FROM categoria WHERE id = ?", (id,))
        categoria_data = cursor.fetchone()

        if not categoria_data:
            return jsonify({"error": "Categoria não encontrada"}), 404

        if request.method == 'GET':
            # Buscar produtos desta categoria
            cursor.execute(
                """
                SELECT id, nome, codigo, preco, estoque
                FROM produto
                WHERE categoria_id = ? ORDER BY nome
                """,
                (id,)
            )
            produtos_rows = cursor.fetchall()
            produtos_list = [dict(p)
                             for p in produtos_rows]  # Converter para dict

            return jsonify({
                'id': categoria_data['id'],
                'nome': categoria_data['nome'],
                'descricao': categoria_data['descricao'],
                'produtos': produtos_list
            })

        elif request.method == 'PUT':
            # Verificar permissão
            if session.get('user_level') not in ['admin', 'gerente']:
                return jsonify({"error": "Permissão negada"}), 403

            data = request.json
            novo_nome = data.get('nome')
            nova_descricao = data.get('descricao')

            nome_final = categoria_data['nome']
            descricao_final = categoria_data['descricao']
            needs_update = False

            # Verificar nome duplicado apenas se o nome foi alterado
            if novo_nome and novo_nome != categoria_data['nome']:
                cursor.execute(
                    "SELECT id FROM categoria WHERE nome = ? AND id != ?", (novo_nome, id))
                if cursor.fetchone():
                    return jsonify({"error": "Já existe outra categoria com este nome"}), 400
                nome_final = novo_nome
                needs_update = True

            if nova_descricao is not None and nova_descricao != categoria_data['descricao']:
                descricao_final = nova_descricao
                needs_update = True

            if not needs_update:
                return jsonify({"message": "Nenhuma alteração detectada"})

            cursor.execute(
                "UPDATE categoria SET nome = ?, descricao = ? WHERE id = ?",
                (nome_final, descricao_final, id)
            )
            conn.commit()

            return jsonify({
                "message": "Categoria atualizada com sucesso",
                "categoria": {
                    "id": id,
                    "nome": nome_final,
                    "descricao": descricao_final
                }
            })

        elif request.method == 'DELETE':
            # Verificar permissão
            if session.get('user_level') not in ['admin', 'gerente']:
                return jsonify({"error": "Permissão negada"}), 403

            # Verificar se existem produtos nesta categoria
            cursor.execute(
                "SELECT COUNT(*) FROM produto WHERE categoria_id = ?", (id,))
            total_produtos = cursor.fetchone()[0]

            if total_produtos > 0:
                return jsonify({
                    "error": "Não é possível excluir esta categoria pois existem produtos associados a ela."
                }), 400

            cursor.execute("DELETE FROM categoria WHERE id = ?", (id,))
            conn.commit()

            return jsonify({"message": "Categoria excluída com sucesso"})

    except sqlite3.Error as e:
        if conn:
            if request.method in ['PUT', 'DELETE']:
                conn.rollback()
        return jsonify({"error": f"Erro no banco de dados: {e}"}), 500


# --- API para produtos ---


@produtos_bp.route('/', methods=['GET', 'POST'])
@login_required
def listar_produtos():
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        if request.method == 'GET':
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            categoria_id = request.args.get('categoria_id', type=int)
            # Adicionado filtro fornecedor
            fornecedor_id = request.args.get('fornecedor_id', type=int)

            base_query = """
                SELECT
                    p.id, p.codigo, p.nome, p.descricao, p.preco, p.preco_compra,
                    p.estoque, p.estoque_minimo, p.imagem_url, p.data_criacao,
                    p.categoria_id, c.nome as categoria_nome,
                    p.fornecedor_id, f.nome as fornecedor_nome
                FROM produto p
                LEFT JOIN categoria c ON p.categoria_id = c.id
                LEFT JOIN fornecedor f ON p.fornecedor_id = f.id
            """
            count_base_query = "SELECT COUNT(p.id) FROM produto p"
            where_clauses = []
            params = []
            count_params = []

            if categoria_id:
                where_clauses.append("p.categoria_id = ?")
                params.append(categoria_id)
                count_params.append(categoria_id)

            if fornecedor_id:
                where_clauses.append("p.fornecedor_id = ?")
                params.append(fornecedor_id)
                count_params.append(fornecedor_id)

            # Montar query final
            query = base_query
            count_query = count_base_query
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
                count_query += " WHERE " + " AND ".join(where_clauses)

            # Contar total para paginação
            cursor.execute(count_query, count_params)
            total = cursor.fetchone()[0]
            total_pages = (total + per_page - 1) // per_page if per_page > 0 else 1

            # Adicionar ordenação e paginação
            query += " ORDER BY p.nome LIMIT ? OFFSET ?"
            params.append(per_page)
            params.append((page - 1) * per_page)

            cursor.execute(query, params)
            produtos_rows = cursor.fetchall()

            resultado = []
            for p in produtos_rows:
                resultado.append({
                    "id": p['id'],
                    "codigo": p['codigo'],
                    "nome": p['nome'],
                    "preco": p['preco'],
                    "categoria": {
                        "id": p['categoria_id'],
                        "nome": p['categoria_nome']
                    } if p['categoria_id'] else None,
                    "fornecedor": {  # Adicionado fornecedor
                        "id": p['fornecedor_id'],
                        "nome": p['fornecedor_nome']
                    } if p['fornecedor_id'] else None,
                    "estoque": p['estoque'],
                    "estoque_minimo": p['estoque_minimo'],
                    "imagem_url": p['imagem_url']
                })

            return jsonify({
                "produtos": resultado,
                "total": total,
                "pages": total_pages,
                "page": page,
                "per_page": per_page
            })

        elif request.method == 'POST':
            # Verificar permissão
            if session.get('user_level') not in ['admin', 'gerente']:
                return jsonify({"error": "Permissão negada"}), 403

            nome = None
            categoria_id = None
            preco = None
            preco_compra = None
            estoque = 0
            estoque_minimo = 5
            descricao = ''
            fornecedor_id = None
            imagem_url = None
            file = None

            # Lida com 'multipart/form-data' (com arquivo) ou 'application/json'
            if request.content_type.startswith('multipart/form-data'):
                nome = request.form.get('nome')
                categoria_id = request.form.get('categoria_id')
                preco = request.form.get('preco')
                preco_compra = request.form.get('preco_compra')
                estoque = request.form.get('estoque', 0)
                estoque_minimo = request.form.get('estoque_minimo', 5)
                descricao = request.form.get('descricao', '')
                fornecedor_id = request.form.get('fornecedor_id')
                if 'imagem' in request.files:
                    file = request.files['imagem']

            elif request.content_type.startswith('application/json'):
                data = request.json
                nome = data.get('nome')
                categoria_id = data.get('categoria_id')
                preco = data.get('preco')
                preco_compra = data.get('preco_compra')
                estoque = data.get('estoque', 0)
                estoque_minimo = data.get('estoque_minimo', 5)
                descricao = data.get('descricao', '')
                fornecedor_id = data.get('fornecedor_id')
                # Permite URL de imagem via JSON
                imagem_url = data.get('imagem_url')
            else:
                return jsonify({"error": "Content-Type não suportado"}), 415

            # Validar dados obrigatórios
            if not all([nome, categoria_id, preco]):
                return jsonify({"error": "Nome, categoria e preço são obrigatórios"}), 400

            # Validar e converter tipos
            try:
                preco = float(preco)
                preco_compra = float(preco_compra) if preco_compra else None
                estoque = int(estoque)
                estoque_minimo = int(estoque_minimo)
                categoria_id = int(categoria_id)
                fornecedor_id = int(fornecedor_id) if fornecedor_id else None
            except (ValueError, TypeError) as e:
                return jsonify({"error": f"Valores inválidos para campos numéricos ou IDs: {e}"}), 400

            # Verificar se a categoria existe
            cursor.execute(
                "SELECT id FROM categoria WHERE id = ?", (categoria_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Categoria não encontrada"}), 404

            # Verificar se o fornecedor existe (se fornecido)
            if fornecedor_id:
                cursor.execute(
                    "SELECT id FROM fornecedor WHERE id = ?", (fornecedor_id,))
                if not cursor.fetchone():
                    return jsonify({"error": "Fornecedor não encontrado"}), 404

            # Processar imagem, se houver (apenas se for form-data)
            if file and allowed_file(file.filename):
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                filename = secure_filename(file.filename)
                # Garante nome único mesmo com nomes iguais
                filename = f"{uuid.uuid4().hex}_{filename}"
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                # Garante que a URL comece com / (relativo à raiz do site)
                # Adapta para URL web
                imagem_url = f"/{'/'.join(filepath.split(os.path.sep)[1:])}"

            # Gerar código único e data de criação
            codigo = f"P{uuid.uuid4().hex[:6].upper()}"
            # data_criacao = datetime.datetime.now() # SQLite geralmente lida com CURRENT_TIMESTAMP

            # Criar o produto
            sql = """
                INSERT INTO produto
                (codigo, nome, descricao, categoria_id, fornecedor_id, preco, preco_compra,
                 estoque, estoque_minimo, imagem_url, data_criacao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            params = (
                codigo, nome, descricao, categoria_id, fornecedor_id, preco, preco_compra,
                estoque, estoque_minimo, imagem_url
            )
            cursor.execute(sql, params)
            produto_id = cursor.lastrowid
            conn.commit()

            # Registrar movimento de estoque inicial
            if estoque > 0 and 'user_id' in session:  # Garante que usuario está logado
                registrar_movimento(
                    produto_id=produto_id,
                    tipo='entrada',
                    quantidade=estoque,
                    usuario_id=session['user_id'],
                    observacao="Estoque inicial - Cadastro de produto"
                )
            elif estoque > 0:
                print(
                    "WARN: Estoque inicial > 0 mas user_id não encontrado na sessão para registrar movimento.")

            return jsonify({
                "message": "Produto adicionado com sucesso",
                "produto": {
                    "id": produto_id,
                    "codigo": codigo,
                    "nome": nome,
                    "preco": preco,
                    "estoque": estoque
                }
            }), 201

    except sqlite3.Error as e:
        if conn:
            if request.method == 'POST':
                conn.rollback()
        return jsonify({"error": f"Erro no banco de dados: {e}"}), 500
    except Exception as e:  # Captura outros erros (ex: file save)
        if conn and request.method == 'POST':
            conn.rollback()  # Tenta rollback mesmo para erros não-sqlite
        # Considerar logar o erro `e`
        return jsonify({"error": f"Erro inesperado: {e}"}), 500


# --- API para um produto específico ---


@produtos_bp.route('/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def produto(id):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Função auxiliar para buscar o produto
        def fetch_produto(prod_id):
            cursor.execute(
                """
                SELECT
                    p.*, c.nome as categoria_nome, f.nome as fornecedor_nome
                FROM produto p
                LEFT JOIN categoria c ON p.categoria_id = c.id
                LEFT JOIN fornecedor f ON p.fornecedor_id = f.id
                WHERE p.id = ?
                """,
                (prod_id,)
            )
            return cursor.fetchone()

        produto_data = fetch_produto(id)

        if not produto_data:
            return jsonify({"error": "Produto não encontrado"}), 404

        if request.method == 'GET':
            # Formatar data_criacao (assumindo que vem como string ISO do SQLite)
            data_criacao_fmt = produto_data['data_criacao']
            try:
                # Tenta converter de ISO string para datetime e formatar
                dt_obj = datetime.datetime.fromisoformat(
                    produto_data['data_criacao'])
                data_criacao_fmt = dt_obj.strftime('%d/%m/%Y %H:%M')
            except (TypeError, ValueError):
                # Se já for string formatada ou outro formato, usa como está
                pass

            return jsonify({
                "id": produto_data['id'],
                "codigo": produto_data['codigo'],
                "nome": produto_data['nome'],
                "descricao": produto_data['descricao'],
                "categoria": {
                    "id": produto_data['categoria_id'],
                    "nome": produto_data['categoria_nome']
                } if produto_data['categoria_id'] else None,
                "fornecedor": {
                    "id": produto_data['fornecedor_id'],
                    "nome": produto_data['fornecedor_nome']
                } if produto_data['fornecedor_id'] else None,
                "preco": produto_data['preco'],
                "preco_compra": produto_data['preco_compra'],
                "estoque": produto_data['estoque'],
                "estoque_minimo": produto_data['estoque_minimo'],
                "imagem_url": produto_data['imagem_url'],
                "data_criacao": data_criacao_fmt
            })

        elif request.method == 'PUT':
            # Verificar permissão
            if session.get('user_level') not in ['admin', 'gerente']:
                return jsonify({"error": "Permissão negada"}), 403

            updates = {}
            file = None

            # Lida com form-data ou json
            if request.content_type.startswith('multipart/form-data'):
                # Extrair dados do form
                for key in ['nome', 'descricao', 'preco', 'preco_compra', 'estoque_minimo', 'categoria_id', 'fornecedor_id']:
                    if key in request.form:
                        updates[key] = request.form[key]
                if 'imagem' in request.files:
                    file = request.files['imagem']
            elif request.content_type.startswith('application/json'):
                data = request.json
                # Extrair dados do JSON
                for key in ['nome', 'descricao', 'preco', 'preco_compra', 'estoque_minimo', 'categoria_id', 'fornecedor_id', 'imagem_url']:
                    if key in data:
                        updates[key] = data[key]
            else:
                return jsonify({"error": "Content-Type não suportado"}), 415

            # Validar e converter tipos (exceto imagem_url)
            params = {}
            for key, value in updates.items():
                if value is None:  # Ignora Nones explícitos no JSON? Ou permite setar pra NULL?
                    # Permite setar pra NULL (ex: remover fornecedor)
                    params[key] = None
                    continue
                try:
                    if key in ['preco', 'preco_compra']:
                        params[key] = float(value)
                    elif key in ['estoque_minimo', 'categoria_id', 'fornecedor_id']:
                        # Verifica se ID existe antes de adicionar
                        if key == 'categoria_id':
                            cursor.execute(
                                "SELECT id FROM categoria WHERE id = ?", (int(value),))
                            if not cursor.fetchone():
                                continue  # Pula se categoria não existe
                        if key == 'fornecedor_id':
                            if not value:  # Permite remover fornecedor passando '' ou null
                                params[key] = None
                                continue
                            cursor.execute(
                                "SELECT id FROM fornecedor WHERE id = ?", (int(value),))
                            if not cursor.fetchone():
                                continue  # Pula se fornecedor não existe

                        params[key] = int(value)
                    elif key == 'imagem_url':  # Já vem como string do JSON
                        params[key] = value
                    else:  # nome, descricao
                        params[key] = str(value)
                except (ValueError, TypeError):
                    # Ignora campos com tipo inválido ou loga um aviso
                    print(
                        f"WARN: Valor inválido '{value}' para campo '{key}' na atualização do produto {id}")
                    pass  # Pula este campo

            # Processar imagem, se houver (form-data)
            if file and allowed_file(file.filename):
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                filename = secure_filename(file.filename)
                filename = f"{uuid.uuid4().hex}_{filename}"
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                params['imagem_url'] = f"/{'/'.join(filepath.split(os.path.sep)[1:])}"

            if not params:
                return jsonify({"message": "Nenhuma alteração válida fornecida"})

            # Construir a consulta de atualização
            set_clause = ', '.join(f"{key} = ?" for key in params.keys())
            sql_params = list(params.values())
            sql_params.append(id)

            cursor.execute(
                f"UPDATE produto SET {set_clause} WHERE id = ?", sql_params)
            conn.commit()

            # Buscar dados atualizados para retornar
            produto_atualizado = fetch_produto(id)  # Reutiliza a função

            return jsonify({
                "message": "Produto atualizado com sucesso",
                # Retorna o produto completo atualizado
                "produto": dict(produto_atualizado)
            })

        elif request.method == 'DELETE':
            # Verificar permissão
            if session.get('user_level') not in ['admin']:
                return jsonify({"error": "Permissão negada"}), 403

            # Verificar movimentos de estoque
            cursor.execute(
                "SELECT COUNT(*) FROM movimento_estoque WHERE produto_id = ?", (id,))
            if cursor.fetchone()[0] > 0:
                return jsonify({"error": "Produto possui movimentos de estoque associados."}), 400

            # Verificar itens de venda (assumindo tabela item_venda)
            try:
                cursor.execute(
                    "SELECT COUNT(*) FROM item_venda WHERE produto_id = ?", (id,))
                if cursor.fetchone()[0] > 0:
                    return jsonify({"error": "Produto possui vendas associadas."}), 400
            except sqlite3.Error as e:
                # Se a tabela item_venda não existir, ignora o erro
                if "no such table" not in str(e).lower():
                    raise e  # Relança outros erros
                print(
                    "WARN: Tabela item_venda não encontrada, pulando verificação de vendas.")

            # Excluir o produto
            cursor.execute("DELETE FROM produto WHERE id = ?", (id,))
            conn.commit()

            # Opcional: Excluir imagem do disco se existir
            if produto_data['imagem_url']:
                try:
                    # Constrói o caminho do sistema a partir da URL relativa
                    image_path = os.path.join(
                        'static', produto_data['imagem_url'].lstrip('/'))
                    if os.path.exists(image_path):
                        os.remove(image_path)
                        print(f"INFO: Imagem {image_path} excluída.")
                except Exception as img_err:
                    print(
                        f"ERROR: Falha ao excluir imagem {produto_data['imagem_url']}: {img_err}")

            return jsonify({"message": "Produto excluído com sucesso"})

    except sqlite3.Error as e:
        if conn:
            if request.method in ['PUT', 'DELETE']:
                conn.rollback()
        return jsonify({"error": f"Erro no banco de dados: {e}"}), 500
    except Exception as e:
        if conn and request.method in ['PUT', 'DELETE']:
            conn.rollback()
        return jsonify({"error": f"Erro inesperado: {e}"}), 500

# --- NOVA ROTA: Produtos com Estoque Baixo ---


@produtos_bp.route('/estoque-baixo', methods=['GET'])
@login_required
# Permite que operadores vejam também
@acesso_requerido(['admin', 'gerente', 'operador'])
def produtos_estoque_baixo():
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        page = request.args.get('page', 1, type=int)
        # Default maior para relatórios?
        per_page = request.args.get('per_page', 20, type=int)

        # Query base para produtos com estoque baixo ou igual ao mínimo
        base_query = """
            SELECT
                p.id, p.codigo, p.nome, p.estoque, p.estoque_minimo,
                p.categoria_id, c.nome as categoria_nome,
                p.fornecedor_id, f.nome as fornecedor_nome
            FROM produto p
            LEFT JOIN categoria c ON p.categoria_id = c.id
            LEFT JOIN fornecedor f ON p.fornecedor_id = f.id
            WHERE p.estoque <= p.estoque_minimo
        """
        count_query = """
            SELECT COUNT(p.id) FROM produto p WHERE p.estoque <= p.estoque_minimo
        """

        # Contar total para paginação
        cursor.execute(count_query)
        total = cursor.fetchone()[0]
        total_pages = (total + per_page - 1) // per_page if per_page > 0 else 1

        # Adicionar ordenação (talvez por quão abaixo do mínimo?) e paginação
        # Ordenando por nome por enquanto
        query = base_query + " ORDER BY p.nome LIMIT ? OFFSET ?"
        params = (per_page, (page - 1) * per_page)

        cursor.execute(query, params)
        produtos_rows = cursor.fetchall()

        # Formatar resultado
        resultado = []
        for p in produtos_rows:
            resultado.append({
                "id": p['id'],
                "codigo": p['codigo'],
                "nome": p['nome'],
                "estoque": p['estoque'],
                "estoque_minimo": p['estoque_minimo'],
                "categoria": {
                    "id": p['categoria_id'],
                    "nome": p['categoria_nome']
                } if p['categoria_id'] else None,
                "fornecedor": {
                    "id": p['fornecedor_id'],
                    "nome": p['fornecedor_nome']
                } if p['fornecedor_id'] else None,
            })

        return jsonify({
            "produtos": resultado,
            "total": total,
            "pages": total_pages,
            "page": page,
            "per_page": per_page
        })

    except sqlite3.Error as e:
        return jsonify({"error": f"Erro no banco de dados: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"Erro inesperado: {e}"}), 500


@produtos_bp.route('/mais-vendidos', methods=['GET'])
@login_required
@acesso_requerido(['admin', 'gerente'])  # Definir quem pode acessar
def produtos_mais_vendidos():
    """
    Retorna uma lista paginada dos produtos mais vendidos,
    ordenados pela quantidade total vendida (decrescente).
    Requer a tabela 'item_venda' com 'produto_id' e 'quantidade'.
    """
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        page = request.args.get('page', 1, type=int)
        # Ajuste o padrão se necessário
        per_page = request.args.get('per_page', 10, type=int)

        # Query para contar o total de produtos distintos que foram vendidos
        count_query = """
            SELECT COUNT(DISTINCT p.id)
            FROM produto p
            INNER JOIN item_venda iv ON p.id = iv.produto_id
        """
        cursor.execute(count_query)
        total = cursor.fetchone()[0]
        total_pages = (total + per_page - 1) // per_page if per_page > 0 else 1

        # Query principal para buscar os produtos mais vendidos
        base_query = """
            SELECT
                p.id, p.codigo, p.nome, p.preco,
                c.id as categoria_id, c.nome as categoria_nome,
                f.id as fornecedor_id, f.nome as fornecedor_nome,
                SUM(iv.quantidade) as total_vendido
            FROM produto p
            LEFT JOIN categoria c ON p.categoria_id = c.id
            LEFT JOIN fornecedor f ON p.fornecedor_id = f.id
            INNER JOIN item_venda iv ON p.id = iv.produto_id -- INNER JOIN: Apenas produtos vendidos
            GROUP BY p.id, p.codigo, p.nome, p.preco, c.id, c.nome, f.id, f.nome -- Agrupar por todos os campos não agregados
            ORDER BY total_vendido DESC -- Ordenar por mais vendidos
            LIMIT ? OFFSET ?
        """
        params = (per_page, (page - 1) * per_page)
        cursor.execute(base_query, params)
        produtos_rows = cursor.fetchall()

        # Formatar resultado
        resultado = []
        for p in produtos_rows:
            resultado.append({
                "id": p['id'],
                "codigo": p['codigo'],
                "nome": p['nome'],
                "preco": p['preco'],
                "categoria": {
                    "id": p['categoria_id'],
                    "nome": p['categoria_nome']
                } if p['categoria_id'] else None,
                "fornecedor": {
                    "id": p['fornecedor_id'],
                    "nome": p['fornecedor_nome']
                } if p['fornecedor_id'] else None,
                # Adiciona a quantidade vendida
                "total_vendido": p['total_vendido']
            })

        return jsonify({
            "produtos": resultado,
            "total": total,
            "pages": total_pages,
            "page": page,
            "per_page": per_page
        })

    except sqlite3.Error as e:
        # Verifica se o erro é sobre a tabela item_venda não existir
        if "no such table: item_venda" in str(e).lower():
            # 501 Not Implemented
            return jsonify({"error": "A funcionalidade de mais vendidos requer a tabela 'item_venda'."}), 501
        return jsonify({"error": f"Erro no banco de dados: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"Erro inesperado: {e}"}), 500


# --- NOVA ROTA: Produtos Menos Vendidos ---


@produtos_bp.route('/menos-vendidos', methods=['GET'])
@login_required
@acesso_requerido(['admin', 'gerente'])  # Definir quem pode acessar
def produtos_menos_vendidos():
    """
    Retorna uma lista paginada dos produtos menos vendidos,
    incluindo os que nunca foram vendidos (quantidade 0),
    ordenados pela quantidade total vendida (crescente).
    Requer a tabela 'item_venda' com 'produto_id' e 'quantidade'.
    """
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # Query para contar o total de produtos (todos, vendidos ou não)
        count_query = "SELECT COUNT(id) FROM produto"
        cursor.execute(count_query)
        total = cursor.fetchone()[0]
        total_pages = (total + per_page - 1) // per_page if per_page > 0 else 1

        # Query principal para buscar os produtos menos vendidos
        base_query = """
            SELECT
                p.id, p.codigo, p.nome, p.preco,
                c.id as categoria_id, c.nome as categoria_nome,
                f.id as fornecedor_id, f.nome as fornecedor_nome,
                -- COALESCE para tratar produtos nunca vendidos (SUM retornaria NULL)
                COALESCE(SUM(iv.quantidade), 0) as total_vendido
            FROM produto p
            LEFT JOIN categoria c ON p.categoria_id = c.id
            LEFT JOIN fornecedor f ON p.fornecedor_id = f.id
            LEFT JOIN item_venda iv ON p.id = iv.produto_id -- LEFT JOIN: Inclui produtos não vendidos
            GROUP BY p.id, p.codigo, p.nome, p.preco, c.id, c.nome, f.id, f.nome
            ORDER BY total_vendido ASC -- Ordenar por menos vendidos (0 primeiro)
            LIMIT ? OFFSET ?
        """
        params = (per_page, (page - 1) * per_page)
        cursor.execute(base_query, params)
        produtos_rows = cursor.fetchall()

        # Formatar resultado
        resultado = []
        for p in produtos_rows:
            resultado.append({
                "id": p['id'],
                "codigo": p['codigo'],
                "nome": p['nome'],
                "preco": p['preco'],
                "categoria": {
                    "id": p['categoria_id'],
                    "nome": p['categoria_nome']
                } if p['categoria_id'] else None,
                "fornecedor": {
                    "id": p['fornecedor_id'],
                    "nome": p['fornecedor_nome']
                } if p['fornecedor_id'] else None,
                # Adiciona a quantidade vendida (pode ser 0)
                "total_vendido": p['total_vendido']
            })

        return jsonify({
            "produtos": resultado,
            "total": total,
            "pages": total_pages,
            "page": page,
            "per_page": per_page
        })

    except sqlite3.Error as e:
        # Verifica se o erro é sobre a tabela item_venda não existir
        if "no such table: item_venda" in str(e).lower():
            # 501 Not Implemented
            return jsonify({"error": "A funcionalidade de menos vendidos requer a tabela 'item_venda'."}), 501
        return jsonify({"error": f"Erro no banco de dados: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"Erro inesperado: {e}"}), 500


# --- API para busca de produtos (usando helper) ---


@produtos_bp.route('/busca', methods=['GET'])
@login_required
def busca_produto():
    # Delega para a função importada `buscar_produtos`
    # Garanta que `buscar_produtos` também use get_db() e sqlite3
    try:
        termo = request.args.get('termo', '')
        categoria = request.args.get('categoria_id', type=int)
        fornecedor = request.args.get('fornecedor_id', type=int)
        estoque_baixo = request.args.get('estoque_baixo', '').lower() == 'true'
        page = request.args.get('page', 1, type=int)
        # 'limite' aqui, 'per_page' em outros lugares? Padronizar.
        per_page = request.args.get('limite', 20, type=int)

        # Assumindo que buscar_produtos retorna um dicionário pronto para jsonify
        resultado = buscar_produtos(
            termo, categoria, fornecedor, estoque_baixo, page, per_page)

        return jsonify(resultado)
    except Exception as e:
        # Logar erro e retornar genérico
        print(f"Erro em busca_produto: {e}")
        return jsonify({"error": "Erro ao buscar produtos"}), 500


# --- Nova Rota ---


@produtos_bp.route('/estoque/categorias', methods=['GET'])
@login_required
def categorias_em_estoque():
    """Retorna uma lista de categorias que possuem produtos com estoque > 0."""
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT c.id, c.nome
            FROM categoria c
            JOIN produto p ON c.id = p.categoria_id
            WHERE p.estoque > 0
            ORDER BY c.nome ASC
        """)
        categorias = [dict_factory(cursor, row) for row in cursor.fetchall()]
        return jsonify(categorias)
    except sqlite3.Error as e:
        print(f"Erro ao buscar categorias em estoque: {e}")
        return jsonify({"error": "Erro ao buscar categorias"}), 500
    finally:
        if conn:
            conn.close()


# --- Rotas de Página HTML (se existirem neste arquivo) ---

# Exemplo: Rota para renderizar a página de produtos (se estiver aqui)
@produtos_bp.route('/page', methods=['GET'])
@login_required
def produtos_page():
    # A lógica de carregamento de dados agora é feita via JS/API
    return render_template('produtos.html')


# Exemplo: Rota para renderizar a página de adicionar produto (se estiver aqui)
@produtos_bp.route('/adicionar', methods=['GET'])
@login_required
@acesso_requerido(['admin', 'gerente'])
def adicionar_produto():
     # Pode carregar categorias/fornecedores aqui para o template,
     # ou deixar o JS carregar nos modais
    return render_template('adicionar_produto.html') # Ou renderizar o modal direto na página principal


# Exemplo: Rota para renderizar a página de edição de produto (se estiver aqui)
@produtos_bp.route('/editar/<int:id>', methods=['GET'])
@login_required
@acesso_requerido(['admin', 'gerente'])
def editar_produto(id):
    produto_dict = None
    categorias = []
    fornecedores = []
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Buscar produto específico
        cursor.execute(
            """
            SELECT
                p.*, c.nome as categoria_nome, f.nome as fornecedor_nome
            FROM produto p
            LEFT JOIN categoria c ON p.categoria_id = c.id
            LEFT JOIN fornecedor f ON p.fornecedor_id = f.id
            WHERE p.id = ?
            """,
            (id,)
        )
        produto_data = cursor.fetchone()

        if not produto_data:
            flash('Produto não encontrado', 'danger')
            return redirect(url_for('produtos.produtos_page'))

        produto_dict = dict(produto_data)

        # Buscar todas as categorias e fornecedores para os dropdowns
        cursor.execute("SELECT id, nome FROM categoria ORDER BY nome")
        categorias = cursor.fetchall()
        # Apenas ativos
        cursor.execute(
            "SELECT id, nome FROM fornecedor WHERE ativo = 1 ORDER BY nome")
        fornecedores = cursor.fetchall()

    except sqlite3.Error as e:
        flash(f'Erro ao carregar dados para edição: {e}', 'danger')
        # Redireciona mesmo se der erro ao carregar categorias/fornecedores
        # para evitar mostrar a página de edição sem dados essenciais.
        return redirect(url_for('produtos.produtos_page'))
    except Exception as e:
        flash(f'Erro inesperado: {e}', 'danger')
        return redirect(url_for('produtos.produtos_page'))

    return render_template('editar_produto.html',
                           produto=produto_dict,
                           categorias=[dict(c) for c in categorias],
                           fornecedores=[dict(f) for f in fornecedores])
