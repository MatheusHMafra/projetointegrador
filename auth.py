from flask import (
    Blueprint,
    request,
    jsonify,
    render_template,
    redirect,
    url_for,
    session,
    flash,
)
from database_utils import get_db
from datetime import datetime
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash

# Criar Blueprint para autenticação
auth_bp = Blueprint("auth", __name__)

# Função de decorador para verificar se o usuário está autenticado


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            if request.is_json:
                return jsonify({"error": "Autenticação necessária"}), 401
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)

    return decorated_function


# Função para verificar nível de acesso


def acesso_requerido(niveis_permitidos):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                if request.is_json:
                    return jsonify({"error": "Autenticação necessária"}), 401
                return redirect(url_for("auth.login", next=request.url))

            # Primeiro, verificar se o nivel_acesso está na sessão
            if "user_level" not in session:
                db = get_db()
                usuario = db.execute(
                    "SELECT * FROM usuario WHERE id = ?", (session["user_id"],)
                ).fetchone()
                db.close()  # Fechar a conexão após obter o usuário

                # Corrigido: Acessar colunas usando notação de dicionário
                if not usuario or not usuario["ativo"]:
                    session.clear()
                    if request.is_json:
                        return (
                            jsonify(
                                {"error": "Usuário inativo ou não encontrado"}),
                            401,
                        )
                    flash("Sua sessão expirou ou seu usuário está inativo.", "danger")
                    return redirect(url_for("auth.login"))

                # Adicionar o nivel_acesso à sessão se não existir
                session["user_level"] = usuario["nivel_acesso"]

            # Agora verificar permissões com o nível da sessão
            if session["user_level"] not in niveis_permitidos:
                if request.is_json:
                    return jsonify({"error": "Acesso não autorizado"}), 403
                flash("Você não tem permissão para acessar este recurso.", "danger")
                # Redirecionar para uma página inicial ou de erro de acesso
                return redirect(url_for("index"))

            return f(*args, **kwargs)

        return decorated_function

    return decorator


