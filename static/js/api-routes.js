const API_ROUTES = {
  AUTH_LOGIN: "/auth/login",
  AUTH_LOGOUT: "/auth/logout",
  AUTH_CHECK: "/auth/check",
  AUTH_ALTERAR_SENHA: "/auth/alterar-senha",

  USUARIOS_LISTAR: "/auth/usuarios",
  USUARIO_NOVO: "/auth/usuarios/novo",
  USUARIO_DETALHES: (id) => `/auth/usuarios/${id}`,

  DASHBOARD_STATS: "/api/dashboard/stats",

  PRODUTOS_LISTAR: "/produtos/",
  PRODUTO_DETALHES: (id) => `/produtos/${id}`,
  PRODUTO_ALTERNAR_STATUS: (id) => `/produtos/${id}/alternar-status`,
  PRODUTOS_BUSCA: "/produtos/busca",
  PRODUTOS_MAIS_VENDIDOS: "/produtos/mais-vendidos",
  PRODUTOS_MENOS_VENDIDOS: "/produtos/menos-vendidos",

  CATEGORIAS_LISTAR: "/produtos/categorias",
  CATEGORIA_DETALHES: (id) => `/produtos/categorias/${id}`,

  FORNECEDORES_LISTAR: "/fornecedores/",
  FORNECEDOR_DETALHES: (id) => `/fornecedores/${id}`,
  FORNECEDOR_PRODUTOS: (id) => `/fornecedores/${id}/produtos`,
  FORNECEDOR_ALTERNAR_STATUS: (id) => `/fornecedores/${id}/alternar-status`,

  ESTOQUE_MOVIMENTACOES_LISTAR: "/estoque/movimentacoes",
  ESTOQUE_MOVIMENTACOES_GRAFICO: "/estoque/movimentacoes/grafico",
  ESTOQUE_ENTRADA: "/estoque/entrada",
  ESTOQUE_SAIDA: "/estoque/saida",
  ESTOQUE_AJUSTE: "/estoque/ajuste",

  VENDAS_LISTAR_REGISTRAR: "/estoque/vendas",
  VENDA_DETALHES: (id) => `/estoque/vendas/${id}`,
  VENDA_CANCELAR: (id) => `/estoque/vendas/${id}/cancelar`,

  RELATORIOS_VENDAS_PRODUTOS: "/relatorios/vendas/produtos",
  RELATORIOS_ESTOQUE_NIVEIS: "/relatorios/estoque/niveis",
};

Object.freeze(API_ROUTES);
