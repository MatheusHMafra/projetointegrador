/**
 * EstoquePro - Mapeamento de Rotas da API
 * 
 * Este arquivo contém o mapeamento de todas as rotas da API,
 * facilitando atualizações em um único lugar.
 */

/*
const API_ROUTES = {
    // Dashboard
    DASHBOARD_STATS: '/api/dashboard/stats',
    
    // Produtos
    PRODUTOS_LISTAR: '/produtos',
    PRODUTOS_BUSCAR: '/produtos/busca',
    PRODUTOS_ESTOQUE_BAIXO: '/produtos/estoque-baixo',
    PRODUTO_DETALHES: (id) => `/produtos/${id}`,
    
    // Categorias
    CATEGORIAS_LISTAR: '/produtos/categorias',
    CATEGORIA_DETALHES: (id) => `/produtos/categorias/${id}`,
    
    // Estoque
    ESTOQUE_ENTRADA: '/estoque/entrada',
    ESTOQUE_SAIDA: '/estoque/saida',
    ESTOQUE_AJUSTE: '/estoque/ajuste',
    ESTOQUE_MOVIMENTACOES: '/estoque/movimentacoes',
    ESTOQUE_GRAFICO: '/estoque/movimentacoes/grafico',
    
    // Vendas
    VENDAS_LISTAR: '/estoque/vendas',
    VENDA_DETALHES: (id) => `/estoque/vendas/${id}`,
    VENDA_CANCELAR: (id) => `/estoque/vendas/${id}/cancelar`,
    
    // Fornecedores
    FORNECEDORES_LISTAR: '/fornecedores',
    FORNECEDOR_DETALHES: (id) => `/fornecedores/${id}`,
    FORNECEDOR_ALTERNAR_STATUS: (id) => `/fornecedores/${id}/alternar-status`,
    
    // Relatórios
    RELATORIOS: '/relatorios'
};
*/
const API_ROUTES = {
    stats: '/api/dashboard/stats',
    produtos: '/produtos',
    categorias: '/categorias',
    fornecedores: '/fornecedores',
    movimentacoesRecentes: '/estoque/movimentacoes',
    produtosMaisVendidos: '/produtos/mais-vendidos',
    produtosMenosVendidos: '/produtos/menos-vendidos',
    // Adicione outras rotas da sua API aqui
};

// Opcional: Congela o objeto para evitar modificações acidentais
Object.freeze(API_ROUTES);
