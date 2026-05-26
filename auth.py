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


auth_bp = Blueprint("auth", __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            if request.is_json:
                return jsonify({"error": "Autenticação necessária"}), 401
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)

    return decorated_function


def acesso_requerido(niveis_permitidos):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                if request.is_json:
                    return jsonify({"error": "Autenticação necessária"}), 401
                return redirect(url_for("auth.login", next=request.url))

            if "user_level" not in session:
                db = get_db()
                usuario = db.execute(
                    "SELECT * FROM usuario WHERE id = ?", (session["user_id"],)
                ).fetchone()
                db.close()

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

                session["user_level"] = usuario["nivel_acesso"]

            if session["user_level"] not in niveis_permitidos:
                if request.is_json:
                    return jsonify({"error": "Acesso não autorizado"}), 403
                flash("Você não tem permissão para acessar este recurso.", "danger")

                return redirect(url_for("index"))

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def acesso_requerido_com_hierarquia(niveis_permitidos):
    """Decorador que verifica nível de acesso + hierarquia.
    - Admin: pode acessar tudo
    - Gerente: pode acessar apenas usuários com manager_id igual ao seu user_id
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                if request.is_json:
                    return jsonify({"error": "Autenticação necessária"}), 401
                return redirect(url_for("auth.login", next=request.url))

            if "user_level" not in session:
                db = get_db()
                usuario = db.execute(
                    "SELECT * FROM usuario WHERE id = ?", (session["user_id"],)
                ).fetchone()
                db.close()

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

                session["user_level"] = usuario["nivel_acesso"]

            if session["user_level"] not in niveis_permitidos:
                if request.is_json:
                    return jsonify({"error": "Acesso não autorizado"}), 403
                flash("Você não tem permissão para acessar este recurso.", "danger")
                return redirect(url_for("index"))

            return f(*args, **kwargs)

        return decorated_function

    return decorator


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
        senha = data.get("senha")

        if not email or not senha:
            if request.is_json:
                return jsonify({"error": "Email e senha são obrigatórios"}), 400
            flash("Email e senha são obrigatórios", "danger")
            return render_template("login.html")

        db = get_db()

        usuario = db.execute(
            "SELECT * FROM usuario WHERE email = ?", (email,)
        ).fetchone()

        if not usuario:

            db.close()
            if request.is_json:
                return jsonify({"error": "Usuário não encontrado"}), 404
            flash("Usuário não encontrado", "danger")
            return render_template("login.html")

        if not check_password_hash(usuario["senha_hash"], senha):

            db.close()
            if request.is_json:
                return jsonify({"error": "Senha incorreta"}), 401
            flash("Senha incorreta", "danger")
            return render_template("login.html")

        if not usuario["ativo"]:

            db.close()
            if request.is_json:
                return jsonify({"error": "Usuário inativo"}), 401
            flash(
                "Sua conta está inativa. Entre em contato com o administrador.",
                "warning",
            )
            return render_template("login.html")

        try:
            db.execute(
                "UPDATE usuario SET ultimo_acesso = ? WHERE id = ?",
                (datetime.now(), usuario["id"]),
            )
            db.commit()
        except Exception as e:

            print(f"Erro ao atualizar ultimo_acesso: {e}")
            db.rollback()
        finally:
            db.close()

        session["user_id"] = usuario["id"]
        session["user_name"] = usuario["nome"]
        session["nome_usuario"] = usuario["nome"]

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
                        "id": usuario["id"],
                        "nome": usuario["nome"],
                        "email": usuario["email"],
                        "nivel_acesso": usuario["nivel_acesso"],
                    },
                }
            )

        return redirect(url_for("dashboard"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    if request.is_json:
        return jsonify({"message": "Logout realizado com sucesso"})
    return redirect(url_for("auth.login"))


@auth_bp.route("/usuarios", methods=["GET"])
@login_required
@acesso_requerido(["admin"])
def listar_usuarios():
    db = None
    try:
        accepts = request.accept_mimetypes
        wants_json = (
            request.is_json
            or request.headers.get("X-Requested-With") == "XMLHttpRequest"
            or (
                accepts["application/json"] >= accepts["text/html"]
                and accepts["application/json"] > 0
            )
        )

        db = get_db()
        usuarios_raw = db.execute(
            "SELECT id, nome, email, nivel_acesso, ativo, data_criacao, ultimo_acesso FROM usuario ORDER BY nome"
        ).fetchall()

        usuarios_list = [dict(u) for u in usuarios_raw] if usuarios_raw else []

        if wants_json:
            return jsonify({"usuarios": usuarios_list})

        if not usuarios_list:

            flash("Nenhum usuário encontrado.", "info")

        return render_template("usuarios.html", usuarios=usuarios_list)
    except Exception as e:

        print(f"Erro ao listar usuários: {e}")
        flash_msg = "Erro ao carregar a lista de usuários."
        accepts = request.accept_mimetypes
        wants_json = request.is_json or (
            accepts["application/json"] >= accepts["text/html"]
            and accepts["application/json"] > 0
        )
        if wants_json:
            return jsonify({"error": flash_msg, "usuarios": []}), 500
        flash(flash_msg, "danger")
        return render_template("usuarios.html", usuarios=[])
    finally:
        if db:
            db.close()


@auth_bp.route("/usuarios/novo", methods=["GET", "POST"])
@login_required
@acesso_requerido(["admin"])
def novo_usuario():
    if request.method == "POST":
        data = request.form if request.form else request.get_json()

        nome = data.get("nome")
        email = data.get("email")
        senha = data.get("senha")

        nivel_acesso = data.get("nivel_acesso", "operador")

        if not all([nome, email, senha]):
            if request.is_json:
                return jsonify({"error": "Nome, email e senha são obrigatórios"}), 400
            flash("Nome, email e senha são obrigatórios", "danger")

            return render_template("novo_usuario.html")

        db = get_db()
        userexiste = db.execute(
            "SELECT id FROM usuario WHERE email = ?", (email,)
        ).fetchone()

        if userexiste:
            db.close()
            if request.is_json:

                return jsonify({"error": "Email já cadastrado"}), 409
            flash("Email já cadastrado. Tente um email diferente.", "danger")
            return render_template("novo_usuario.html")

        senha_hash = generate_password_hash(senha)

        try:

            manager_id = None
            if session.get("user_level") == "gerente":
                manager_id = session.get("user_id")

            cursor = db.execute(
                "INSERT INTO usuario (nome, email, senha_hash, nivel_acesso, ativo, manager_id) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    nome,
                    email,
                    senha_hash,
                    nivel_acesso,
                    1,
                    manager_id,
                ),
            )
            db.commit()
            novo_usuario_id = cursor.lastrowid

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
            return redirect(url_for("auth.listar_usuarios"))

        except Exception as e:
            db.rollback()
            db.close()

            print(f"Erro ao cadastrar usuário: {e}")
            if request.is_json:
                return jsonify({"error": "Erro interno ao cadastrar usuário"}), 500
            flash("Ocorreu um erro ao cadastrar o usuário. Tente novamente.", "danger")
            return render_template("novo_usuario.html")

    return render_template("novo_usuario.html")


@auth_bp.route("/usuarios/<int:id>", methods=["GET", "PUT", "DELETE"])
@login_required
def usuario(id):
    db = get_db()

    usuario_row = db.execute(
        "SELECT id, nome, email, nivel_acesso, ativo, data_criacao, ultimo_acesso, manager_id FROM usuario WHERE id = ?",
        (id,),
    ).fetchone()

    if not usuario_row:
        db.close()
        if request.is_json:
            return jsonify({"error": "Usuário não encontrado"}), 404
        flash("Usuário não encontrado", "danger")
        return redirect(url_for("auth.listar_usuarios"))

    user_level = session.get("user_level")
    user_id = session.get("user_id")

    if user_level not in ["admin", "gerente"]:
        db.close()
        if request.is_json:
            return jsonify({"error": "Acesso não autorizado"}), 403
        flash("Você não tem permissão para acessar este recurso.", "danger")
        return redirect(url_for("auth.listar_usuarios"))

    if user_level == "gerente" and usuario_row["manager_id"] != user_id:
        db.close()
        if request.is_json:
            return (
                jsonify(
                    {"error": "Você só pode editar seus próprios subordinados."}),
                403,
            )
        flash("Você só pode editar seus próprios subordinados.", "danger")
        return redirect(url_for("auth.listar_usuarios"))

    if request.method == "GET":
        db.close()

        return jsonify({"usuario": dict(usuario_row)})

    elif request.method == "PUT":
        data = request.get_json()
        if not data:
            db.close()
            return jsonify({"error": "Dados não fornecidos"}), 400

        updates = {}

        if "nome" in data and data["nome"].strip():
            updates["nome"] = data["nome"].strip()
        if "email" in data and data["email"].strip():

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

        if "senha" in data and data["senha"]:
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
        param_values.append(id)

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

            print(f"Erro ao atualizar usuário {id}: {e}")
            return jsonify({"error": "Erro interno ao atualizar usuário"}), 500

    elif request.method == "DELETE":
        if id == session.get("user_id"):
            db.close()
            return jsonify({"error": "Não é possível excluir o próprio usuário."}), 400

        try:

            db.execute("DELETE FROM usuario WHERE id = ?", (id,))
            db.commit()
            db.close()
            return jsonify({"message": "Usuário excluído com sucesso!"})
        except Exception as e:
            db.rollback()
            db.close()

            print(f"Erro ao excluir usuário {id}: {e}")
            return jsonify({"error": "Erro interno ao excluir usuário"}), 500

    db.close()
    return jsonify({"error": "Método não suportado"}), 405


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
            session.clear()
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
            return redirect(url_for("dashboard"))
        except Exception as e:
            db.rollback()
            db.close()

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
