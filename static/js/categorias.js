/**
 * GEP - Gerenciamento de Categorias
 * Script para a página de listagem e gerenciamento de categorias.
 */

// Estado da página
let currentSearchTermCategorias = '';

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    carregarCategorias();
    configurarBuscaCategorias();
    configurarModaisCategorias();

    // Esconder o spinner inicial (geralmente em app.js ou após o primeiro carregamento de dados)
    // toggleLoading(false); // Será chamado no finally de carregarCategorias
});

/**
 * Carrega a lista de categorias do servidor.
 */
function carregarCategorias() {
    toggleLoading(true);
    axios.get(API_ROUTES.CATEGORIAS_LISTAR) // GET /produtos/categorias
        .then(response => {
            const categorias = response.data || [];
            renderizarTabelaCategorias(categorias);
            document.getElementById('total-categorias').textContent = `Total: ${categorias.length} categorias`;
        })
        .catch(error => {
            console.error('Erro ao carregar categorias:', error.response ? error.response.data : error.message);
            showNotification('Falha ao carregar lista de categorias.', 'danger');
            document.getElementById('categorias-tabela').innerHTML = `<tr><td colspan="4" class="text-center text-danger">Erro ao carregar categorias.</td></tr>`;
        })
        .finally(() => {
            toggleLoading(false);
        });
}

/**
 * Renderiza a tabela de categorias.
 * @param {Array} categorias - Lista de categorias a serem exibidas.
 */
function renderizarTabelaCategorias(categorias) {
    const tabelaBody = document.getElementById('categorias-tabela');
    if (!tabelaBody) return;

    tabelaBody.innerHTML = ''; // Limpar tabela

    const termoBusca = currentSearchTermCategorias.toLowerCase();
    const categoriasFiltradas = termoBusca
        ? categorias.filter(cat => cat.nome.toLowerCase().includes(termoBusca) || (cat.descricao && cat.descricao.toLowerCase().includes(termoBusca)))
        : categorias;


    if (categoriasFiltradas.length === 0) {
        tabelaBody.innerHTML = `<tr><td colspan="4" class="text-center">Nenhuma categoria encontrada.</td></tr>`;
        return;
    }

    categoriasFiltradas.forEach(categoria => {
        const row = `
            <tr>
                <td>${categoria.nome}</td>
                <td>${categoria.descricao || '-'}</td>
                <td>${categoria.total_produtos !== undefined ? categoria.total_produtos : 'N/A'}</td>
                <td class="text-end">
                    <button class="btn btn-sm btn-primary me-1" onclick="abrirModalEditarCategoria(${categoria.id})" title="Editar">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="confirmarExclusaoCategoriaModal(${categoria.id}, '${categoria.nome.replace(/'/g, "\\'")}')" title="Excluir" ${categoria.total_produtos > 0 ? 'disabled' : ''}>
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </td>
            </tr>
        `;
        tabelaBody.innerHTML += row;
    });
}

/**
 * Configura a funcionalidade de busca de categorias com debounce.
 */
function configurarBuscaCategorias() {
    const buscaInputEl = document.getElementById('busca-categoria');
    let debounceTimeout;

    if (buscaInputEl) {
        buscaInputEl.addEventListener('input', (e) => {
            clearTimeout(debounceTimeout);
            debounceTimeout = setTimeout(() => {
                currentSearchTermCategorias = e.target.value.trim();
                // A filtragem agora é feita no lado do cliente ao renderizar
                carregarCategorias(); // Recarrega e aplica o filtro no renderizarTabelaCategorias
            }, 300);
        });
    }
}

/**
 * Configura os eventos e a lógica dos modais de categorias.
 */
function configurarModaisCategorias() {
    // --- Modal Adicionar Categoria ---
    const modalAdicionarEl = document.getElementById('modalAdicionarCategoria');
    const formAdicionarEl = document.getElementById('formAdicionarCategoria');
    const btnSalvarCategoriaEl = document.getElementById('btnSalvarCategoria');

    if (modalAdicionarEl && formAdicionarEl && btnSalvarCategoriaEl) {
        modalAdicionarEl.addEventListener('show.bs.modal', () => {
            formAdicionarEl.reset();
        });
        btnSalvarCategoriaEl.addEventListener('click', () => {
             if (formAdicionarEl.checkValidity()) {
                submeterFormularioAdicionarCategoria();
            } else {
                formAdicionarEl.reportValidity();
            }
        });
    }

    // --- Modal Editar Categoria ---
    const modalEditarEl = document.getElementById('modalEditarCategoria');
    const formEditarEl = document.getElementById('formEditarCategoria');
    const btnAtualizarCategoriaEl = document.getElementById('btnAtualizarCategoria');
    
    if (modalEditarEl && formEditarEl && btnAtualizarCategoriaEl) {
         btnAtualizarCategoriaEl.addEventListener('click', () => {
             if (formEditarEl.checkValidity()) {
                submeterFormularioEditarCategoria();
            } else {
                formEditarEl.reportValidity();
            }
        });
    }

    // --- Modal Confirmar Exclusão ---
    const btnConfirmarExclusaoEl = document.getElementById('btnConfirmarExclusaoCategoria');
    if (btnConfirmarExclusaoEl) {
        btnConfirmarExclusaoEl.addEventListener('click', () => {
            const categoriaId = btnConfirmarExclusaoEl.dataset.categoriaId;
            if (categoriaId) {
                executarExclusaoCategoria(categoriaId);
            }
        });
    }
}

/**
 * Submete o formulário de adicionar nova categoria.
 */
