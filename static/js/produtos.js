/**
 * EstoquePro - Gerenciamento de Produtos
 * 
 * Script para a página de listagem e gerenciamento de produtos (produtos.html).
 */

// Configuração global do Axios (se não estiver em app.js)
// axios.defaults.headers.post['Content-Type'] = 'application/json';

// Estado da página
let currentPage = 1;
let totalPages = 1;
let currentFilters = {
    categoria_id: '',
    fornecedor_id: '',
    estoque_baixo: false,
    termo: ''
};

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    // Carregar dados iniciais
    carregarOpcoesCategorias('filtro-categoria');
    carregarOpcoesFornecedores('filtro-fornecedor');
    carregarProdutos(); // Carrega a primeira página sem filtros

    // Configurar eventos
    configurarFiltros();
    configurarBusca();
    configurarModais();

    // Esconder spinner inicial (pode ser melhorado para esconder após o carregamento)
    // toggleLoading(false); // Assumindo que toggleLoading está em app.js
});

/**
 * Carrega as opções de categoria nos selects fornecidos.
 * @param {string} selectId - ID do elemento select para categorias.
 */
function carregarOpcoesCategorias(selectId) {
    const select = document.getElementById(selectId);
    if (!select) return;

    axios.get('/categorias') // Ajuste a rota se necessário
        .then(response => {
            select.innerHTML = '<option value="">Todas as Categorias</option>'; // Opção padrão
            response.data.forEach(cat => {
                select.innerHTML += `<option value="${cat.id}">${cat.nome}</option>`;
            });
        })
        .catch(error => {
            console.error(`Erro ao carregar categorias para ${selectId}:`, error);
            select.innerHTML = '<option value="">Erro ao carregar</option>';
            showNotification('Erro ao carregar categorias.', 'danger');
        });
}

/**
 * Carrega as opções de fornecedores nos selects fornecidos.
 * @param {string} selectId - ID do elemento select para fornecedores.
 */
function carregarOpcoesFornecedores(selectId) {
    const select = document.getElementById(selectId);
    if (!select) return;

    axios.get('/fornecedores', { params: { ativo: true } }) // Busca apenas fornecedores ativos
        .then(response => {
            select.innerHTML = '<option value="">Todos os Fornecedores</option>'; // Opção padrão
            // A API /fornecedores pode retornar um objeto com a chave 'fornecedores' ou a lista diretamente
            const fornecedores = response.data.fornecedores || response.data; 
            fornecedores.forEach(forn => {
                select.innerHTML += `<option value="${forn.id}">${forn.nome}</option>`; // Usar 'nome' conforme API
            });
        })
        .catch(error => {
            console.error(`Erro ao carregar fornecedores para ${selectId}:`, error);
            select.innerHTML = '<option value="">Erro ao carregar</option>';
            showNotification('Erro ao carregar fornecedores.', 'danger');
        });
}


/**
 * Carrega a lista de produtos do servidor com base nos filtros e página atuais.
 */
function carregarProdutos() {
    toggleLoading(true); // Mostrar spinner (de app.js)

    const params = {
        page: currentPage,
        per_page: 15, // Ou outro valor desejado
        categoria_id: currentFilters.categoria_id || null,
        fornecedor_id: currentFilters.fornecedor_id || null,
        estoque_baixo: currentFilters.estoque_baixo,
        termo: currentFilters.termo || null // Usar 'termo' para busca
    };

    // Limpar parâmetros nulos ou vazios para não enviar na URL
    Object.keys(params).forEach(key => (params[key] === null || params[key] === '') && delete params[key]);

    // Decide qual endpoint usar: busca ou listagem geral/filtrada
    const url = currentFilters.termo ? '/produtos/busca' : '/produtos';

    axios.get(url, { params })
        .then(response => {
            const data = response.data;
            renderizarTabela(data.produtos || []);
            totalPages = data.pages || 1;
            currentPage = data.page || 1;
            renderizarPaginacao();
            document.getElementById('total-produtos').textContent = `Total: ${data.total || 0} produtos`;
        })
        .catch(error => {
            console.error('Erro ao carregar produtos:', error);
            showNotification('Erro ao carregar produtos.', 'danger');
            document.getElementById('produtos-tabela').innerHTML = `<tr><td colspan="9" class="text-center text-danger">Erro ao carregar produtos. Tente novamente.</td></tr>`;
        })
        .finally(() => {
            toggleLoading(false); // Esconder spinner
        });
}

