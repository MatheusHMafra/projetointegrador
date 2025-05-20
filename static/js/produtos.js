/**
 * GEP - Gerenciamento de Produtos
 * Script para a página de listagem e gerenciamento de produtos (produtos.html).
 */

// Estado da página
let currentPageProdutos = 1; // Renomeado para evitar conflito se outros scripts usarem currentPage
let totalPagesProdutos = 1;
let currentFiltersProdutos = {
    categoria_id: '',
    fornecedor_id: '',
    estoque_baixo: false,
    termo: ''
};

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    // As funções showNotification e toggleLoading são esperadas de app.js

    // Carregar dados iniciais
    carregarOpcoesCategoriasParaFiltro('filtro-categoria'); // Nome da função mais específico
    carregarOpcoesFornecedoresParaFiltro('filtro-fornecedor'); // Nome da função mais específico
    carregarProdutos(); // Carrega a primeira página sem filtros

    // Configurar eventos
    configurarFiltrosProdutos(); // Renomeado
    configurarBuscaProdutos();   // Renomeado
    configurarModaisProdutos();  // Renomeado

    // Esconder spinner inicial (geralmente em app.js ou após o primeiro carregamento de dados)
    // toggleLoading(false); // Será chamado no finally de carregarProdutos
});

/**
 * Carrega as opções de categoria nos selects de filtro.
 * @param {string} selectId - ID do elemento select para categorias.
 */
function carregarOpcoesCategoriasParaFiltro(selectId) {
    const select = document.getElementById(selectId);
    if (!select) {
        console.warn(`Elemento select '${selectId}' para filtro de categorias não encontrado.`);
        return;
    }

    if (typeof API_ROUTES === 'undefined' || !API_ROUTES.CATEGORIAS_LISTAR) {
        console.error('Erro de Configuração: API_ROUTES.CATEGORIAS_LISTAR não definido em api-routes.js.');
        select.innerHTML = '<option value="">Erro Config API</option>';
        showNotification('Erro ao carregar opções de categorias (Config API).', 'danger');
        return;
    }

    axios.get(API_ROUTES.CATEGORIAS_LISTAR) // Rota: /produtos/categorias
        .then(response => {
            select.innerHTML = '<option value="">Todas as Categorias</option>';
            (response.data || []).forEach(cat => { // response.data deve ser a lista de categorias
                select.innerHTML += `<option value="${cat.id}">${cat.nome}</option>`;
            });
        })
        .catch(error => {
            console.error(`Erro ao carregar categorias para ${selectId}:`, error.response ? error.response.data : error.message);
            select.innerHTML = '<option value="">Erro ao carregar</option>';
            showNotification('Falha ao carregar categorias.', 'danger');
        });
}

/**
 * Carrega as opções de fornecedores nos selects de filtro.
 * @param {string} selectId - ID do elemento select para fornecedores.
 */
function carregarOpcoesFornecedoresParaFiltro(selectId) {
    const select = document.getElementById(selectId);
    if (!select) {
        console.warn(`Elemento select '${selectId}' para filtro de fornecedores não encontrado.`);
        return;
    }

    if (typeof API_ROUTES === 'undefined' || !API_ROUTES.FORNECEDORES_LISTAR) {
        console.error('Erro de Configuração: API_ROUTES.FORNECEDORES_LISTAR não definido em api-routes.js.');
        select.innerHTML = '<option value="">Erro Config API</option>';
        showNotification('Erro ao carregar opções de fornecedores (Config API).', 'danger');
        return;
    }
    // Busca apenas fornecedores ativos para os filtros
    axios.get(API_ROUTES.FORNECEDORES_LISTAR, { params: { ativo: 'true', per_page: 200 } }) // per_page alto para pegar todos ativos
        .then(response => {
            select.innerHTML = '<option value="">Todos os Fornecedores</option>';
            const fornecedores = response.data.fornecedores || []; // API /fornecedores retorna { fornecedores: [...] }
            fornecedores.forEach(forn => {
                select.innerHTML += `<option value="${forn.id}">${forn.nome}</option>`;
            });
        })
        .catch(error => {
            console.error(`Erro ao carregar fornecedores para ${selectId}:`, error.response ? error.response.data : error.message);
            select.innerHTML = '<option value="">Erro ao carregar</option>';
            showNotification('Falha ao carregar fornecedores.', 'danger');
        });
}