function submeterFormularioAdicionarCategoria() {
    toggleLoading(true);
    const dadosCategoria = {
        nome: document.getElementById('nomeCategoria').value.trim(),
        descricao: document.getElementById('descricaoCategoria').value.trim()
    };

    if (!dadosCategoria.nome) {
        showNotification('Nome da categoria é obrigatório.', 'warning');
        toggleLoading(false);
        return;
    }

    axios.post(API_ROUTES.CATEGORIAS_LISTAR, dadosCategoria) // POST /produtos/categorias
        .then(response => {
            showNotification(response.data.message || 'Categoria adicionada com sucesso!', 'success');
            const modalEl = document.getElementById('modalAdicionarCategoria');
            if (modalEl) bootstrap.Modal.getInstance(modalEl).hide();
            carregarCategorias();
        })
        .catch(error => {
            console.error('Erro ao adicionar categoria:', error.response ? error.response.data : error.message);
            const msg = error.response?.data?.error || 'Erro desconhecido ao adicionar categoria.';
            showNotification(msg, 'danger');
        })
        .finally(() => {
            toggleLoading(false);
        });
}

/**
 * Abre o modal de edição preenchido com os dados da categoria.
 * @param {number} categoriaId - ID da categoria a ser editada.
 */
function abrirModalEditarCategoria(categoriaId) {
    toggleLoading(true);
    axios.get(API_ROUTES.CATEGORIA_DETALHES(categoriaId)) // GET /produtos/categorias/{id}
        .then(response => {
            const categoria = response.data;
            if (!categoria) {
                showNotification('Categoria não encontrada para edição.', 'warning');
                return;
            }

            document.getElementById('idCategoriaEditar').value = categoria.id;
            document.getElementById('nomeCategoriaEditar').value = categoria.nome || '';
            document.getElementById('descricaoCategoriaEditar').value = categoria.descricao || '';
            
            const modalEl = document.getElementById('modalEditarCategoria');
            if (modalEl) new bootstrap.Modal(modalEl).show();
        })
        .catch(error => {
            console.error('Erro ao carregar dados da categoria para edição:', error.response ? error.response.data : error.message);
            showNotification('Falha ao carregar dados da categoria para edição.', 'danger');
        })
        .finally(() => {
            toggleLoading(false);
        });
}

/**
 * Submete o formulário de edição da categoria.
 */
function submeterFormularioEditarCategoria() {
    const categoriaId = document.getElementById('idCategoriaEditar').value;
    if (!categoriaId) {
        showNotification('ID da categoria para edição não encontrado.', 'danger');
        return;
    }
    toggleLoading(true);
    const dadosCategoriaAtualizada = {
        nome: document.getElementById('nomeCategoriaEditar').value.trim(),
        descricao: document.getElementById('descricaoCategoriaEditar').value.trim()
    };
    
    if (!dadosCategoriaAtualizada.nome) {
        showNotification('Nome da categoria é obrigatório.', 'warning');
        toggleLoading(false);
        return;
    }

    axios.put(API_ROUTES.CATEGORIA_DETALHES(categoriaId), dadosCategoriaAtualizada) // PUT /produtos/categorias/{id}
        .then(response => {
            showNotification(response.data.message || 'Categoria atualizada com sucesso!', 'success');
            const modalEl = document.getElementById('modalEditarCategoria');
            if (modalEl) bootstrap.Modal.getInstance(modalEl).hide();
            carregarCategorias();
        })
        .catch(error => {
            console.error('Erro ao atualizar categoria:', error.response ? error.response.data : error.message);
            const msg = error.response?.data?.error || 'Erro desconhecido ao atualizar categoria.';
            showNotification(msg, 'danger');
        })
        .finally(() => {
            toggleLoading(false);
        });
}

/**
 * Prepara e abre o modal de confirmação de exclusão para categorias.
 * @param {number} categoriaId - ID da categoria a ser excluída.
 * @param {string} nomeCategoria - Nome da categoria.
 */
function confirmarExclusaoCategoriaModal(categoriaId, nomeCategoria) {
    document.getElementById('nomeCategoriaExcluir').textContent = nomeCategoria;
    document.getElementById('btnConfirmarExclusaoCategoria').dataset.categoriaId = categoriaId;
    
    const modalEl = document.getElementById('modalConfirmarExclusaoCategoria');
    if (modalEl) new bootstrap.Modal(modalEl).show();
}

/**
 * Confirma e executa a exclusão da categoria.
 * @param {number} categoriaId - ID da categoria a ser excluída.
 */
function executarExclusaoCategoria(categoriaId) {
    if (!categoriaId) return;
    toggleLoading(true);
    axios.delete(API_ROUTES.CATEGORIA_DETALHES(categoriaId)) // DELETE /produtos/categorias/{id}
        .then(response => {
            showNotification(response.data.message || 'Categoria excluída com sucesso!', 'success');
            const modalEl = document.getElementById('modalConfirmarExclusaoCategoria');
            if (modalEl) bootstrap.Modal.getInstance(modalEl).hide();
            carregarCategorias();
        })
        .catch(error => {
            console.error('Erro ao excluir categoria:', error.response ? error.response.data : error.message);
            const msg = error.response?.data?.error || 'Erro ao excluir categoria. Verifique se há produtos associados.';
            showNotification(msg, 'danger');
            const modalEl = document.getElementById('modalConfirmarExclusaoCategoria');
            if (modalEl) bootstrap.Modal.getInstance(modalEl).hide();
        })
        .finally(() => {
            toggleLoading(false);
        });
}