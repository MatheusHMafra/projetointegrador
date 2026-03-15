/**
 * GEP - Script para a página de Movimentações de Estoque
 */

document.addEventListener('DOMContentLoaded', () => {
    if (typeof API_ROUTES === 'undefined' || !API_ROUTES.ESTOQUE_MOVIMENTACOES_LISTAR) {
        console.error("API_ROUTES ou API_ROUTES.ESTOQUE_MOVIMENTACOES_LISTAR não definido.");
        showNotification("Erro de configuração de API. Verifique o console.", "danger");
        return;
    }

    carregarMovimentacoes();
    configurarFiltrosMovimentacoes();
    // Futuramente: carregarProdutosParaFiltro();
});

let currentPageMov = 1;
const perPageMov = 15; // Ou pegar de um seletor na página

/**
 * Carrega as movimentações da API e atualiza a tabela e paginação.
 * @param {number} page - Número da página a ser carregada.
 * @param {object} filtros - Objeto contendo os filtros a serem aplicados.
 */
function carregarMovimentacoes(page = 1, filtros = {}) {
    currentPageMov = page;
    const spinner = document.getElementById('loading-spinner-mov');
    const placeholder = document.getElementById('movimentacoes-placeholder');
    const tabelaCorpo = document.getElementById('movimentacoes-tabela-corpo');
    const paginacaoNav = document.getElementById('paginacao-movimentacoes-nav');

    if (spinner) spinner.style.display = 'inline-block';
    if (placeholder) placeholder.textContent = 'Carregando movimentações...';
    if (tabelaCorpo) tabelaCorpo.innerHTML = ''; // Limpa a tabela antes de carregar

    let params = { page: currentPageMov, per_page: perPageMov, ...filtros };

    // Limpar parâmetros vazios
    Object.keys(params).forEach(key => {
        if (params[key] === '' || params[key] === null || params[key] === undefined) {
            delete params[key];
        }
    });
    
    // Tratar filtro de produto (ID ou Nome)
    // A API /estoque/movimentacoes espera produto_id. Se for nome, precisaria de uma busca prévia.
    // Por simplicidade, vamos assumir que o backend pode lidar com 'produto_id_ou_nome' ou adaptamos aqui.
    // Se o backend só aceita produto_id, e o usuário digitou um nome, teríamos que:
    // 1. Buscar o ID do produto pelo nome (usando API_ROUTES.PRODUTOS_BUSCA)
    // 2. Se encontrado, usar o ID no filtro. Se não, mostrar aviso.
    // Por ora, vamos enviar o que foi digitado e deixar o backend tratar ou ajustar depois.
    if (params.produto_id_ou_nome) {
        // Se o backend espera 'produto_id' e o valor é numérico, usamos.
        // Se não, e o backend não trata busca por nome aqui, precisaria de lógica adicional.
        // Para este exemplo, vamos renomear para 'produto_id' se for numérico,
        // ou manter como está se o backend for adaptado.
        // A API atual espera 'produto_id' como int.
        if (!isNaN(parseInt(params.produto_id_ou_nome))) {
            params.produto_id = parseInt(params.produto_id_ou_nome);
        } else {
            // Se não for numérico, a API atual não vai filtrar por nome diretamente aqui.
            // Poderia exibir uma mensagem ou tentar buscar o ID.
            // Por ora, vamos remover se não for ID para evitar erro na API.
            // Idealmente, o backend lidaria com isso ou teríamos uma busca de produto aqui.
            console.warn("Filtro por nome de produto não implementado diretamente na API de movimentações. Filtro por nome ignorado.");
            delete params.produto_id_ou_nome; // Remove se não for ID
        }
        delete params.produto_id_ou_nome; // Remove o original
    }


    axios.get(API_ROUTES.ESTOQUE_MOVIMENTACOES_LISTAR, { params })
        .then(response => {
            const data = response.data;
            if (data && data.movimentacoes) {
                montarTabelaMovimentacoes(data.movimentacoes);
                montarPaginacaoMovimentacoes(data.total, data.pages, data.page, data.per_page);
                if (data.movimentacoes.length === 0 && placeholder) {
                    placeholder.textContent = 'Nenhuma movimentação encontrada para os filtros aplicados.';
                    tabelaCorpo.innerHTML = `<tr><td colspan="10" class="text-center">${placeholder.textContent}</td></tr>`;
                }
                 if (paginacaoNav) paginacaoNav.style.display = data.movimentacoes.length > 0 ? 'block' : 'none';
            } else {
                 if (placeholder) placeholder.textContent = 'Não foi possível carregar as movimentações.';
                 if (tabelaCorpo) tabelaCorpo.innerHTML = `<tr><td colspan="10" class="text-center">${placeholder.textContent}</td></tr>`;
            }
        })
        .catch(error => {
            console.error('Erro ao carregar movimentações:', error);
            const errorMsg = error.response?.data?.error || 'Falha ao carregar movimentações.';
            showNotification(errorMsg, 'danger');
            if (placeholder) placeholder.textContent = errorMsg;
            if (tabelaCorpo) tabelaCorpo.innerHTML = `<tr><td colspan="10" class="text-center text-danger">${errorMsg}</td></tr>`;
        })
        .finally(() => {
            if (spinner) spinner.style.display = 'none';
        });
}