/**
 * Carrega a lista de produtos do servidor com base nos filtros e página atuais.
 */
function carregarProdutos() {
    if (typeof API_ROUTES === 'undefined' || (!API_ROUTES.PRODUTOS_LISTAR && !API_ROUTES.PRODUTOS_BUSCA)) {
        console.error('Erro de Configuração: Rotas de produtos (PRODUTOS_LISTAR/PRODUTOS_BUSCA) não definidas em api-routes.js.');
        showNotification('Erro ao carregar produtos (Config API).', 'danger');
        document.getElementById('produtos-tabela').innerHTML = `<tr><td colspan="9" class="text-center text-danger">Erro de Configuração API.</td></tr>`;
        toggleLoading(false);
        return;
    }
    toggleLoading(true);

    const params = {
        page: currentPageProdutos,
        per_page: 15, // Itens por página
        categoria_id: currentFiltersProdutos.categoria_id || null,
        fornecedor_id: currentFiltersProdutos.fornecedor_id || null,
        estoque_baixo: currentFiltersProdutos.estoque_baixo,
        // 'termo' é usado para a rota de busca, 'q' ou 'nome' podem ser usados pela API de listagem geral
        // A função buscar_produtos no backend espera 'termo'.
        termo: currentFiltersProdutos.termo || null
    };

    // Limpar parâmetros nulos ou vazios para não enviar na URL, exceto booleanos
    Object.keys(params).forEach(key => {
        if (params[key] === null || params[key] === '') {
            delete params[key];
        }
    });
    
    // Decide qual endpoint usar: busca específica ou listagem geral/filtrada
    // A rota /produtos (PRODUTOS_LISTAR) no backend já aceita 'termo' através da função buscar_produtos.
    // Portanto, podemos usar sempre PRODUTOS_LISTAR e a lógica de busca está no backend.
    const url = API_ROUTES.PRODUTOS_LISTAR; // Rota: /produtos (que pode usar buscar_produtos internamente)

    axios.get(url, { params })
        .then(response => {
            const data = response.data; // Espera-se { produtos: [], total: X, pages: Y, page: Z, per_page: W }
            renderizarTabelaProdutos(data.produtos || []);
            totalPagesProdutos = data.pages || 1;
            currentPageProdutos = data.page || 1;
            renderizarPaginacaoProdutos();
            document.getElementById('total-produtos').textContent = `Total: ${data.total || 0} produtos`;
        })
        .catch(error => {
            console.error('Erro ao carregar produtos:', error.response ? error.response.data : error.message);
            showNotification('Falha ao carregar lista de produtos.', 'danger');
            document.getElementById('produtos-tabela').innerHTML = `<tr><td colspan="9" class="text-center text-danger">Erro ao carregar produtos. Tente novamente.</td></tr>`;
        })
        .finally(() => {
            toggleLoading(false);
        });
}

/**
 * Renderiza a tabela de produtos.
 * @param {Array} produtos - Lista de produtos a serem exibidos.
 */
