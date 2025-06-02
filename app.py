from flask import Flask, jsonify, render_template, redirect, url_for, session, request
from models import init_db_sqlite
from database_utils import inicializar_dados_exemplo, obter_estatisticas
from datetime import timedelta, datetime
import logging
from logging.handlers import RotatingFileHandler
import os
from dotenv import load_dotenv

# ---- Importar blueprints ----
from auth import auth_bp
from produtos import produtos_bp
from estoque import estoque_bp
from fornecedores import fornecedores_bp
from relatorios import relatorios_bp


# Carregar variáveis de ambiente
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configuração do SQLite
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24).hex())
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') != 'development'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
    
    # Configurar logs
    if not os.path.exists('logs'):
        os.makedirs('logs')
    log_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=3)
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_handler.setFormatter(log_formatter)
    app.logger.addHandler(log_handler)
    app.logger.setLevel(logging.INFO)
    
    # Registrar blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(produtos_bp, url_prefix='/produtos')
    app.register_blueprint(estoque_bp, url_prefix='/estoque')
    app.register_blueprint(relatorios_bp, url_prefix='/relatorios')
    app.register_blueprint(fornecedores_bp, url_prefix='/fornecedores')
    
    # Criar tabelas se não existirem
    with app.app_context():
        init_db_sqlite()

    # Verificação de login antes de cada requisição
    @app.before_request
    def require_login():
        # Permitir acesso a rotas de autenticação, arquivos estáticos e inicialização de dados
        allowed_endpoints = ['auth.login', 'static', 'init_data']
        if request.endpoint and (request.endpoint.startswith('auth.') or request.endpoint in allowed_endpoints or request.endpoint == 'static'):
            return  # Permitir acesso

        if 'user_id' not in session:
            # Se for uma requisição JSON, retornar erro (opcional, mas bom para APIs)
            if request.is_json:
                 return jsonify({"error": "Autenticação necessária"}), 401
            # Redirecionar para a página de login para requisições normais
            return redirect(url_for('auth.login'))

    # Rota principal
    @app.route('/')
    def index():
        # A verificação before_request cuidará do redirecionamento se não estiver logado
        return redirect(url_for('dashboard'))
    
    # Dashboard
    @app.route('/dashboard')
    # @login_required # Decorator não é mais estritamente necessário aqui devido ao before_request
    def dashboard():
        now = datetime.now()
        return render_template('dashboard.html', now=now)
    
    # Dados do dashboard
    @app.route('/api/dashboard/stats')
    # @login_required # Decorator não é mais estritamente necessário aqui devido ao before_request
    def dashboard_stats():
        with app.app_context():
            estatisticas = obter_estatisticas()
        return jsonify(estatisticas)
    
    # Inicialização de dados (para desenvolvimento) - Já permitido pelo before_request
    @app.route('/api/init-data', methods=['GET'])
    def init_data():
        sucesso = inicializar_dados_exemplo()
        if sucesso:
            app.logger.info('Dados de exemplo inicializados com sucesso')
        else:
            app.logger.error("Erro ao inicializar dados de exemplo.")

    app.logger.info('Aplicação iniciada com sucesso')
    return app

# Para uso com o Flask CLI
app = create_app()

if __name__ == '__main__':
    # Iniciar a aplicação
    port = int(os.environ.get('PORT', 80))
    app.run(host='0.0.0.0', port=port)