/**
 * Renderiza a tabela de produtos.
 * @param {Array} produtos - Lista de produtos a serem exibidos.
 */
function renderizarTabela(produtos) {
    const tabela = document.getElementById('produtos-tabela');
    if (!tabela) return;

    tabela.innerHTML = ''; // Limpar tabela

    if (produtos.length === 0) {
        tabela.innerHTML = `<tr><td colspan="9" class="text-center">Nenhum produto encontrado.</td></tr>`;
        return;
    }

    produtos.forEach(produto => {
        const precoCompra = produto.preco_compra ? `R$ ${produto.preco_compra.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '-';
        const precoVenda = produto.preco ? `R$ ${produto.preco.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '-';
        const estoqueClasse = produto.estoque <= produto.estoque_minimo ? 'text-danger fw-bold' : '';

        const row = `
            <tr>
                <td>${produto.codigo || '-'}</td>
                <td>${produto.nome}</td>
                <td>${produto.categoria?.nome || 'N/A'}</td>
                <td>${produto.fornecedor?.nome || 'N/A'}</td>
                <td>${precoCompra}</td>
                <td>${precoVenda}</td>
                <td class="${estoqueClasse}">${produto.estoque}</td>
                <td>${produto.estoque_minimo}</td>
                <td class="text-end">
                    <button class="btn btn-sm btn-primary me-1" onclick="editarProduto(${produto.id})" title="Editar">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="excluirProduto(${produto.id}, '${produto.nome}')" title="Excluir">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </td>
            </tr>
        `;
        tabela.innerHTML += row;
    });
}

/**
 * Renderiza os controles de paginação.
 */
function renderizarPaginacao() {
    const paginacaoContainer = document.getElementById('paginacao-produtos');
    if (!paginacaoContainer) return;

    paginacaoContainer.innerHTML = ''; // Limpar paginação existente

    if (totalPages <= 1) return; // Não mostrar paginação se só há uma página

    const ul = document.createElement('ul');
    ul.className = 'pagination pagination-sm mb-0';

    // Botão Anterior
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
    const prevLink = document.createElement('a');
    prevLink.className = 'page-link';
    prevLink.href = '#';
    prevLink.innerHTML = '&laquo;';
    prevLink.addEventListener('click', (e) => {
        e.preventDefault();
        if (currentPage > 1) {
            currentPage--;
            carregarProdutos();
        }
    });
    prevLi.appendChild(prevLink);
    ul.appendChild(prevLi);

    // Números das Páginas (simplificado para mostrar algumas páginas)
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
        // Link para a primeira página
        const firstLi = document.createElement('li');
        firstLi.className = 'page-item';
        const firstLink = document.createElement('a');
        firstLink.className = 'page-link';
        firstLink.href = '#';
        firstLink.textContent = '1';
        firstLink.addEventListener('click', (e) => {
            e.preventDefault();
            currentPage = 1;
            carregarProdutos();
        });
        firstLi.appendChild(firstLink);
        ul.appendChild(firstLi);
        if (startPage > 2) {
             // Reticências
            const ellipsisLi = document.createElement('li');
            ellipsisLi.className = 'page-item disabled';
            ellipsisLi.innerHTML = '<span class="page-link">...</span>';
            ul.appendChild(ellipsisLi);
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        const li = document.createElement('li');
        li.className = `page-item ${i === currentPage ? 'active' : ''}`;
        const link = document.createElement('a');
        link.className = 'page-link';
        link.href = '#';
        link.textContent = i;
        link.addEventListener('click', (e) => {
            e.preventDefault();
            currentPage = i;
            carregarProdutos();
        });
        li.appendChild(link);
        ul.appendChild(li);
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            // Reticências
            const ellipsisLi = document.createElement('li');
            ellipsisLi.className = 'page-item disabled';
            ellipsisLi.innerHTML = '<span class="page-link">...</span>';
            ul.appendChild(ellipsisLi);
        }
         // Link para a última página
        const lastLi = document.createElement('li');
        lastLi.className = 'page-item';
        const lastLink = document.createElement('a');
        lastLink.className = 'page-link';
        lastLink.href = '#';
        lastLink.textContent = totalPages;
        lastLink.addEventListener('click', (e) => {
            e.preventDefault();
            currentPage = totalPages;
            carregarProdutos();
        });
        lastLi.appendChild(lastLink);
        ul.appendChild(lastLi);
    }


    // Botão Próximo
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
    const nextLink = document.createElement('a');
    nextLink.className = 'page-link';
    nextLink.href = '#';
    nextLink.innerHTML = '&raquo;';
    nextLink.addEventListener('click', (e) => {
        e.preventDefault();
        if (currentPage < totalPages) {
            currentPage++;
            carregarProdutos();
        }
    });
    nextLi.appendChild(nextLink);
    ul.appendChild(nextLi);

    paginacaoContainer.appendChild(ul);
}

