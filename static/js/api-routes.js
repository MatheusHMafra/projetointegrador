/**
 * EstoquePro - Mapeamento de Rotas da API
 *
 * Este arquivo contém o mapeamento de todas as rotas da API,
 * facilitando atualizações em um único lugar.
 */

const API_ROUTES = {
  // Autenticação
  AUTH_LOGIN: "/auth/login", // Example, not used by dashboard.js directly
  AUTH_CHECK: "/auth/check", // Example

  // Dashboard
  DASHBOARD_STATS: "/api/dashboard/stats", // Used by carregarEstatisticas, carregarProdutosEstoqueBaixoCard
  // Matches @app.route('/api/dashboard/stats') in app.py

  // Produtos
  PRODUTOS_LISTAR: "/produtos", // Matches @produtos_bp.route('/')
  PRODUTO_DETALHES: (id) => `/produtos/${id}`, // Example
  PRODUTOS_BUSCA: "/produtos/busca", // Matches @produtos_bp.route('/busca')
  PRODUTOS_ESTOQUE_BAIXO_LISTA: "/produtos/estoque-baixo", // For a list, if different from stats
  // Matches @produtos_bp.route('/estoque-baixo')
  PRODUTOS_MAIS_VENDIDOS: "/produtos/mais-vendidos", // Matches @produtos_bp.route('/mais-vendidos')
  PRODUTOS_MENOS_VENDIDOS: "/produtos/menos-vendidos", // Matches @produtos_bp.route('/menos-vendidos')

  // Categorias
  CATEGORIAS_LISTAR: "/produtos/categorias", // Matches @produtos_bp.route('/categorias')

  // Fornecedores
  FORNECEDORES_LISTAR: "/fornecedores", // Matches @fornecedores_bp.route('/')

  // Estoque / Movimentações
  ESTOQUE_MOVIMENTACOES_LISTAR: "/estoque/movimentacoes", // Matches @estoque_bp.route('/movimentacoes')
  ESTOQUE_MOVIMENTACOES_GRAFICO: "/estoque/movimentacoes/grafico", // Matches @estoque_bp.route('/movimentacoes/grafico')
  // Used by criarGraficoMovimentacao

  // Vendas
  VENDAS_LISTAR_REGISTRAR: "/estoque/vendas", // Matches @estoque_bp.route('/vendas')

  // Relatórios (se a rota /relatorios/vendas/produtos for a principal de relatórios para o dashboard)
  RELATORIOS_VENDAS_PRODUTOS: "/relatorios/vendas/produtos", // Matches @relatorios_bp.route('/vendas/produtos')

  // Adicione outras rotas conforme necessário
};

// Opcional: Congela o objeto para evitar modificações acidentais
Object.freeze(API_ROUTES);