/**
 * Popula a tabela de movimentações com os dados recebidos.
 * @param {Array} movimentacoes - Array de objetos de movimentação.
 */
function montarTabelaMovimentacoes(movimentacoes) {
    const tabelaCorpo = document.getElementById('movimentacoes-tabela-corpo');
    if (!tabelaCorpo) return;
    tabelaCorpo.innerHTML = ''; // Limpar antes de adicionar

    if (movimentacoes.length === 0) {
        tabelaCorpo.innerHTML = '<tr><td colspan="10" class="text-center">Nenhuma movimentação encontrada.</td></tr>';
        return;
    }

    movimentacoes.forEach(mov => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${mov.id}</td>
            <td>
                ${mov.produto ? `${mov.produto.nome || 'N/A'} <small class="text-muted d-block">(${mov.produto.codigo || 'S/Cód.'})</small>` : 'Produto não encontrado'}
            </td>
            <td><span class="badge bg-${getBadgeClassForTipo(mov.tipo)}">${mov.tipo.charAt(0).toUpperCase() + mov.tipo.slice(1)}</span></td>
            <td>${mov.quantidade}</td>
            <td>${mov.estoque_anterior !== null ? mov.estoque_anterior : 'N/A'}</td>
            <td>${mov.estoque_atual !== null ? mov.estoque_atual : 'N/A'}</td>
            <td>${mov.data || 'N/A'}</td>
            <td>${mov.usuario ? mov.usuario.nome || 'Sistema' : 'Sistema'}</td>
            <td class="text-truncate" style="max-width: 150px;" title="${mov.observacao || ''}">${mov.observacao || '-'}</td>
            <td>${mov.venda_codigo || '-'}</td>
        `;
        tabelaCorpo.appendChild(tr);
    });
}

/**
 * Retorna a classe do badge Bootstrap baseada no tipo de movimentação.
 * @param {string} tipo - O tipo da movimentação.
 * @returns {string} - A classe CSS do badge.
 */
function getBadgeClassForTipo(tipo) {
    switch (tipo) {
        case 'entrada': return 'success';
        case 'saida': return 'danger';
        case 'ajuste': return 'info';
        case 'venda': return 'warning';
        default: return 'secondary';
    }
}

/**
 * Monta os controles de paginação.
 * @param {number} totalItems - Total de itens.
 * @param {number} totalPages - Total de páginas.
 * @param {number} currentPage - Página atual.
 * @param {number} itemsPerPage - Itens por página.
 */
function montarPaginacaoMovimentacoes(totalItems, totalPages, currentPage, itemsPerPage) {
    const paginacaoLista = document.getElementById('paginacao-movimentacoes-lista');
    const paginacaoNav = document.getElementById('paginacao-movimentacoes-nav');

    if (!paginacaoLista || !paginacaoNav) return;
    paginacaoLista.innerHTML = '';

    if (totalPages <= 1) {
        paginacaoNav.style.display = 'none';
        return;
    }
    paginacaoNav.style.display = 'block';

    // Botão "Anterior"
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
    prevLi.innerHTML = `<a class="page-link" href="#" data-page="${currentPage - 1}">Anterior</a>`;
    if (currentPage > 1) {
        prevLi.querySelector('a').addEventListener('click', (e) => {
            e.preventDefault();
            carregarMovimentacoes(currentPage - 1, getCurrentFiltersMov());
        });
    }
    paginacaoLista.appendChild(prevLi);

    // Números das páginas (simplificado)
    // Idealmente, adicionar lógica para "..." se houver muitas páginas
    let inicio = Math.max(1, currentPage - 2);
    let fim = Math.min(totalPages, currentPage + 2);

    if (currentPage <= 3) { // Se estiver nas primeiras páginas, mostrar até 5
        fim = Math.min(totalPages, 5);
    }
    if (currentPage >= totalPages - 2) { // Se estiver nas últimas páginas, mostrar as últimas 5
        inicio = Math.max(1, totalPages - 4);
    }


    for (let i = inicio; i <= fim; i++) {
        const li = document.createElement('li');
        li.className = `page-item ${i === currentPage ? 'active' : ''}`;
        li.innerHTML = `<a class="page-link" href="#" data-page="${i}">${i}</a>`;
        if (i !== currentPage) {
            li.querySelector('a').addEventListener('click', (e) => {
                e.preventDefault();
                carregarMovimentacoes(i, getCurrentFiltersMov());
            });
        }
        paginacaoLista.appendChild(li);
    }
    
    // Botão "Próximo"
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
    nextLi.innerHTML = `<a class="page-link" href="#" data-page="${currentPage + 1}">Próximo</a>`;
    if (currentPage < totalPages) {
        nextLi.querySelector('a').addEventListener('click', (e) => {
            e.preventDefault();
            carregarMovimentacoes(currentPage + 1, getCurrentFiltersMov());
        });
    }
    paginacaoLista.appendChild(nextLi);
}

/**
 * Configura os event listeners para os filtros.
 */
function configurarFiltrosMovimentacoes() {
    const formFiltros = document.getElementById('filtros-movimentacoes-form');
    const btnLimparFiltros = document.getElementById('limpar-filtros');

    if (formFiltros) {
        formFiltros.addEventListener('submit', (event) => {
            event.preventDefault();
            carregarMovimentacoes(1, getCurrentFiltersMov());
        });
    }

    if (btnLimparFiltros) {
        btnLimparFiltros.addEventListener('click', () => {
            if (formFiltros) formFiltros.reset();
            carregarMovimentacoes(1, {}); // Carrega sem filtros
        });
    }
}

/**
 * Obtém os valores atuais dos campos de filtro.
 * @returns {object} - Objeto com os filtros.
 */
function getCurrentFiltersMov() {
    const filtros = {};
    const produtoInput = document.getElementById('filtro-produto');
    const tipoSelect = document.getElementById('filtro-tipo');
    const dataInicioInput = document.getElementById('filtro-data-inicio');
    const dataFimInput = document.getElementById('filtro-data-fim');

    if (produtoInput && produtoInput.value.trim()) {
        // A API espera 'produto_id'. Se o usuário digitar um nome, precisaria de uma busca de ID.
        // Por ora, se for número, envia como produto_id. Se for texto, o backend precisaria tratar.
        // A lógica de tratamento está em carregarMovimentacoes. Aqui só coletamos.
        filtros.produto_id_ou_nome = produtoInput.value.trim();
    }
    if (tipoSelect && tipoSelect.value) {
        filtros.tipo = tipoSelect.value;
    }
    if (dataInicioInput && dataInicioInput.value) {
        filtros.data_inicio = dataInicioInput.value;
    }
    if (dataFimInput && dataFimInput.value) {
        filtros.data_fim = dataFimInput.value;
    }
    return filtros;
}

// Funções utilitárias globais (showNotification, toggleLoading) são esperadas de app.js ou similar.
// Se não existirem, precisarão ser definidas ou importadas.
// Exemplo de showNotification (se não existir globalmente):
/*
if (typeof showNotification === 'undefined') {
    function showNotification(message, type = 'info') {
        console.log(`Notification (${type}): ${message}`);
        // Implementar uma notificação visual real aqui
        const notificationArea = document.getElementById('notification-area'); // Supondo que exista
        if (notificationArea) {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
            alertDiv.role = 'alert';
            alertDiv.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            notificationArea.appendChild(alertDiv);
            setTimeout(() => alertDiv.remove(), 5000);
        }
    }
}
*/