/**
 * Configura os eventos dos filtros (selects e checkbox).
 */
function configurarFiltros() {
    const filtroCategoria = document.getElementById('filtro-categoria');
    const filtroFornecedor = document.getElementById('filtro-fornecedor');
    const filtroEstoqueBaixo = document.getElementById('filtro-estoque-baixo');

    if (filtroCategoria) {
        filtroCategoria.addEventListener('change', (e) => {
            currentFilters.categoria_id = e.target.value;
            currentPage = 1; // Resetar para a primeira página ao mudar filtro
            carregarProdutos();
        });
    }

    if (filtroFornecedor) {
        filtroFornecedor.addEventListener('change', (e) => {
            currentFilters.fornecedor_id = e.target.value;
            currentPage = 1;
            carregarProdutos();
        });
    }

    if (filtroEstoqueBaixo) {
        filtroEstoqueBaixo.addEventListener('change', (e) => {
            currentFilters.estoque_baixo = e.target.checked;
            currentPage = 1;
            carregarProdutos();
        });
    }
}

/**
 * Configura a funcionalidade de busca com debounce.
 */
function configurarBusca() {
    const buscaInput = document.getElementById('busca-produto');
    let debounceTimeout;

    if (buscaInput) {
        buscaInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimeout);
            debounceTimeout = setTimeout(() => {
                currentFilters.termo = e.target.value.trim();
                currentPage = 1; // Resetar página na busca
                carregarProdutos();
            }, 500); // Atraso de 500ms para buscar
        });
    }
}

/**
 * Configura os eventos e a lógica dos modais (Adicionar, Editar, Excluir).
 */
function configurarModais() {
    // --- Modal Adicionar Produto ---
    const modalAdicionar = document.getElementById('modalAdicionarProduto');
    const formAdicionar = document.getElementById('formAdicionarProduto');
    if (modalAdicionar && formAdicionar) {
        // Carregar selects quando o modal for aberto
        modalAdicionar.addEventListener('show.bs.modal', () => {
            carregarOpcoesCategorias('categoriaProduto');
            carregarOpcoesFornecedores('fornecedorProduto');
            formAdicionar.reset(); // Limpar formulário
        });

        formAdicionar.addEventListener('submit', (e) => {
            e.preventDefault();
            adicionarProduto();
        });
    }

    // --- Modal Editar Produto ---
    const modalEditar = document.getElementById('modalEditarProduto');
    const formEditar = document.getElementById('formEditarProduto');
    if (modalEditar && formEditar) {
         // Carregar selects quando o modal for aberto (serão preenchidos depois)
        modalEditar.addEventListener('show.bs.modal', () => {
            carregarOpcoesCategorias('categoriaProdutoEditar');
            carregarOpcoesFornecedores('fornecedorProdutoEditar');
        });
        
        formEditar.addEventListener('submit', (e) => {
            e.preventDefault();
            salvarAlteracoesProduto();
        });
    }

    // --- Modal Confirmar Exclusão ---
    const btnConfirmarExclusao = document.getElementById('btnConfirmarExclusao');
    if (btnConfirmarExclusao) {
        btnConfirmarExclusao.addEventListener('click', () => {
            const id = btnConfirmarExclusao.dataset.produtoId; // Pega o ID armazenado no botão
            if (id) {
                confirmarExclusaoProduto(id);
            }
        });
    }
}

