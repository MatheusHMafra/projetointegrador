from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from database_utils import get_db
from datetime import datetime
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash

# Criar Blueprint para autenticação
auth_bp = Blueprint('auth', __name__)

# Função de decorador para verificar se o usuário está autenticado


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({"error": "Autenticação necessária"}), 401
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Função para verificar nível de acesso


def acesso_requerido(niveis_permitidos):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({"error": "Autenticação necessária"}), 401
                return redirect(url_for('auth.login', next=request.url))

            # Primeiro, verificar se o nivel_acesso está na sessão
            if 'user_level' not in session:
                db = get_db()
                usuario = db.execute(
                    'SELECT * FROM usuario WHERE id = ?', (session['user_id'],)).fetchone()
                db.close()  # Fechar a conexão após obter o usuário

                # Corrigido: Acessar colunas usando notação de dicionário
                if not usuario or not usuario['ativo']:
                    session.clear()
                    if request.is_json:
                        return jsonify({"error": "Usuário inativo ou não encontrado"}), 401
                    flash('Sua sessão expirou ou seu usuário está inativo.', 'danger')
                    return redirect(url_for('auth.login'))

                # Adicionar o nivel_acesso à sessão se não existir
                session['user_level'] = usuario['nivel_acesso']

            # Agora verificar permissões com o nível da sessão
            if session['user_level'] not in niveis_permitidos:
                if request.is_json:
                    return jsonify({"error": "Acesso não autorizado"}), 403
                flash('Você não tem permissão para acessar este recurso.', 'danger')
                # Redirecionar para uma página inicial ou de erro de acesso
                return redirect(url_for('index'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Rota de login


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form if request.form else request.get_json()
        if not data:
            if request.is_json:
                return jsonify({"error": "Dados de login inválidos"}), 400
            flash('Dados de login inválidos', 'danger')
            return render_template('login.html')

        email = data.get('email')
        senha = data.get('senha')  # Esta é a senha em texto plano

        if not email or not senha:
            if request.is_json:
                return jsonify({"error": "Email e senha são obrigatórios"}), 400
            flash('Email e senha são obrigatórios', 'danger')
            return render_template('login.html')

        db = get_db()
        # Note: SELECT * pega a senha_hash se a coluna existir
        usuario = db.execute(
            'SELECT * FROM usuario WHERE email = ?', (email,)).fetchone()
        # Não feche a conexão ainda se for usá-la novamente para o UPDATE

        if not usuario:
            # Fechar a conexão antes de retornar se não for usá-la mais aqui
            db.close()
            if request.is_json:
                return jsonify({"error": "Usuário não encontrado"}), 404
            flash('Usuário não encontrado', 'danger')
            return render_template('login.html')

        # ! Verificar se a senha está correta USANDO check_password_hash
        # Assumindo que a coluna com o hash da senha se chama 'senha_hash'
        # Corrigido: Acessar 'senha_hash' usando notação de dicionário
        if not check_password_hash(usuario['senha_hash'], senha):
            # Fechar a conexão antes de retornar
            db.close()
            if request.is_json:
                return jsonify({"error": "Senha incorreta"}), 401
            flash('Senha incorreta', 'danger')
            return render_template('login.html')

        # Corrigido: Acessar a coluna 'ativo' do sqlite3.Row
        if not usuario['ativo']:
            # Fechar a conexão antes de retornar
            db.close()
            if request.is_json:
                return jsonify({"error": "Usuário inativo"}), 401
            flash(
                'Sua conta está inativa. Entre em contato com o administrador.', 'warning')
            return render_template('login.html')

        # Registrar o acesso
        # Reutilizando a conexão aberta anteriormente (ou reabrindo se fechou)
        # db = get_db() # Se você fechou a conexão antes, reabra aqui
        try:
            db.execute(
                'UPDATE usuario SET ultimo_acesso = ? WHERE id = ?',
                # Corrigido: Acessando 'id' do sqlite3.Row
                (datetime.now(), usuario['id'])
            )
            db.commit()
        except Exception as e:
            # Tratar erros de DB aqui, se necessário
            print(f"Erro ao atualizar ultimo_acesso: {e}")
            db.rollback()  # Desfaz a operação se der erro
        finally:
            db.close()  # Fechar a conexão depois de usá-la

        # Criar sessão
        # Corrigido: Acessando colunas usando notação de dicionário e garantindo o armazenamento correto do nivel_acesso
        session['user_id'] = usuario['id']
        session['user_name'] = usuario['nome']
        # Garantir que este valor é armazenado corretamente
        session['user_level'] = usuario['nivel_acesso']
        session['user_email'] = usuario['email']
        session.permanent = True

        next_url = request.args.get('next')
        if next_url:
            return redirect(next_url)

        if request.is_json:
            return jsonify({
                "message": "Login realizado com sucesso",
                "user": {
                    # Corrigido: Acessando colunas usando notação de dicionário
                    "id": usuario['id'],
                    "nome": usuario['nome'],
                    "email": usuario['email'],
                    "nivel_acesso": usuario['nivel_acesso']
                }
            })

        # Certifique-se de que 'dashboard' é o endpoint correto
        return redirect(url_for('dashboard'))

    return render_template('login.html')

# Rota de logout


@auth_bp.route('/logout')
def logout():
    session.clear()
    if request.is_json:
        return jsonify({"message": "Logout realizado com sucesso"})
    return redirect(url_for('auth.login'))

# Rota de registro de usuário (apenas para admin)


@auth_bp.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
@acesso_requerido(['admin'])
def novo_usuario():
    if request.method == 'POST':
        data = request.form if request.form else request.get_json()

        nome = data.get('nome')
        email = data.get('email')
        senha = data.get('senha')
        nivel_acesso = data.get('nivel_acesso', 'operador')

        if not all([nome, email, senha]):
            if request.is_json:
                return jsonify({"error": "Todos os campos são obrigatórios"}), 400
            flash('Todos os campos são obrigatórios', 'danger')
            return render_template('novo_usuario.html')

        db = get_db()
        userexiste = db.execute(
            'SELECT * FROM usuario WHERE email = ?', (email,)).fetchone()
        # Verificar se o email já está em uso
        if userexiste:
            if request.is_json:
                return jsonify({"error": "Email já cadastrado"}), 400
            flash('Email já cadastrado', 'danger')
            db.close()
            return render_template('novo_usuario.html')

        # ! Gerar hash da senha antes de armazenar
        senha_hash = generate_password_hash(senha)

        # Criar usuário
        try:
            cursor = db.execute(
                'INSERT INTO usuario (nome, email, senha_hash, nivel_acesso) VALUES (?, ?, ?, ?)',
                (nome, email, senha_hash, nivel_acesso)  # Usar a senha_hash
            )
            db.commit()
            # Recuperar o usuário recém-criado para a resposta JSON (opcional)
            usuario = db.execute(
                'SELECT * FROM usuario WHERE id = ?', (cursor.lastrowid,)).fetchone()
        except Exception as e:
            print(f"Erro ao inserir novo usuário: {e}")
            db.rollback()
            if request.is_json:
                return jsonify({"error": "Erro ao cadastrar usuário"}), 500
            flash('Erro ao cadastrar usuário.', 'danger')
            return render_template('novo_usuario.html')
        finally:
            db.close()

        if request.is_json and usuario:  # Verificar se usuario foi recuperado com sucesso
            return jsonify({
                "message": "Usuário cadastrado com sucesso",
                "usuario": {
                    # Corrigido: Acessando colunas usando notação de dicionário
                    "id": usuario['id'],
                    "nome": usuario['nome'],
                    "email": usuario['email'],
                    "nivel_acesso": usuario['nivel_acesso']
                }
            })
        elif request.is_json:
            # Retornar sucesso mesmo se não recuperou o usuário para JSON
            return jsonify({"message": "Usuário cadastrado com sucesso (detalhes não recuperados)"})

        flash('Usuário cadastrado com sucesso!', 'success')
        return redirect(url_for('auth.listar_usuarios'))

    return render_template('novo_usuario.html')

# API para gerenciar usuários (apenas admin)


@auth_bp.route('/usuarios', methods=['GET'])
@login_required
@acesso_requerido(['admin'])
def listar_usuarios():
    db = get_db()
    usuarios = db.execute(
        'SELECT * FROM usuario ORDER BY nome').fetchall()
    db.close()  # Fechar a conexão após obter os dados

    if not usuarios and request.is_json:
        # Retorna lista vazia para JSON se não houver usuários
        return jsonify({"usuarios": []}), 200
    elif not usuarios:
        flash('Nenhum usuário encontrado', 'warning')
        # Passar lista vazia ou None para o template
        return render_template('usuarios.html')

    if request.is_json:
        return jsonify({
            "usuarios": [{
                # Corrigido: Acessando colunas usando notação de dicionário
                "id": u['id'],
                "nome": u['nome'],
                "email": u['email'],
                "nivel_acesso": u['nivel_acesso'],
                "ativo": u['ativo'],
                "data_criacao": u['data_criacao'].strftime('%d/%m/%Y %H:%M') if u['data_criacao'] else None,
                "ultimo_acesso": u['ultimo_acesso'].strftime('%d/%m/%Y %H:%M') if u['ultimo_acesso'] else None
            } for u in usuarios]
        })

    return render_template('usuarios.html', usuarios=usuarios)

# API para detalhes de um usuário


@auth_bp.route('/usuarios/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
@acesso_requerido(['admin'])
def usuario(id):
    db = get_db()
    usuario = db.execute(
        'SELECT * FROM usuario WHERE id = ?', (id,)).fetchone()
    db.close()  # Fechar a conexão após obter o usuário

    if not usuario:
        if request.is_json:
            return jsonify({"error": "Usuário não encontrado"}), 404
        flash('Usuário não encontrado', 'danger')
        return redirect(url_for('auth.listar_usuarios'))

    if request.method == 'GET':
        if request.is_json:
            return jsonify({
                "usuario": {
                    # Corrigido: Acessando colunas usando notação de dicionário
                    "id": usuario['id'],
                    "nome": usuario['nome'],
                    "email": usuario['email'],
                    "nivel_acesso": usuario['nivel_acesso'],
                    "ativo": usuario['ativo'],
                    "data_criacao": usuario['data_criacao'].strftime('%d/%m/%Y %H:%M') if usuario['data_criacao'] else None,
                    "ultimo_acesso": usuario['ultimo_acesso'].strftime('%d/%m/%Y %H:%M') if usuario['ultimo_acesso'] else None
                }
            })
        return render_template('editar_usuario.html', usuario=usuario)

    elif request.method == 'PUT':
        data = request.get_json()  # Assumindo que PUT usa JSON

        # Crie um dicionário para armazenar as atualizações
        updates = {}
        if 'nome' in data:
            updates['nome'] = data['nome']
        if 'email' in data:
            # Verificar se o novo email não está em uso por outro usuário
            db = get_db()  # Reabrir conexão para a verificação
            existing = db.execute(
                'SELECT * FROM usuario WHERE email = ? AND id != ?', (data['email'], id)).fetchone()
            db.close()  # Fechar conexão após a verificação
            if existing:
                return jsonify({"error": "Email já está em uso por outro usuário"}), 400
            updates['email'] = data['email']
        if 'nivel_acesso' in data:
            updates['nivel_acesso'] = data['nivel_acesso']
        if 'ativo' in data:
            updates['ativo'] = data['ativo']
        # Atualizar senha apenas se fornecida
        if 'senha' in data and data['senha']:
            # ! Gerar hash da nova senha
            updates['senha_hash'] = generate_password_hash(data['senha'])

        if not updates:
            # Nada para fazer
            return jsonify({"message": "Nenhum dado para atualizar"}), 200

        # Construir a query de UPDATE dinamicamente
        set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values())
        values.append(id)  # Adicionar o ID para a cláusula WHERE

        db = get_db()  # Reabrir conexão para a atualização
        try:
            db.execute(f'UPDATE usuario SET {set_clause} WHERE id = ?', values)
            db.commit()
        except Exception as e:
            print(f"Erro ao atualizar usuário {id}: {e}")
            db.rollback()
            return jsonify({"error": "Erro ao atualizar usuário"}), 500
        finally:
            db.close()  # Fechar conexão após a atualização

        return jsonify({"message": "Usuário atualizado com sucesso"})

    elif request.method == 'DELETE':
        # Verificar se não é o próprio usuário logado
        # Corrigido: Acessar 'id' do sqlite3.Row
        if usuario['id'] == session.get('user_id'):
            if request.is_json:
                return jsonify({"error": "Não é possível excluir o próprio usuário"}), 400
            flash('Não é possível excluir o próprio usuário', 'danger')
            return redirect(url_for('auth.listar_usuarios'))

        db = get_db()  # Reabrir conexão para a exclusão
        try:
            # Corrigido: Acessar 'id' do sqlite3.Row
            db.execute('DELETE FROM usuario WHERE id = ?', (usuario['id'],))
            db.commit()
        except Exception as e:
            print(f"Erro ao excluir usuário {id}: {e}")
            db.rollback()
            if request.is_json:
                return jsonify({"error": "Erro ao excluir usuário"}), 500
            flash('Erro ao excluir usuário.', 'danger')
            return redirect(url_for('auth.listar_usuarios'))
        finally:
            db.close()  # Fechar conexão após a exclusão

        if request.is_json:
            return jsonify({"message": "Usuário excluído com sucesso"})
        flash('Usuário excluído com sucesso', 'success')
        return redirect(url_for('auth.listar_usuarios'))

    return jsonify({"error": "Método não permitido"}), 405

# Rota para alteração de senha


@auth_bp.route('/alterar-senha', methods=['GET', 'POST'])
@login_required
def alterar_senha():
    if request.method == 'POST':
        data = request.form if request.form else request.get_json()

        senha_atual = data.get('senha_atual')
        nova_senha = data.get('nova_senha')
        confirma_senha = data.get('confirma_senha')

        if not all([senha_atual, nova_senha, confirma_senha]):
            if request.is_json:
                return jsonify({"error": "Todos os campos são obrigatórios"}), 400
            flash('Todos os campos são obrigatórios', 'danger')
            return render_template('alterar_senha.html')

        if nova_senha != confirma_senha:
            if request.is_json:
                return jsonify({"error": "Nova senha e confirmação não conferem"}), 400
            flash('Nova senha e confirmação não conferem', 'danger')
            return render_template('alterar_senha.html')

        db = get_db()
        usuario = db.execute(
            'SELECT * FROM usuario WHERE id = ?', (session['user_id'],)).fetchone()
        db.close()  # Fechar conexão após obter o usuário

        if not usuario:
            session.clear()
            if request.is_json:
                return jsonify({"error": "Usuário não encontrado"}), 404
            flash('Sua sessão expirou.', 'danger')  # Melhor mensagem
            return redirect(url_for('auth.login'))

        # Corrigido: Usar check_password_hash com a senha_hash do banco
        if not check_password_hash(usuario['senha_hash'], senha_atual):
            if request.is_json:
                return jsonify({"error": "Senha atual incorreta"}), 400
            flash('Senha atual incorreta', 'danger')
            return render_template('alterar_senha.html')

        # ! Gerar hash da nova senha
        hashed_nova_senha = generate_password_hash(nova_senha)

        db = get_db()  # Reabrir conexão para a atualização
        try:
            # Corrigido: Usar o hash da nova senha e o id do usuário
            db.execute(
                'UPDATE usuario SET senha_hash = ? WHERE id = ?',
                (hashed_nova_senha, usuario['id'])
            )
            db.commit()
        except Exception as e:
            print(f"Erro ao alterar senha do usuário {usuario['id']}: {e}")
            db.rollback()
            if request.is_json:
                return jsonify({"error": "Erro ao alterar senha"}), 500
            flash('Erro ao alterar senha.', 'danger')
            return render_template('alterar_senha.html')
        finally:
            db.close()  # Fechar conexão após a atualização

        if request.is_json:
            return jsonify({"message": "Senha alterada com sucesso"})

        flash('Senha alterada com sucesso!', 'success')
        # Redirecionar para o dashboard ou página de perfil
        return redirect(url_for('dashboard'))

    return render_template('alterar_senha.html')

# Verificação de autenticação para API


@auth_bp.route('/check', methods=['GET'])
def check_auth():
    if 'user_id' in session:
        db = get_db()
        usuario = db.execute(
            'SELECT * FROM usuario WHERE id = ?', (session['user_id'],)).fetchone()
        db.close()  # Fechar conexão após obter o usuário

        # Corrigido: Acessar colunas usando notação de dicionário
        if usuario and usuario['ativo']:
            return jsonify({
                "authenticated": True,
                "user": {
                    # Corrigido: Acessar colunas usando notação de dicionário
                    "id": usuario['id'],
                    "nome": usuario['nome'],
                    "email": usuario['email'],
                    "nivel_acesso": usuario['nivel_acesso']
                }
            })
    return jsonify({"authenticated": False}), 401