# Rota de login


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.form if request.form else request.get_json()
        if not data:
            if request.is_json:
                return jsonify({"error": "Dados de login inválidos"}), 400
            flash("Dados de login inválidos", "danger")
            return render_template("login.html")

        email = data.get("email")
        senha = data.get("senha")  # Esta é a senha em texto plano

        if not email or not senha:
            if request.is_json:
                return jsonify({"error": "Email e senha são obrigatórios"}), 400
            flash("Email e senha são obrigatórios", "danger")
            return render_template("login.html")

        db = get_db()
        # Note: SELECT * pega a senha_hash se a coluna existir
        usuario = db.execute(
            "SELECT * FROM usuario WHERE email = ?", (email,)
        ).fetchone()
        # Não feche a conexão ainda se for usá-la novamente para o UPDATE

        if not usuario:
            # Fechar a conexão antes de retornar se não for usá-la mais aqui
            db.close()
            if request.is_json:
                return jsonify({"error": "Usuário não encontrado"}), 404
            flash("Usuário não encontrado", "danger")
            return render_template("login.html")

        # ! Verificar se a senha está correta USANDO check_password_hash
        # Assumindo que a coluna com o hash da senha se chama 'senha_hash'
        # Corrigido: Acessar 'senha_hash' usando notação de dicionário
        if not check_password_hash(usuario["senha_hash"], senha):
            # Fechar a conexão antes de retornar
            db.close()
            if request.is_json:
                return jsonify({"error": "Senha incorreta"}), 401
            flash("Senha incorreta", "danger")
            return render_template("login.html")

        # Corrigido: Acessar a coluna 'ativo' do sqlite3.Row
        if not usuario["ativo"]:
            # Fechar a conexão antes de retornar
            db.close()
            if request.is_json:
                return jsonify({"error": "Usuário inativo"}), 401
            flash(
                "Sua conta está inativa. Entre em contato com o administrador.",
                "warning",
            )
            return render_template("login.html")

        # Registrar o acesso
        # Reutilizando a conexão aberta anteriormente (ou reabrindo se fechou)
        # db = get_db() # Se você fechou a conexão antes, reabra aqui
        try:
            db.execute(
                "UPDATE usuario SET ultimo_acesso = ? WHERE id = ?",
                # Corrigido: Acessando 'id' do sqlite3.Row
                (datetime.now(), usuario["id"]),
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
        session["user_id"] = usuario["id"]
        session["user_name"] = usuario["nome"]
        # Garantir que este valor é armazenado corretamente
        session["user_level"] = usuario["nivel_acesso"]
        session["user_email"] = usuario["email"]
        session.permanent = True

        next_url = request.args.get("next")
        if next_url:
            return redirect(next_url)

        if request.is_json:
            return jsonify(
                {
                    "message": "Login realizado com sucesso",
                    "user": {
                        # Corrigido: Acessando colunas usando notação de dicionário
                        "id": usuario["id"],
                        "nome": usuario["nome"],
                        "email": usuario["email"],
                        "nivel_acesso": usuario["nivel_acesso"],
                    },
                }
            )

        # Certifique-se de que 'dashboard' é o endpoint correto
        return redirect(url_for("dashboard"))

    return render_template("login.html")


# Rota de logout


@auth_bp.route("/logout")
def logout():
    session.clear()
    if request.is_json:
        return jsonify({"message": "Logout realizado com sucesso"})
    return redirect(url_for("auth.login"))


# API para gerenciar usuários (apenas admin)


@auth_bp.route("/usuarios", methods=["GET"])
@login_required
@acesso_requerido(["admin"])
def listar_usuarios():
    db = None
    try:
        db = get_db()
        usuarios_raw = db.execute(
            "SELECT id, nome, email, nivel_acesso, ativo, data_criacao, ultimo_acesso FROM usuario ORDER BY nome"
        ).fetchall()

        # CORREÇÃO PRINCIPAL: Sempre converter para lista de dicionários
        usuarios_list = [dict(u) for u in usuarios_raw] if usuarios_raw else []

        if request.is_json:
            return jsonify({"usuarios": usuarios_list})

        # Para renderização HTML, passar a lista de dicionários
        if not usuarios_list:
            # Usar info para "nenhum dado"
            flash("Nenhum usuário encontrado.", "info")

        # Passa a lista de dicionários para o template.
        # O filtro `|tojson` no template cuidará da serialização para o script injetado.
        return render_template("usuarios.html", usuarios=usuarios_list)
    except Exception as e:
        # app.logger.error(f"Erro ao listar usuários: {e}", exc_info=True)
        print(f"Erro ao listar usuários: {e}")
        flash_msg = "Erro ao carregar a lista de usuários."
        if request.is_json:
            return jsonify({"error": flash_msg, "usuarios": []}), 500
        flash(flash_msg, "danger")
        return render_template(
            "usuarios.html", usuarios=[]
        )  # Passa lista vazia em caso de erro
    finally:
        if db:
            db.close()


# API para detalhes de um usuário
@auth_bp.route("/usuarios/novo", methods=["GET", "POST"])
@login_required
@acesso_requerido(["admin"])
def novo_usuario():
    if request.method == "POST":
        data = request.form if request.form else request.get_json()

        nome = data.get("nome")
        email = data.get("email")
        senha = data.get("senha")
        # Default para operador
        nivel_acesso = data.get("nivel_acesso", "operador")

        if not all([nome, email, senha]):
            if request.is_json:
                return jsonify({"error": "Nome, email e senha são obrigatórios"}), 400
            flash("Nome, email e senha são obrigatórios", "danger")
            # Renderiza o form novamente
            return render_template("novo_usuario.html")

        db = get_db()
        userexiste = db.execute(
            "SELECT id FROM usuario WHERE email = ?", (email,)
        ).fetchone()

        if userexiste:
            db.close()
            if request.is_json:
                # Conflict
                return jsonify({"error": "Email já cadastrado"}), 409
            flash("Email já cadastrado. Tente um email diferente.", "danger")
            return render_template("novo_usuario.html")

        senha_hash = generate_password_hash(senha)

        try:
            cursor = db.execute(
                "INSERT INTO usuario (nome, email, senha_hash, nivel_acesso, ativo) VALUES (?, ?, ?, ?, ?)",
                (
                    nome,
                    email,
                    senha_hash,
                    nivel_acesso,
                    1,
                ),  # Novo usuário ativo por padrão
            )
            db.commit()
            novo_usuario_id = cursor.lastrowid

            # Para resposta JSON, buscar o usuário recém-criado
            if request.is_json:
                usuario_criado = db.execute(
                    "SELECT id, nome, email, nivel_acesso, ativo FROM usuario WHERE id = ?",
                    (novo_usuario_id,),
                ).fetchone()
                db.close()
                return (
                    jsonify(
                        {
                            "message": "Usuário cadastrado com sucesso!",
                            "usuario": dict(usuario_criado) if usuario_criado else None,
                        }
                    ),
                    201,
                )

            db.close()
            flash("Usuário cadastrado com sucesso!", "success")
            return redirect(
                url_for("auth.listar_usuarios")
            )  # Redireciona para a lista após cadastro

        except Exception as e:
            db.rollback()
            db.close()
            # app.logger.error(f"Erro ao cadastrar usuário: {e}", exc_info=True) # Use app.logger se configurado
            print(f"Erro ao cadastrar usuário: {e}")
            if request.is_json:
                return jsonify({"error": "Erro interno ao cadastrar usuário"}), 500
            flash("Ocorreu um erro ao cadastrar o usuário. Tente novamente.", "danger")
            return render_template("novo_usuario.html")

    # Método GET para /usuarios/novo
    return render_template("novo_usuario.html")


@auth_bp.route("/usuarios/<int:id>", methods=["GET", "PUT", "DELETE"])
@login_required
@acesso_requerido(["admin"])
def usuario(id):
    db = get_db()
    usuario_row = db.execute(
        "SELECT id, nome, email, nivel_acesso, ativo, data_criacao, ultimo_acesso FROM usuario WHERE id = ?",
        (id,),
    ).fetchone()

    if not usuario_row:
        db.close()
        if request.is_json:
            return jsonify({"error": "Usuário não encontrado"}), 404
        flash("Usuário não encontrado", "danger")
        return redirect(url_for("auth.listar_usuarios"))

    if request.method == "GET":
        db.close()
        # A API de detalhes sempre retorna JSON, o template de edição é separado.
        return jsonify({"usuario": dict(usuario_row)})

    elif request.method == "PUT":
        data = request.get_json()
        if not data:
            db.close()
            return jsonify({"error": "Dados não fornecidos"}), 400

        updates = {}
        params_update = []

        if "nome" in data and data["nome"].strip():
            updates["nome"] = data["nome"].strip()
        if "email" in data and data["email"].strip():
            # Verificar se o novo email já está em uso por OUTRO usuário
            email_existente = db.execute(
                "SELECT id FROM usuario WHERE email = ? AND id != ?",
                (data["email"].strip(), id),
            ).fetchone()
            if email_existente:
                db.close()
                return (
                    jsonify(
                        {"error": "Este email já está em uso por outro usuário."}),
                    409,
                )
            updates["email"] = data["email"].strip()

        if "nivel_acesso" in data and data["nivel_acesso"] in [
            "admin",
            "gerente",
            "operador",
        ]:
            updates["nivel_acesso"] = data["nivel_acesso"]

        if "ativo" in data and isinstance(data["ativo"], bool):
            updates["ativo"] = 1 if data["ativo"] else 0

        if (
            "senha" in data and data["senha"]
        ):  # Atualizar senha apenas se fornecida e não vazia
            updates["senha_hash"] = generate_password_hash(data["senha"])

        if not updates:
            db.close()
            return (
                jsonify(
                    {"message": "Nenhum dado válido para atualizar fornecido."}),
                400,
            )

        set_clauses = [f"{key} = ?" for key in updates.keys()]
        param_values = list(updates.values())
        param_values.append(id)  # Para o WHERE id = ?

        try:
            db.execute(
                f"UPDATE usuario SET {', '.join(set_clauses)} WHERE id = ?",
                param_values,
            )
            db.commit()
            usuario_atualizado = db.execute(
                "SELECT id, nome, email, nivel_acesso, ativo FROM usuario WHERE id = ?",
                (id,),
            ).fetchone()
            db.close()
            return jsonify(
                {
                    "message": "Usuário atualizado com sucesso!",
                    "usuario": dict(usuario_atualizado),
                }
            )
        except Exception as e:
            db.rollback()
            db.close()
            # app.logger.error(f"Erro ao atualizar usuário {id}: {e}", exc_info=True)
            print(f"Erro ao atualizar usuário {id}: {e}")
            return jsonify({"error": "Erro interno ao atualizar usuário"}), 500

    elif request.method == "DELETE":
        if id == session.get("user_id"):
            db.close()
            return jsonify({"error": "Não é possível excluir o próprio usuário."}), 400

        try:
            # Adicionar verificação se o usuário tem dependências (ex: movimentações, vendas)
            # Por simplicidade, vamos apenas excluir. Em um sistema real, isso seria importante.
            db.execute("DELETE FROM usuario WHERE id = ?", (id,))
            db.commit()
            db.close()
            return jsonify({"message": "Usuário excluído com sucesso!"})
        except Exception as e:
            db.rollback()
            db.close()
            # app.logger.error(f"Erro ao excluir usuário {id}: {e}", exc_info=True)
            print(f"Erro ao excluir usuário {id}: {e}")
            return jsonify({"error": "Erro interno ao excluir usuário"}), 500

    db.close()  # Fallback
    return jsonify({"error": "Método não suportado"}), 405


# Rota para página de edição de usuário (se você quiser uma página dedicada além do modal)
@auth_bp.route("/usuarios/editar/<int:id>/page", methods=["GET"])
@login_required
@acesso_requerido(["admin"])
def editar_usuario_page(id):
    db = get_db()
    usuario = db.execute(
        "SELECT id, nome, email, nivel_acesso, ativo FROM usuario WHERE id = ?", (
            id,)
    ).fetchone()
    db.close()
    if not usuario:
        flash("Usuário não encontrado.", "danger")
        return redirect(url_for("auth.listar_usuarios"))
    return render_template("editar_usuario.html", usuario=dict(usuario))


@auth_bp.route("/alterar-senha", methods=["GET", "POST"])
@login_required
def alterar_senha():
    if request.method == "POST":
        data = request.form if request.form else request.get_json()

        senha_atual = data.get("senha_atual")
        nova_senha = data.get("nova_senha")
        confirma_senha = data.get("confirma_senha")

        if not all([senha_atual, nova_senha, confirma_senha]):
            flash_msg = "Todos os campos são obrigatórios para alterar a senha."
            if request.is_json:
                return jsonify({"error": flash_msg}), 400
            flash(flash_msg, "danger")
            return render_template("alterar_senha.html")

        if nova_senha != confirma_senha:
            flash_msg = "Nova senha e confirmação não conferem."
            if request.is_json:
                return jsonify({"error": flash_msg}), 400
            flash(flash_msg, "danger")
            return render_template("alterar_senha.html")

        db = get_db()
        usuario = db.execute(
            "SELECT id, senha_hash FROM usuario WHERE id = ?", (
                session["user_id"],)
        ).fetchone()

        if not usuario:
            db.close()
            session.clear()  # Deslogar se o usuário não for encontrado
            flash_msg = "Usuário não encontrado. Sua sessão pode ter expirado."
            if request.is_json:
                return jsonify({"error": flash_msg}), 404
            flash(flash_msg, "danger")
            return redirect(url_for("auth.login"))

        if not check_password_hash(usuario["senha_hash"], senha_atual):
            db.close()
            flash_msg = "Senha atual incorreta."
            if request.is_json:
                return jsonify({"error": flash_msg}), 400
            flash(flash_msg, "danger")
            return render_template("alterar_senha.html")

        hashed_nova_senha = generate_password_hash(nova_senha)

        try:
            db.execute(
                "UPDATE usuario SET senha_hash = ? WHERE id = ?",
                (hashed_nova_senha, usuario["id"]),
            )
            db.commit()
            db.close()
            flash_msg = "Senha alterada com sucesso!"
            if request.is_json:
                return jsonify({"message": flash_msg})
            flash(flash_msg, "success")
            return redirect(url_for("dashboard"))  # Ou página de perfil
        except Exception as e:
            db.rollback()
            db.close()
            # app.logger.error(f"Erro ao alterar senha do usuário {usuario['id']}: {e}", exc_info=True)
            print(f"Erro ao alterar senha do usuário {usuario['id']}: {e}")
            flash_msg = "Ocorreu um erro ao alterar a senha. Tente novamente."
            if request.is_json:
                return jsonify({"error": flash_msg}), 500
            flash(flash_msg, "danger")
            return render_template("alterar_senha.html")

    return render_template("alterar_senha.html")


@auth_bp.route("/check", methods=["GET"])
def check_auth():
    if "user_id" in session:
        db = get_db()
        usuario = db.execute(
            "SELECT id, nome, email, nivel_acesso, ativo FROM usuario WHERE id = ?",
            (session["user_id"],),
        ).fetchone()
        db.close()

        if usuario and usuario["ativo"]:
            return jsonify({"authenticated": True, "user": dict(usuario)})
    return jsonify({"authenticated": False}), 401
