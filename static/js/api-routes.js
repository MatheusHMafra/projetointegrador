/**
 * EstoquePro - Mapeamento de Rotas da API
 *
 * Este arquivo contém o mapeamento de todas as rotas da API,
 * facilitando atualizações em um único lugar.
 */

const API_ROUTES = {
  // Autenticação
  AUTH_LOGIN: "/auth/login", 
  AUTH_LOGOUT: "/auth/logout", // Added for completeness, though sidebar uses url_for
  AUTH_CHECK: "/auth/check", 

  // Dashboard
  DASHBOARD_STATS: "/api/dashboard/stats", 

  // Produtos
  PRODUTOS_LISTAR: "/produtos/", // Base route for GET (list) and POST (add)
  PRODUTO_DETALHES: (id) => `/produtos/${id}`, // For GET (details), PUT (update), DELETE
  PRODUTOS_BUSCA: "/produtos/busca", 
  // PRODUTOS_ESTOQUE_BAIXO_LISTA: "/produtos/estoque-baixo", // This might be part of DASHBOARD_STATS or a specific filter on PRODUTOS_LISTAR
  PRODUTOS_MAIS_VENDIDOS: "/produtos/mais-vendidos", 
  PRODUTOS_MENOS_VENDIDOS: "/produtos/menos-vendidos", 

  // Categorias
  CATEGORIAS_LISTAR: "/produtos/categorias", // For GET (list) and POST (add)
  CATEGORIA_DETALHES: (id) => `/produtos/categorias/${id}`, // For GET (details), PUT, DELETE

  // Fornecedores
  FORNECEDORES_LISTAR: "/fornecedores/", // Base route for GET (list) and POST (add)
  FORNECEDOR_DETALHES: (id) => `/fornecedores/${id}`, // For GET (details), PUT, DELETE
  FORNECEDOR_PRODUTOS: (id) => `/fornecedores/${id}/produtos`, // To list products of a specific supplier
  FORNECEDOR_ALTERNAR_STATUS: (id) => `/fornecedores/${id}/alternar-status`, // To toggle active/inactive status

  // Estoque / Movimentações
  ESTOQUE_MOVIMENTACOES_LISTAR: "/estoque/movimentacoes", 
  ESTOQUE_MOVIMENTACOES_GRAFICO: "/estoque/movimentacoes/grafico", 
  ESTOQUE_ENTRADA: "/estoque/entrada",
  ESTOQUE_SAIDA: "/estoque/saida",
  ESTOQUE_AJUSTE: "/estoque/ajuste",

  // Vendas
  VENDAS_LISTAR_REGISTRAR: "/estoque/vendas", // For GET (list) and POST (add)
  VENDA_DETALHES: (id) => `/estoque/vendas/${id}`, // For GET (details)
  VENDA_CANCELAR: (id) => `/estoque/vendas/${id}/cancelar`, // For POST (cancel)


  // Relatórios
  RELATORIOS_VENDAS_PRODUTOS: "/relatorios/vendas/produtos", 
  RELATORIOS_ESTOQUE_NIVEIS: "/relatorios/estoque/niveis",

  // Adicione outras rotas conforme necessário
};

// Opcional: Congela o objeto para evitar modificações acidentais
Object.freeze(API_ROUTES);