function renderizarTabelaProdutos(produtos) {
    const tabelaBody = document.getElementById('produtos-tabela');
    if (!tabelaBody) return;

    tabelaBody.innerHTML = ''; // Limpar tabela

    if (produtos.length === 0) {
        tabelaBody.innerHTML = `<tr><td colspan="9" class="text-center">Nenhum produto encontrado com os filtros atuais.</td></tr>`;
        return;
    }

    produtos.forEach(produto => {
        const precoCompraFmt = produto.preco_compra ? `R$ ${parseFloat(produto.preco_compra).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '-';
        const precoVendaFmt = produto.preco ? `R$ ${parseFloat(produto.preco).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '-';
        const estoqueClasse = produto.estoque <= produto.estoque_minimo ? 'text-danger fw-bold' : '';

        const row = `
            <tr>
                <td>${produto.codigo || '-'}</td>
                <td>${produto.nome}</td>
                <td>${produto.categoria_nome || produto.categoria?.nome || 'N/A'}</td>
                <td>${produto.fornecedor_nome || produto.fornecedor?.nome || 'N/A'}</td>
                <td>${precoCompraFmt}</td>
                <td>${precoVendaFmt}</td>
                <td class="${estoqueClasse}">${produto.estoque}</td>
                <td>${produto.estoque_minimo}</td>
                <td class="text-end">
                    <button class="btn btn-sm btn-primary me-1" onclick="abrirModalEditarProduto(${produto.id})" title="Editar">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="confirmarExclusaoProdutoModal(${produto.id}, '${produto.nome.replace(/'/g, "\\'")}')" title="Excluir">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </td>
            </tr>
        `;
        tabelaBody.innerHTML += row;
    });
}

/**
 * Renderiza os controles de paginação para a lista de produtos.
 */
function renderizarPaginacaoProdutos() {
    const paginacaoContainer = document.getElementById('paginacao-produtos');
    if (!paginacaoContainer) return;

    paginacaoContainer.innerHTML = '';
    if (totalPagesProdutos <= 1) return;

    const ul = document.createElement('ul');
    ul.className = 'pagination pagination-sm mb-0';

    // Botão Anterior
    ul.appendChild(criarItemPaginacao('&laquo;', currentPageProdutos > 1 ? currentPageProdutos - 1 : null, currentPageProdutos === 1));

    // Números das Páginas (lógica simplificada para mostrar algumas páginas ao redor da atual)
    let inicio = Math.max(1, currentPageProdutos - 2);
    let fim = Math.min(totalPagesProdutos, currentPageProdutos + 2);

    if (totalPagesProdutos > 5 && currentPageProdutos > 3) { // Adiciona "1 ..." se necessário
        ul.appendChild(criarItemPaginacao('1', 1));
        if (currentPageProdutos > 4) {
             ul.appendChild(criarItemPaginacao('...', null, true)); // '...' desabilitado
        }
    }
    
    for (let i = inicio; i <= fim; i++) {
        ul.appendChild(criarItemPaginacao(i, i, false, i === currentPageProdutos));
    }

    if (totalPagesProdutos > 5 && currentPageProdutos < totalPagesProdutos - 2) { // Adiciona "... UltimaPagina" se necessário
        if (currentPageProdutos < totalPagesProdutos - 3) {
            ul.appendChild(criarItemPaginacao('...', null, true));
        }
        ul.appendChild(criarItemPaginacao(totalPagesProdutos, totalPagesProdutos));
    }
    
    // Botão Próximo
    ul.appendChild(criarItemPaginacao('&raquo;', currentPageProdutos < totalPagesProdutos ? currentPageProdutos + 1 : null, currentPageProdutos === totalPagesProdutos));

    paginacaoContainer.appendChild(ul);
}

/**
 * Cria um item de paginação (li > a).
 */
function criarItemPaginacao(texto, paginaAlvo, desabilitado = false, ativo = false) {
    const li = document.createElement('li');
    li.className = `page-item ${desabilitado ? 'disabled' : ''} ${ativo ? 'active' : ''}`;
    const a = document.createElement('a');
    a.className = 'page-link';
    a.href = '#';
    a.innerHTML = texto;
    if (!desabilitado && paginaAlvo !== null) {
        a.addEventListener('click', (e) => {
            e.preventDefault();
            currentPageProdutos = paginaAlvo;
            carregarProdutos();
        });
    }
    li.appendChild(a);
    return li;
}


/**
 * Configura os eventos dos filtros (selects e checkbox) da página de produtos.
 */
function configurarFiltrosProdutos() {
    const filtroCategoriaEl = document.getElementById('filtro-categoria');
    const filtroFornecedorEl = document.getElementById('filtro-fornecedor');
    const filtroEstoqueBaixoEl = document.getElementById('filtro-estoque-baixo');

    if (filtroCategoriaEl) {
        filtroCategoriaEl.addEventListener('change', (e) => {
            currentFiltersProdutos.categoria_id = e.target.value;
            currentPageProdutos = 1;
            carregarProdutos();
        });
    }
    if (filtroFornecedorEl) {
        filtroFornecedorEl.addEventListener('change', (e) => {
            currentFiltersProdutos.fornecedor_id = e.target.value;
            currentPageProdutos = 1;
            carregarProdutos();
        });
    }
    if (filtroEstoqueBaixoEl) {
        filtroEstoqueBaixoEl.addEventListener('change', (e) => {
            currentFiltersProdutos.estoque_baixo = e.target.checked;
            currentPageProdutos = 1;
            carregarProdutos();
        });
    }
}

/**
 * Configura a funcionalidade de busca de produtos com debounce.
 */
function configurarBuscaProdutos() {
    const buscaInputEl = document.getElementById('busca-produto'); // ID da barra de busca principal
    let debounceTimeout;

    if (buscaInputEl) {
        buscaInputEl.addEventListener('input', (e) => {
            clearTimeout(debounceTimeout);
            debounceTimeout = setTimeout(() => {
                currentFiltersProdutos.termo = e.target.value.trim();
                currentPageProdutos = 1;
                carregarProdutos();
            }, 500); // Atraso de 500ms
        });
    }
}

/**
 * Configura os eventos e a lógica dos modais (Adicionar, Editar, Excluir).
 */
function configurarModaisProdutos() {
    // --- Modal Adicionar Produto ---
    const modalAdicionarEl = document.getElementById('modalAdicionarProduto');
    const formAdicionarEl = document.getElementById('formAdicionarProduto');
    if (modalAdicionarEl && formAdicionarEl) {
        modalAdicionarEl.addEventListener('show.bs.modal', () => {
            // Carregar opções para selects DENTRO do modal
            carregarOpcoesCategoriasParaModal('categoriaProduto', true); // true para modal
            carregarOpcoesFornecedoresParaModal('fornecedorProduto', true); // true para modal
            formAdicionarEl.reset();
        });

        formAdicionarEl.addEventListener('submit', (e) => {
            e.preventDefault();
            submeterFormularioAdicionarProduto();
        });
    }

    // --- Modal Editar Produto ---
    const modalEditarEl = document.getElementById('modalEditarProduto');
    const formEditarEl = document.getElementById('formEditarProduto');
    if (modalEditarEl && formEditarEl) {
        modalEditarEl.addEventListener('show.bs.modal', () => {
            // As opções serão carregadas e o valor selecionado quando abrirModalEditarProduto for chamado
            carregarOpcoesCategoriasParaModal('categoriaProdutoEditar', true);
            carregarOpcoesFornecedoresParaModal('fornecedorProdutoEditar', true);
        });
        
        formEditarEl.addEventListener('submit', (e) => {
            e.preventDefault();
            submeterFormularioEditarProduto();
        });
    }

    // --- Modal Confirmar Exclusão ---
    const btnConfirmarExclusaoEl = document.getElementById('btnConfirmarExclusao');
    if (btnConfirmarExclusaoEl) {
        btnConfirmarExclusaoEl.addEventListener('click', () => {
            const produtoId = btnConfirmarExclusaoEl.dataset.produtoId;
            if (produtoId) {
                executarExclusaoProduto(produtoId);
            }
        });
    }
}

/**
 * Carrega opções de categorias para selects dentro de modais.
 */
function carregarOpcoesCategoriasParaModal(selectId, isModalContext = false) {
    const select = document.getElementById(selectId);
    if (!select) return;

    if (typeof API_ROUTES === 'undefined' || !API_ROUTES.CATEGORIAS_LISTAR) {
        console.error('Erro Config: API_ROUTES.CATEGORIAS_LISTAR não definido (modal).');
        select.innerHTML = '<option value="">Erro API</option>';
        return;
    }
    axios.get(API_ROUTES.CATEGORIAS_LISTAR)
        .then(response => {
            select.innerHTML = '<option value="">Selecione...</option>';
            (response.data || []).forEach(cat => {
                select.innerHTML += `<option value="${cat.id}">${cat.nome}</option>`;
            });
            // Se for um modal de edição, um evento pode ser disparado para preencher o valor
            if (isModalContext && select.dataset.selectedValue) {
                select.value = select.dataset.selectedValue;
            }
        })
        .catch(error => console.error(`Erro ao carregar categorias para modal ${selectId}:`, error));
}

/**
 * Carrega opções de fornecedores para selects dentro de modais.
 */
function carregarOpcoesFornecedoresParaModal(selectId, isModalContext = false) {
    const select = document.getElementById(selectId);
    if (!select) return;

    if (typeof API_ROUTES === 'undefined' || !API_ROUTES.FORNECEDORES_LISTAR) {
        console.error('Erro Config: API_ROUTES.FORNECEDORES_LISTAR não definido (modal).');
        select.innerHTML = '<option value="">Erro API</option>';
        return;
    }
    axios.get(API_ROUTES.FORNECEDORES_LISTAR, { params: { ativo: 'true', per_page: 200 }})
        .then(response => {
            select.innerHTML = '<option value="">Selecione...</option>';
            const fornecedores = response.data.fornecedores || [];
            fornecedores.forEach(forn => {
                select.innerHTML += `<option value="${forn.id}">${forn.nome}</option>`;
            });
             if (isModalContext && select.dataset.selectedValue) {
                select.value = select.dataset.selectedValue;
            }
        })
        .catch(error => console.error(`Erro ao carregar fornecedores para modal ${selectId}:`, error));
}


/**
 * Submete o formulário de adicionar novo produto.
 */
function submeterFormularioAdicionarProduto() {
    if (typeof API_ROUTES === 'undefined' || !API_ROUTES.PRODUTOS_LISTAR) {
        showNotification('Erro de Configuração API ao adicionar produto.', 'danger');
        return;
    }
    toggleLoading(true);
    const dadosProduto = {
        codigo: document.getElementById('codigoProduto').value.trim(), // ID do input no modal
        nome: document.getElementById('nomeProduto').value.trim(),
        categoria_id: document.getElementById('categoriaProduto').value,
        fornecedor_id: document.getElementById('fornecedorProduto').value || null,
        preco_compra: parseFloat(document.getElementById('precoCompra').value) || null,
        preco: parseFloat(document.getElementById('precoVenda').value), // 'preco' é o preço de venda
        estoque: parseInt(document.getElementById('estoqueProduto').value) || 0,
        estoque_minimo: parseInt(document.getElementById('estoqueMinimo').value) || 0,
        descricao: document.getElementById('descricaoProduto').value.trim() || ''
    };

    if (!dadosProduto.nome || !dadosProduto.categoria_id || !dadosProduto.preco) {
        showNotification('Nome, Categoria e Preço de Venda são obrigatórios.', 'warning');
        toggleLoading(false);
        return;
    }
    // Adicionar validação de código único aqui ou deixar para o backend
    // if (!dadosProduto.codigo) { /* ... */ }


    axios.post(API_ROUTES.PRODUTOS_LISTAR, dadosProduto) // POST para /produtos
        .then(response => {
            showNotification(response.data.message || 'Produto adicionado com sucesso!', 'success');
            const modalEl = document.getElementById('modalAdicionarProduto');
            if (modalEl) bootstrap.Modal.getInstance(modalEl).hide();
            carregarProdutos(); // Recarregar a lista
        })
        .catch(error => {
            console.error('Erro ao adicionar produto:', error.response ? error.response.data : error.message);
            const msg = error.response?.data?.error || 'Erro desconhecido ao adicionar produto.';
            showNotification(msg, 'danger');
        })
        .finally(() => {
            toggleLoading(false);
        });
}

/**
 * Abre o modal de edição preenchido com os dados do produto.
 * @param {number} produtoId - ID do produto a ser editado.
 */
function abrirModalEditarProduto(produtoId) {
    if (typeof API_ROUTES === 'undefined' || !API_ROUTES.PRODUTO_DETALHES) {
        showNotification('Erro de Configuração API ao editar produto.', 'danger');
        return;
    }
    toggleLoading(true);
    axios.get(API_ROUTES.PRODUTO_DETALHES(produtoId)) // GET /produtos/{id}
        .then(response => {
            const produto = response.data;
            if (!produto) {
                showNotification('Produto não encontrado para edição.', 'warning');
                return;
            }

            document.getElementById('idProdutoEditar').value = produto.id;
            document.getElementById('codigoProdutoEditar').value = produto.codigo || '';
            document.getElementById('nomeProdutoEditar').value = produto.nome || '';
            
            // Para selects, armazena o valor para ser setado após o carregamento das opções
            const catSelect = document.getElementById('categoriaProdutoEditar');
            catSelect.dataset.selectedValue = produto.categoria_id || produto.categoria?.id || '';
            // Força o recarregamento das opções e seleciona o valor
            carregarOpcoesCategoriasParaModal('categoriaProdutoEditar', true);


            const fornSelect = document.getElementById('fornecedorProdutoEditar');
            fornSelect.dataset.selectedValue = produto.fornecedor_id || produto.fornecedor?.id || '';
            carregarOpcoesFornecedoresParaModal('fornecedorProdutoEditar', true);


            document.getElementById('precoCompraEditar').value = produto.preco_compra || '';
            document.getElementById('precoVendaEditar').value = produto.preco || ''; // 'preco' é o preço de venda
            document.getElementById('estoqueProdutoEditar').value = produto.estoque !== undefined ? produto.estoque : '';
            document.getElementById('estoqueMinimoEditar').value = produto.estoque_minimo !== undefined ? produto.estoque_minimo : '';
            document.getElementById('descricaoProdutoEditar').value = produto.descricao || '';

            const modalEl = document.getElementById('modalEditarProduto');
            if (modalEl) new bootstrap.Modal(modalEl).show();
        })
        .catch(error => {
            console.error('Erro ao carregar dados do produto para edição:', error.response ? error.response.data : error.message);
            showNotification('Falha ao carregar dados do produto para edição.', 'danger');
        })
        .finally(() => {
            toggleLoading(false);
        });
}

/**
 * Submete o formulário de edição do produto.
 */
function submeterFormularioEditarProduto() {
    const produtoId = document.getElementById('idProdutoEditar').value;
    if (!produtoId) {
        showNotification('ID do produto para edição não encontrado.', 'danger');
        return;
    }
    if (typeof API_ROUTES === 'undefined' || !API_ROUTES.PRODUTO_DETALHES) { // Rota para PUT é a mesma do GET/DELETE por ID
        showNotification('Erro de Configuração API ao salvar alterações.', 'danger');
        return;
    }

    toggleLoading(true);
    const dadosProdutoAtualizado = {
        codigo: document.getElementById('codigoProdutoEditar').value.trim(),
        nome: document.getElementById('nomeProdutoEditar').value.trim(),
        categoria_id: document.getElementById('categoriaProdutoEditar').value,
        fornecedor_id: document.getElementById('fornecedorProdutoEditar').value || null,
        preco_compra: parseFloat(document.getElementById('precoCompraEditar').value) || null,
        preco: parseFloat(document.getElementById('precoVendaEditar').value), // Preço de venda
        // Estoque não é editado diretamente aqui, mas por movimentação.
        // A API de PUT /produtos/{id} pode ou não aceitar 'estoque'.
        // Se aceitar, deve criar um movimento de 'ajuste'.
        // Por ora, não enviamos 'estoque' para evitar alterações diretas sem rastreio.
        estoque_minimo: parseInt(document.getElementById('estoqueMinimoEditar').value) || 0,
        descricao: document.getElementById('descricaoProdutoEditar').value.trim() || ''
    };
    
    if (!dadosProdutoAtualizado.nome || !dadosProdutoAtualizado.categoria_id || !dadosProdutoAtualizado.preco) {
        showNotification('Nome, Categoria e Preço de Venda são obrigatórios.', 'warning');
        toggleLoading(false);
        return;
    }

    axios.put(API_ROUTES.PRODUTO_DETALHES(produtoId), dadosProdutoAtualizado) // PUT /produtos/{id}
        .then(response => {
            showNotification(response.data.message || 'Produto atualizado com sucesso!', 'success');
            const modalEl = document.getElementById('modalEditarProduto');
            if (modalEl) bootstrap.Modal.getInstance(modalEl).hide();
            carregarProdutos();
        })
        .catch(error => {
            console.error('Erro ao atualizar produto:', error.response ? error.response.data : error.message);
            const msg = error.response?.data?.error || 'Erro desconhecido ao atualizar produto.';
            showNotification(msg, 'danger');
        })
        .finally(() => {
            toggleLoading(false);
        });
}

/**
 * Prepara e abre o modal de confirmação de exclusão.
 * @param {number} produtoId - ID do produto a ser excluído.
 * @param {string} nomeProduto - Nome do produto.
 */
function confirmarExclusaoProdutoModal(produtoId, nomeProduto) {
    document.getElementById('nomeProdutoExcluir').textContent = nomeProduto;
    document.getElementById('btnConfirmarExclusao').dataset.produtoId = produtoId;
    
    const modalEl = document.getElementById('modalConfirmarExclusao');
    if (modalEl) new bootstrap.Modal(modalEl).show();
}

/**
 * Confirma e executa a exclusão do produto.
 * @param {number} produtoId - ID do produto a ser excluído.
 */
function executarExclusaoProduto(produtoId) {
    if (!produtoId) return;
    if (typeof API_ROUTES === 'undefined' || !API_ROUTES.PRODUTO_DETALHES) {
        showNotification('Erro de Configuração API ao excluir produto.', 'danger');
        return;
    }
    toggleLoading(true);
    axios.delete(API_ROUTES.PRODUTO_DETALHES(produtoId)) // DELETE /produtos/{id}
        .then(response => {
            showNotification(response.data.message || 'Produto excluído com sucesso!', 'success');
            const modalEl = document.getElementById('modalConfirmarExclusao');
            if (modalEl) bootstrap.Modal.getInstance(modalEl).hide();
            carregarProdutos(); // Recarregar a lista
        })
        .catch(error => {
            console.error('Erro ao excluir produto:', error.response ? error.response.data : error.message);
            const msg = error.response?.data?.error || 'Erro ao excluir produto. Verifique se há estoque ou vendas associadas.';
            showNotification(msg, 'danger');
            // Esconder modal mesmo com erro, pois a ação foi tentada.
            const modalEl = document.getElementById('modalConfirmarExclusao');
            if (modalEl) bootstrap.Modal.getInstance(modalEl).hide();
        })
        .finally(() => {
            toggleLoading(false);
        });
}

// Funções globais showNotification e toggleLoading são esperadas de app.js
// Se não estiverem lá, descomente e use as implementações abaixo ou importe-as.
/*
function toggleLoading(show = true) {
    const spinner = document.getElementById('loading-spinner'); // Certifique-se que este ID existe
     if (spinner) {
        spinner.style.display = show ? 'flex' : 'none';
    }
}

function showNotification(message, type = 'success') { // success, danger, warning, info
    const notificationArea = document.getElementById('notification'); // Certifique-se que este ID existe
    if (!notificationArea) {
        console.warn("Elemento de notificação '#notification' não encontrado no DOM.");
        alert(`${type.toUpperCase()}: ${message}`); // Fallback para alert
        return;
    }
    notificationArea.textContent = message;
    notificationArea.className = `alert alert-${type} notification-popup`; // Reinicia classes
    notificationArea.style.display = 'block';
    notificationArea.style.opacity = 1;

    setTimeout(() => {
        notificationArea.style.opacity = 0;
        setTimeout(() => {
            notificationArea.style.display = 'none';
        }, 300); // Tempo da transição CSS para 'opacity'
    }, 3000); // Notificação visível por 3 segundos
}
*/