/**
 * Adiciona um novo produto.
 */
function adicionarProduto() {
    toggleLoading(true);
    const form = document.getElementById('formAdicionarProduto');
    const dadosProduto = {
        codigo: document.getElementById('codigoProduto').value,
        nome: document.getElementById('nomeProduto').value,
        categoria_id: document.getElementById('categoriaProduto').value,
        fornecedor_id: document.getElementById('fornecedorProduto').value || null, // Envia null se vazio
        preco_compra: parseFloat(document.getElementById('precoCompra').value) || 0,
        preco: parseFloat(document.getElementById('precoVenda').value), // 'preco' é o preço de venda na API
        estoque: parseInt(document.getElementById('estoqueProduto').value) || 0,
        estoque_minimo: parseInt(document.getElementById('estoqueMinimo').value) || 0,
        descricao: document.getElementById('descricaoProduto').value || ''
    };

    // Validação básica
    if (!dadosProduto.nome || !dadosProduto.categoria_id || !dadosProduto.preco) {
        showNotification('Nome, Categoria e Preço de Venda são obrigatórios.', 'warning');
        toggleLoading(false);
        return;
    }

    axios.post('/produtos', dadosProduto)
        .then(response => {
            showNotification('Produto adicionado com sucesso!', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalAdicionarProduto'));
            modal.hide();
            carregarProdutos(); // Recarregar a lista
        })
        .catch(error => {
            console.error('Erro ao adicionar produto:', error);
            const msg = error.response?.data?.error || 'Erro ao adicionar produto.';
            showNotification(msg, 'danger');
        })
        .finally(() => {
            toggleLoading(false);
        });
}

/**
 * Abre o modal de edição preenchido com os dados do produto.
 * @param {number} id - ID do produto a ser editado.
 */
function editarProduto(id) {
    toggleLoading(true);
    axios.get(`/produtos/${id}`)
        .then(response => {
            const produto = response.data;

            // Preencher formulário de edição
            document.getElementById('idProdutoEditar').value = produto.id;
            document.getElementById('codigoProdutoEditar').value = produto.codigo || '';
            document.getElementById('nomeProdutoEditar').value = produto.nome || '';
            document.getElementById('categoriaProdutoEditar').value = produto.categoria?.id || '';
            document.getElementById('fornecedorProdutoEditar').value = produto.fornecedor?.id || '';
            document.getElementById('precoCompraEditar').value = produto.preco_compra || '';
            document.getElementById('precoVendaEditar').value = produto.preco || '';
            document.getElementById('estoqueProdutoEditar').value = produto.estoque || '';
            document.getElementById('estoqueMinimoEditar').value = produto.estoque_minimo || '';
            document.getElementById('descricaoProdutoEditar').value = produto.descricao || '';

            // Abrir o modal
            const modal = new bootstrap.Modal(document.getElementById('modalEditarProduto'));
            modal.show();
        })
        .catch(error => {
            console.error('Erro ao carregar dados do produto para edição:', error);
            showNotification('Erro ao carregar dados do produto.', 'danger');
        })
        .finally(() => {
            toggleLoading(false);
        });
}

/**
 * Salva as alterações feitas no produto.
 */
function salvarAlteracoesProduto() {
    toggleLoading(true);
    const id = document.getElementById('idProdutoEditar').value;
    const dadosProduto = {
        codigo: document.getElementById('codigoProdutoEditar').value, // Código pode ou não ser editável na API
        nome: document.getElementById('nomeProdutoEditar').value,
        categoria_id: document.getElementById('categoriaProdutoEditar').value,
        fornecedor_id: document.getElementById('fornecedorProdutoEditar').value || null,
        preco_compra: parseFloat(document.getElementById('precoCompraEditar').value) || null,
        preco: parseFloat(document.getElementById('precoVendaEditar').value),
        // Estoque não deve ser editado aqui, mas sim por movimentação. A API pode ignorar ou rejeitar.
        // estoque: parseInt(document.getElementById('estoqueProdutoEditar').value), 
        estoque_minimo: parseInt(document.getElementById('estoqueMinimoEditar').value) || 0,
        descricao: document.getElementById('descricaoProdutoEditar').value || ''
    };

     // Validação básica
    if (!dadosProduto.nome || !dadosProduto.categoria_id || !dadosProduto.preco) {
        showNotification('Nome, Categoria e Preço de Venda são obrigatórios.', 'warning');
        toggleLoading(false);
        return;
    }

    axios.put(`/produtos/${id}`, dadosProduto)
        .then(response => {
            showNotification('Produto atualizado com sucesso!', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalEditarProduto'));
            modal.hide();
            carregarProdutos(); // Recarregar a lista
        })
        .catch(error => {
            console.error('Erro ao atualizar produto:', error);
            const msg = error.response?.data?.error || 'Erro ao atualizar produto.';
            showNotification(msg, 'danger');
        })
        .finally(() => {
            toggleLoading(false);
        });
}

/**
 * Prepara e abre o modal de confirmação de exclusão.
 * @param {number} id - ID do produto a ser excluído.
 * @param {string} nome - Nome do produto.
 */
function excluirProduto(id, nome) {
    document.getElementById('nomeProdutoExcluir').textContent = nome;
    // Armazena o ID no botão de confirmação para uso posterior
    document.getElementById('btnConfirmarExclusao').dataset.produtoId = id; 
    
    const modal = new bootstrap.Modal(document.getElementById('modalConfirmarExclusao'));
    modal.show();
}

/**
 * Confirma e executa a exclusão do produto.
 * @param {number} id - ID do produto a ser excluído.
 */
function confirmarExclusaoProduto(id) {
    toggleLoading(true);
    axios.delete(`/produtos/${id}`)
        .then(response => {
            showNotification('Produto excluído com sucesso!', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalConfirmarExclusao'));
            modal.hide();
            carregarProdutos(); // Recarregar a lista
        })
        .catch(error => {
            console.error('Erro ao excluir produto:', error);
            const msg = error.response?.data?.error || 'Erro ao excluir produto. Verifique se há estoque ou vendas associadas.';
            showNotification(msg, 'danger');
             const modal = bootstrap.Modal.getInstance(document.getElementById('modalConfirmarExclusao'));
            modal.hide(); // Esconder modal mesmo com erro
        })
        .finally(() => {
            toggleLoading(false);
        });
}

// Funções auxiliares (toggleLoading, showNotification) devem vir de app.js
// Se não vierem, precisam ser definidas aqui ou importadas.
// Exemplo:
/*
function toggleLoading(show = true) {
    const spinner = document.getElementById('loading-spinner');
     if (spinner) {
        spinner.style.display = show ? 'flex' : 'none';
    }
}

function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    if (!notification) return;
    notification.textContent = message;
    notification.className = `alert alert-${type} notification-popup`; 
    notification.style.display = 'block';
    notification.style.opacity = 1; 

    setTimeout(() => {
        notification.style.opacity = 0;
        setTimeout(() => {
            notification.style.display = 'none';
        }, 500); // Tempo da transição CSS
    }, 3000);
}
*/
