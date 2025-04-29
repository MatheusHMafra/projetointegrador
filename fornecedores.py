import sqlite3
from flask import Blueprint, request, jsonify, render_template, session, flash, redirect, url_for
from database_utils import get_db
from auth import login_required, acesso_requerido

fornecedores_bp = Blueprint('fornecedores', __name__)

# --- Helpers (Opcional, mas pode limpar o código) ---
def dict_factory(cursor, row):
    """Converte uma linha do banco (tupla) em um dicionário."""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

# Configurar row_factory na função get_db é preferível,
# mas se não for possível, você pode usar um helper como acima
# ou acessar por índice. Assumindo get_db já configura sqlite3.Row

# --- Rotas da API ---

@fornecedores_bp.route('/', methods=['GET', 'POST'])
@login_required
def listar_fornecedores():
    db = get_db()
    cursor = db.cursor()

    if request.method == 'GET':
        # Verificar permissão (igual ao original)
        if session.get('user_level') not in ['admin', 'gerente', 'operador']:
             return jsonify({"error": "Permissão negada"}), 403

        # Parâmetros de Paginação e Filtro/Ordenação
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        ativo = request.args.get('ativo')
        busca = request.args.get('busca')
        ordenar = request.args.get('ordenar', 'nome')
        direcao = request.args.get('direcao', 'asc').lower()

        # Construir a consulta SQL dinamicamente
        params = []
        count_params = []
        base_sql = """
            SELECT f.id, f.nome, f.cnpj, f.telefone, f.email, f.contato, f.ativo
            FROM fornecedores f
        """
        where_clauses = []

        # Filtro por ativo
        if ativo is not None:
            where_clauses.append("f.ativo = ?")
            params.append(ativo.lower() == 'true')
            count_params.append(ativo.lower() == 'true')

        # Filtro por busca
        if busca:
            busca_like = f'%{busca}%'
            where_clauses.append("(f.nome LIKE ? OR f.email LIKE ? OR f.contato LIKE ? OR f.cnpj LIKE ?)")
            params.extend([busca_like] * 4)
            count_params.extend([busca_like] * 4)

        # Montar cláusula WHERE
        sql = base_sql
        count_sql = "SELECT COUNT(f.id) FROM fornecedores f"
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
            count_sql += " WHERE " + " AND ".join(where_clauses)

        # Obter contagem total para paginação
        try:
            cursor.execute(count_sql, count_params)
            total = cursor.fetchone()[0]
        except sqlite3.Error as e:
            return jsonify({"error": f"Erro ao contar fornecedores: {e}"}), 500

        # Ordenação
        order_column = "f.nome" # Default
        if ordenar == 'data_cadastro':
             # Supondo que a coluna existe na tabela fornecedores
             order_column = "f.data_cadastro"

        order_direction = "ASC" if direcao == 'asc' else "DESC"
        sql += f" ORDER BY {order_column} {order_direction}" # Cuidado com SQL injection se 'ordenar'/'direcao' não forem validados

        # Paginação
        offset = (page - 1) * per_page
        sql += " LIMIT ? OFFSET ?"
        params.append(per_page)
        params.append(offset)

        # Executar consulta principal
        try:
            cursor.execute(sql, params)
            fornecedores_rows = cursor.fetchall()
        except sqlite3.Error as e:
            return jsonify({"error": f"Erro ao buscar fornecedores: {e}"}), 500

        # Calcular total de páginas
        pages = (total + per_page - 1) // per_page

        # Formatar resposta (e buscar contagem de produtos para cada um)
        fornecedores_list = []
        for row in fornecedores_rows:
            fornecedor_dict = dict(row) # Converte sqlite3.Row para dict
            try:
                # Query para contar produtos do fornecedor
                cursor.execute("SELECT COUNT(id) FROM produtos WHERE fornecedor_id = ?", (row['id'],))
                total_produtos = cursor.fetchone()[0]
                fornecedor_dict['total_produtos'] = total_produtos
            except sqlite3.Error as e:
                # Logar erro ou definir um valor padrão
                print(f"Erro ao contar produtos para fornecedor {row['id']}: {e}")
                fornecedor_dict['total_produtos'] = 'Erro' # Ou 0, ou None
            fornecedores_list.append(fornecedor_dict)


        return jsonify({
            "fornecedores": fornecedores_list,
            "total": total,
            "pages": pages,
            "page": page
        })

    elif request.method == 'POST':
        # Verificar permissão (igual ao original)
        if session.get('user_level') not in ['admin', 'gerente']:
            return jsonify({"error": "Permissão negada"}), 403

        data = request.json

        # Validar dados (igual ao original)
        if not data or not data.get('nome'):
            return jsonify({"error": "Nome do fornecedor é obrigatório"}), 400

        cnpj = data.get('cnpj')

        # Verificar se o CNPJ já existe
        if cnpj:
            try:
                cursor.execute("SELECT id FROM fornecedores WHERE cnpj = ?", (cnpj,))
                if cursor.fetchone():
                    return jsonify({"error": "CNPJ já cadastrado"}), 400
            except sqlite3.Error as e:
                 return jsonify({"error": f"Erro ao verificar CNPJ: {e}"}), 500

        # Inserir novo fornecedor
        sql = """
            INSERT INTO fornecedores
            (nome, cnpj, email, telefone, endereco, contato, observacoes, ativo, data_cadastro, ultima_atualizacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
        params = (
            data['nome'],
            cnpj,
            data.get('email'),
            data.get('telefone'),
            data.get('endereco'),
            data.get('contato'),
            data.get('observacoes'),
            data.get('ativo', True)
        )

        try:
            cursor.execute(sql, params)
            new_id = cursor.lastrowid # Obter o ID do registro inserido
            db.commit() # Salvar as alterações
        except sqlite3.Error as e:
            db.rollback() # Desfazer em caso de erro
            return jsonify({"error": f"Erro ao cadastrar fornecedor: {e}"}), 500

        return jsonify({
            "message": "Fornecedor cadastrado com sucesso",
            "fornecedor": {
                "id": new_id,
                "nome": data['nome']
            }
        }), 201

@fornecedores_bp.route('/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def gerenciar_fornecedor(id):
    db = get_db()
    cursor = db.cursor()

    # Tentar buscar o fornecedor primeiro para todos os métodos
    try:
        cursor.execute("""
            SELECT id, nome, cnpj, email, telefone, endereco, contato, observacoes, ativo,
                   strftime('%d/%m/%Y', data_cadastro) as data_cadastro_fmt
            FROM fornecedores WHERE id = ?
            """, (id,))
        fornecedor = cursor.fetchone()
    except sqlite3.Error as e:
         return jsonify({"error": f"Erro ao buscar fornecedor: {e}"}), 500

    if not fornecedor:
        return jsonify({"error": "Fornecedor não encontrado"}), 404

    fornecedor_dict = dict(fornecedor) # Converter para dict

    if request.method == 'GET':
        # Buscar contagem e alguns produtos associados
        try:
            cursor.execute("SELECT COUNT(id) FROM produtos WHERE fornecedor_id = ?", (id,))
            produtos_count = cursor.fetchone()[0]

            cursor.execute("""
                SELECT id, codigo, nome, preco, estoque
                FROM produtos WHERE fornecedor_id = ? LIMIT 20
                """, (id,))
            produtos_rows = cursor.fetchall()
            produtos_list = [dict(p) for p in produtos_rows] # Converter lista de Rows para lista de dicts

        except sqlite3.Error as e:
             return jsonify({"error": f"Erro ao buscar produtos do fornecedor: {e}"}), 500

        fornecedor_dict["total_produtos"] = produtos_count
        fornecedor_dict["produtos"] = produtos_list
        fornecedor_dict["produtos_tem_mais"] = produtos_count > len(produtos_list)
        # Renomear chave formatada
        fornecedor_dict["data_cadastro"] = fornecedor_dict.pop("data_cadastro_fmt")


        return jsonify(fornecedor_dict)

    elif request.method == 'PUT':
        # Verificar permissão (igual ao original)
        if session.get('user_level') not in ['admin', 'gerente']:
             return jsonify({"error": "Permissão negada"}), 403

        data = request.json
        if not data:
             return jsonify({"error": "Dados não fornecidos"}), 400

        # Verificar se o CNPJ (se fornecido e diferente) já existe em outro fornecedor
        new_cnpj = data.get('cnpj')
        if new_cnpj is not None and new_cnpj != fornecedor_dict['cnpj']:
            try:
                cursor.execute("SELECT id FROM fornecedores WHERE cnpj = ? AND id != ?", (new_cnpj, id))
                if cursor.fetchone():
                    return jsonify({"error": "CNPJ já cadastrado em outro fornecedor"}), 400
            except sqlite3.Error as e:
                return jsonify({"error": f"Erro ao verificar CNPJ duplicado: {e}"}), 500

        # Construir a query de atualização dinamicamente
        update_fields = []
        params = []
        allowed_fields = ['nome', 'cnpj', 'email', 'telefone', 'endereco', 'contato', 'observacoes', 'ativo']

        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                params.append(data[field])

        if not update_fields:
             return jsonify({"error": "Nenhum campo para atualizar fornecido"}), 400

        # Adicionar atualização da data e o ID no final dos parâmetros
        update_fields.append("ultima_atualizacao = CURRENT_TIMESTAMP")
        params.append(id)

        sql = f"UPDATE fornecedores SET {', '.join(update_fields)} WHERE id = ?"

        try:
            cursor.execute(sql, params)
            db.commit()
        except sqlite3.Error as e:
            db.rollback()
            return jsonify({"error": f"Erro ao atualizar fornecedor: {e}"}), 500

        # Buscar nome e status atualizados para retornar
        try:
            cursor.execute("SELECT nome, ativo FROM fornecedores WHERE id = ?", (id,))
            updated_data = cursor.fetchone()
        except sqlite3.Error:
            updated_data = None # Não essencial, mas bom ter

        return jsonify({
            "message": "Fornecedor atualizado com sucesso",
            "fornecedor": {
                "id": id,
                "nome": updated_data['nome'] if updated_data else data.get('nome', fornecedor_dict['nome']),
                "ativo": updated_data['ativo'] if updated_data else data.get('ativo', fornecedor_dict['ativo'])
             }
        })

    elif request.method == 'DELETE':
        # Verificar permissão (igual ao original)
        if session.get('user_level') not in ['admin']:
             return jsonify({"error": "Permissão negada"}), 403

        # Verificar se tem produtos vinculados
        try:
            cursor.execute("SELECT COUNT(id) FROM produtos WHERE fornecedor_id = ?", (id,))
            product_count = cursor.fetchone()[0]
            if product_count > 0:
                return jsonify({
                    "error": "Não é possível excluir este fornecedor pois existem produtos associados a ele"
                }), 400
        except sqlite3.Error as e:
             return jsonify({"error": f"Erro ao verificar produtos associados: {e}"}), 500

        # Excluir fornecedor
        try:
            cursor.execute("DELETE FROM fornecedores WHERE id = ?", (id,))
            db.commit()
        except sqlite3.Error as e:
            db.rollback()
            return jsonify({"error": f"Erro ao excluir fornecedor: {e}"}), 500

        return jsonify({"message": "Fornecedor excluído com sucesso"})


@fornecedores_bp.route('/<int:id>/produtos', methods=['GET'])
@login_required
def produtos_fornecedor(id):
    db = get_db()
    cursor = db.cursor()

    # Verificar se o fornecedor existe e pegar o nome
    try:
        cursor.execute("SELECT id, nome FROM fornecedores WHERE id = ?", (id,))
        fornecedor = cursor.fetchone()
        if not fornecedor:
            return jsonify({"error": "Fornecedor não encontrado"}), 404
    except sqlite3.Error as e:
        return jsonify({"error": f"Erro ao buscar fornecedor: {e}"}), 500

    # Parâmetros de paginação
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    offset = (page - 1) * per_page

    # Contar total de produtos do fornecedor
    try:
        cursor.execute("SELECT COUNT(id) FROM produtos WHERE fornecedor_id = ?", (id,))
        total = cursor.fetchone()[0]
    except sqlite3.Error as e:
        return jsonify({"error": f"Erro ao contar produtos: {e}"}), 500

    # Buscar produtos paginados com nome da categoria (usando LEFT JOIN)
    sql = """
        SELECT p.id, p.codigo, p.nome, p.preco, p.estoque, c.nome as categoria
        FROM produtos p
        LEFT JOIN categorias c ON p.categoria_id = c.id
        WHERE p.fornecedor_id = ?
        ORDER BY p.nome ASC
        LIMIT ? OFFSET ?
    """
    params = (id, per_page, offset)

    try:
        cursor.execute(sql, params)
        produtos_rows = cursor.fetchall()
        produtos_list = [dict(p) for p in produtos_rows]
    except sqlite3.Error as e:
        return jsonify({"error": f"Erro ao buscar produtos: {e}"}), 500

    # Calcular total de páginas
    pages = (total + per_page - 1) // per_page

    return jsonify({
        "fornecedor": dict(fornecedor), # Converte o Row do fornecedor para dict
        "produtos": produtos_list,
        "total": total,
        "pages": pages,
        "page": page
    })


@fornecedores_bp.route('/<int:id>/alternar-status', methods=['POST'])
@login_required
@acesso_requerido(['admin', 'gerente']) # Usa a lista como no original
def alternar_status(id):
    db = get_db()
    cursor = db.cursor()

    # Buscar o status atual
    try:
        cursor.execute("SELECT ativo FROM fornecedores WHERE id = ?", (id,))
        fornecedor = cursor.fetchone()
        if not fornecedor:
            return jsonify({"error": "Fornecedor não encontrado"}), 404
    except sqlite3.Error as e:
        return jsonify({"error": f"Erro ao buscar fornecedor: {e}"}), 500

    novo_status = not fornecedor['ativo']

    # Atualizar o status
    try:
        cursor.execute("UPDATE fornecedores SET ativo = ?, ultima_atualizacao = CURRENT_TIMESTAMP WHERE id = ?", (novo_status, id))
        db.commit()
    except sqlite3.Error as e:
        db.rollback()
        return jsonify({"error": f"Erro ao alterar status: {e}"}), 500

    return jsonify({
        "message": f"Fornecedor {'ativado' if novo_status else 'desativado'} com sucesso",
        "ativo": novo_status
    })


# --- Rotas de Página HTML ---

@fornecedores_bp.route('/page', methods=['GET'])
@login_required
def fornecedores_page():
    # Nenhuma mudança necessária aqui, apenas renderiza o template.
    # O template fará chamadas AJAX para as APIs acima.
    return render_template('fornecedores.html')


@fornecedores_bp.route('/adicionar', methods=['GET'])
@login_required
@acesso_requerido(['admin', 'gerente'])
def adicionar_fornecedor():
    # Nenhuma mudança necessária aqui.
    return render_template('adicionar_fornecedor.html')


@fornecedores_bp.route('/editar/<int:id>', methods=['GET'])
@login_required
@acesso_requerido(['admin', 'gerente'])
def editar_fornecedor(id):
    db = get_db()
    cursor = db.cursor()

    # Buscar dados do fornecedor para preencher o formulário no template
    try:
        # Busca todos os campos necessários para o template 'editar_fornecedor.html'
        cursor.execute("""
            SELECT id, nome, cnpj, email, telefone, endereco, contato, observacoes, ativo
            FROM fornecedores
            WHERE id = ?
            """, (id,)
        )
        fornecedor_row = cursor.fetchone()
    except sqlite3.Error as e:
        flash(f'Erro ao buscar fornecedor: {e}', 'danger')
        return redirect(url_for('fornecedores.fornecedores_page'))

    if not fornecedor_row:
        flash('Fornecedor não encontrado', 'danger')
        return redirect(url_for('fornecedores.fornecedores_page'))

    # Converte o sqlite3.Row para um dicionário para passar ao template
    fornecedor_dict = dict(fornecedor_row)

    return render_template('editar_fornecedor.html', fornecedor=fornecedor_dict)