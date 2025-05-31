/**
 * EstoquePro - Gerenciamento de Fornecedores
 * 
 * Este script gerencia a interface de fornecedores, incluindo listagem,
 * adição, edição e exclusão de fornecedores.
 */

// Configuração global do Axios
// axios.defaults.headers.post['Content-Type'] = 'application/json'; // Se não estiver em app.js

// Estado da página
let fornecedoresList = []; // Lista completa de fornecedores carregados
let currentPageFornecedores = 1;
let totalPagesFornecedores = 1;
let currentFiltersFornecedores = {
    ativo: null, // null para todos, true para ativos, false para inativos
    busca: ''
};
let currentProdutosFornecedorPage = 1; // Página atual para produtos no modal

// Inicialização quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    // Carregar lista inicial de fornecedores (página 1, ativos por padrão talvez?)
    currentFiltersFornecedores.ativo = !document.getElementById('mostrarInativos')?.checked; // Define estado inicial do filtro 'ativo'
    carregarFornecedores();

    // Configurar eventos dos botões, busca e filtros
    configurarEventos();
    configurarBusca();
    configurarFiltrosFornecedores(); // Adicionado para filtro de ativos
});

/**
 * Configura todos os eventos de botões e formulários
 */
function configurarEventos() {
    // Botão para salvar novo fornecedor
    const btnSalvarFornecedor = document.getElementById('btnSalvarFornecedor');
    if (btnSalvarFornecedor) {
        // Associa ao submit do form em vez do click no botão para pegar validação HTML5
        const formAdicionar = document.getElementById('formAdicionarFornecedor');
        formAdicionar.addEventListener('submit', (e) => {
            e.preventDefault();
            adicionarFornecedor();
        });
    }

    // Botão para atualizar fornecedor existente
    const btnAtualizarFornecedor = document.getElementById('btnAtualizarFornecedor');
    if (btnAtualizarFornecedor) {
         // Associa ao submit do form
        const formEditar = document.getElementById('formEditarFornecedor');
        formEditar.addEventListener('submit', (e) => {
            e.preventDefault();
            atualizarFornecedor();
        });
    }

    // Botão para confirmar exclusão
    const btnConfirmarExclusao = document.getElementById('btnConfirmarExclusao');
    if (btnConfirmarExclusao) {
        btnConfirmarExclusao.addEventListener('click', confirmarExclusaoFornecedor);
    }

    // Modal de produtos: limpar paginação ao fechar
    const modalProdutos = document.getElementById('modalProdutosFornecedor');
    if (modalProdutos) {
        modalProdutos.addEventListener('hidden.bs.modal', () => {
            document.getElementById('paginacao-produtos-fornecedor').innerHTML = '';
            document.getElementById('produtos-fornecedor-tabela').innerHTML = `<tr><td colspan="5" class="text-center">Carregando produtos...</td></tr>`; // Reset
        });
    }
}

/**
 * Configura a busca de fornecedores com debounce
 */
function configurarBusca() {
    const buscaInput = document.getElementById('busca-fornecedor');
    let debounceTimeout;

    if (buscaInput) {
        buscaInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimeout);
            debounceTimeout = setTimeout(() => {
                currentFiltersFornecedores.busca = e.target.value.trim();
                currentPageFornecedores = 1; // Resetar página na busca
                carregarFornecedores();
            }, 500); // Atraso de 500ms
        });
    }
}

/**
 * Configura o filtro de mostrar/ocultar inativos
 */
function configurarFiltrosFornecedores() {
    const chkMostrarInativos = document.getElementById('mostrarInativos');
    if (chkMostrarInativos) {
        chkMostrarInativos.addEventListener('change', (e) => {
            currentFiltersFornecedores.ativo = !e.target.checked; // Se checked, não filtra por ativo (mostra todos), senão, filtra por ativo=true
            currentPageFornecedores = 1; // Resetar página ao mudar filtro
            carregarFornecedores();
        });
    }
}

/**
 * Carrega a lista de fornecedores do servidor com base nos filtros e página atuais
 */
function carregarFornecedores() {
    toggleLoading(true);

    const params = {
        page: currentPageFornecedores,
        per_page: 10, // Ou outro valor desejado
        busca: currentFiltersFornecedores.busca || null,
        // Envia 'true' ou 'false' como string se não for null
        ativo: currentFiltersFornecedores.ativo === null ? null : String(currentFiltersFornecedores.ativo)
        // Adicionar ordenação se necessário: ordenar: 'nome', direcao: 'asc'
    };

    // Limpar parâmetros nulos ou vazios
    Object.keys(params).forEach(key => (params[key] === null || params[key] === '') && delete params[key]);

    axios.get(API_ROUTES.FORNECEDORES_LISTAR, { params }) // Correção aqui
        .then(response => {
            const data = response.data;
            fornecedoresList = data.fornecedores || []; // Armazena a lista da página atual
            totalPagesFornecedores = data.pages || 1;
            currentPageFornecedores = data.page || 1;
            renderizarTabelaFornecedores(fornecedoresList); // Renderiza apenas a lista recebida
            renderizarPaginacaoFornecedores(); // Renderiza controles de paginação
            // Atualizar contagem total (opcional, se o backend retornar 'total')
            // document.getElementById('total-fornecedores').textContent = `Total: ${data.total || 0} fornecedores`;
        })
        .catch(error => {
            console.error('Erro ao carregar fornecedores:', error);
            showNotification('Erro ao carregar fornecedores', 'danger');
            document.getElementById('fornecedores-tabela').innerHTML = `<tr><td colspan="7" class="text-center text-danger">Erro ao carregar. Tente novamente.</td></tr>`;
        })
        .finally(() => {
            toggleLoading(false);
        });
}

/**
 * Renderiza a tabela de fornecedores com os dados fornecidos
 * @param {Array} listaFornecedores - Lista de fornecedores a serem exibidos
 */
function renderizarTabelaFornecedores(listaFornecedores) {
    const tabela = document.getElementById('fornecedores-tabela');
    if (!tabela) return;

    tabela.innerHTML = ''; // Limpar tabela

    if (listaFornecedores.length === 0) {
        tabela.innerHTML = `<tr><td colspan="7" class="text-center">Nenhum fornecedor encontrado.</td></tr>`;
        return;
    }

    listaFornecedores.forEach(fornecedor => {
        const statusClass = fornecedor.ativo ? 'success' : 'danger';
        const statusText = fornecedor.ativo ? 'Ativo' : 'Inativo';
        const toggleStatusIcon = fornecedor.ativo ? 'fa-toggle-on text-success' : 'fa-toggle-off text-secondary';
        const toggleStatusTitle = fornecedor.ativo ? 'Desativar' : 'Ativar';

        tabela.innerHTML += `
            <tr>
                <td>${fornecedor.nome}</td>
                <td>${fornecedor.cnpj || '-'}</td>
                <td>${fornecedor.contato || '-'}</td>
                <td>${fornecedor.telefone || '-'}</td>
                <td>${fornecedor.email || '-'}</td>
                <td><span class="badge bg-${statusClass}">${statusText}</span></td>
                <td class="text-end">
                    <button class="btn btn-sm btn-secondary me-1" onclick="alternarStatusFornecedor(${fornecedor.id})" title="${toggleStatusTitle}">
                        <i class="fas ${toggleStatusIcon}"></i>
                    </button>
                    <button class="btn btn-sm btn-info me-1" onclick="verProdutosFornecedor(${fornecedor.id}, '${fornecedor.nome}')" title="Ver Produtos (${fornecedor.total_produtos || 0})">
                        <i class="fas fa-boxes"></i>
                    </button>
                    <button class="btn btn-sm btn-primary me-1" onclick="editarFornecedor(${fornecedor.id})" title="Editar">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="excluirFornecedor(${fornecedor.id}, '${fornecedor.nome}')" title="Excluir" ${fornecedor.total_produtos > 0 ? 'disabled' : ''}>
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </td>
            </tr>
        `;
    });
}

/**
 * Renderiza os controles de paginação para a lista de fornecedores.
 */
function renderizarPaginacaoFornecedores() {
    // Implementação similar a renderizarPaginacao() de produtos.js,
    // mas usando currentPageFornecedores, totalPagesFornecedores e chamando carregarFornecedores() nos clicks.
    // Adapte a função renderizarPaginacao de produtos.js ou crie uma nova aqui.
    // Exemplo simplificado:
    const paginacaoContainer = document.getElementById('paginacao-fornecedores'); // Certifique-se que este ID existe no HTML
     if (!paginacaoContainer) return;
     paginacaoContainer.innerHTML = '';
     if (totalPagesFornecedores <= 1) return;

     // Lógica para criar botões Prev, Next e números de página...
     // Ao clicar, atualize currentPageFornecedores e chame carregarFornecedores();
     // (O código completo é longo, pode ser copiado e adaptado de produtos.js)
     // Exemplo rápido (não completo):
     let html = '<ul class="pagination pagination-sm mb-0">';
     // Prev
     html += `<li class="page-item ${currentPageFornecedores === 1 ? 'disabled' : ''}"><a class="page-link" href="#" onclick="mudarPaginaFornecedor(${currentPageFornecedores - 1})">&laquo;</a></li>`;
     // Números (simplificado)
     for (let i = 1; i <= totalPagesFornecedores; i++) {
         html += `<li class="page-item ${i === currentPageFornecedores ? 'active' : ''}"><a class="page-link" href="#" onclick="mudarPaginaFornecedor(${i})">${i}</a></li>`;
     }
     // Next
     html += `<li class="page-item ${currentPageFornecedores === totalPagesFornecedores ? 'disabled' : ''}"><a class="page-link" href="#" onclick="mudarPaginaFornecedor(${currentPageFornecedores + 1})">&raquo;</a></li>`;
     html += '</ul>';
     paginacaoContainer.innerHTML = html;
}

function mudarPaginaFornecedor(page) {
    if (page >= 1 && page <= totalPagesFornecedores) {
        currentPageFornecedores = page;
        carregarFornecedores();
    }
}

/**
 * Adiciona um novo fornecedor
 */
function adicionarFornecedor() {
    // Obter dados do formulário
    const nome = document.getElementById('nomeFornecedor').value.trim();
    const cnpj = document.getElementById('cnpjFornecedor').value.trim();
    const telefone = document.getElementById('telefoneFornecedor').value.trim();
    const email = document.getElementById('emailFornecedor').value.trim();
    const endereco = document.getElementById('enderecoFornecedor').value.trim();
    const contato = document.getElementById('contatoFornecedor').value.trim();
    const observacoes = document.getElementById('observacoesFornecedor').value.trim();

    // Validação já feita pelo required do HTML, mas pode adicionar mais aqui se necessário
    // if (!nome) { ... }

    toggleLoading(true);

    axios.post(API_ROUTES.FORNECEDORES_LISTAR, { // Correção aqui
        nome,
        cnpj: cnpj || null,
        telefone: telefone || null,
        email: email || null,
        endereco: endereco || null,
        contato: contato || null,
        observacoes: observacoes || null,
        ativo: true // Por padrão, adiciona como ativo
    })
    .then(response => {
        showNotification('Fornecedor adicionado com sucesso!', 'success');

        // Limpar formulário e fechar modal
        document.getElementById('formAdicionarFornecedor').reset();
        const modal = bootstrap.Modal.getInstance(document.getElementById('modalAdicionarFornecedor'));
        modal.hide();

        // Recarregar lista de fornecedores (indo para a primeira página talvez?)
        currentPageFornecedores = 1;
        carregarFornecedores();
    })
    .catch(error => {
        console.error('Erro ao adicionar fornecedor:', error);
        const mensagem = error.response?.data?.error || 'Erro ao adicionar fornecedor';
        showNotification(mensagem, 'danger');
    })
    .finally(() => {
        toggleLoading(false);
    });
}

/**
 * Abre o modal de edição com os dados do fornecedor
 * @param {number} id - ID do fornecedor
 */
function editarFornecedor(id) {
    toggleLoading(true);

    axios.get(API_ROUTES.FORNECEDOR_DETALHES(id))
        .then(response => {
            const fornecedor = response.data;

            // Preencher formulário com dados do fornecedor
            document.getElementById('editFornecedorId').value = fornecedor.id;
            document.getElementById('editNomeFornecedor').value = fornecedor.nome || '';
            document.getElementById('editCnpjFornecedor').value = fornecedor.cnpj || '';
            document.getElementById('editTelefoneFornecedor').value = fornecedor.telefone || '';
            document.getElementById('editEmailFornecedor').value = fornecedor.email || '';
            document.getElementById('editEnderecoFornecedor').value = fornecedor.endereco || '';
            document.getElementById('editContatoFornecedor').value = fornecedor.contato || '';
            document.getElementById('editObservacoesFornecedor').value = fornecedor.observacoes || '';
            document.getElementById('editAtivoFornecedor').checked = fornecedor.ativo;

            // Mostrar modal
            const modal = new bootstrap.Modal(document.getElementById('modalEditarFornecedor'));
            modal.show();
        })
        .catch(error => {
            console.error('Erro ao carregar detalhes do fornecedor:', error);
            showNotification('Erro ao carregar detalhes do fornecedor', 'danger');
        })
        .finally(() => {
            toggleLoading(false);
        });
}

/**
 * Atualiza os dados de um fornecedor existente
 */
function atualizarFornecedor() {
    // Obter dados do formulário
    const id = document.getElementById('editFornecedorId').value;
    const nome = document.getElementById('editNomeFornecedor').value.trim();
    const cnpj = document.getElementById('editCnpjFornecedor').value.trim();
    const telefone = document.getElementById('editTelefoneFornecedor').value.trim();
    const email = document.getElementById('editEmailFornecedor').value.trim();
    const endereco = document.getElementById('editEnderecoFornecedor').value.trim();
    const contato = document.getElementById('editContatoFornecedor').value.trim();
    const observacoes = document.getElementById('editObservacoesFornecedor').value.trim();
    const ativo = document.getElementById('editAtivoFornecedor').checked;

    // Validação
    if (!nome) {
        showNotification('O nome do fornecedor é obrigatório', 'warning');
        return;
    }

    toggleLoading(true);

    axios.put(API_ROUTES.FORNECEDOR_DETALHES(id), {
        nome,
        cnpj: cnpj || null,
        telefone: telefone || null,
        email: email || null,
        endereco: endereco || null,
        contato: contato || null,
        observacoes: observacoes || null,
        ativo
    })
    .then(response => {
        showNotification('Fornecedor atualizado com sucesso!', 'success');

        // Fechar modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('modalEditarFornecedor'));
        modal.hide();

        // Recarregar lista de fornecedores na página atual
        carregarFornecedores();
    })
    .catch(error => {
        console.error('Erro ao atualizar fornecedor:', error);
        const mensagem = error.response?.data?.error || 'Erro ao atualizar fornecedor';
        showNotification(mensagem, 'danger');
    })
    .finally(() => {
        toggleLoading(false);
    });
}

/**
 * Prepara o modal de confirmação de exclusão
 * @param {number} id - ID do fornecedor
 * @param {string} nome - Nome do fornecedor
 */
function excluirFornecedor(id, nome) {
    // Não usa mais o input hidden, pega o ID do data attribute do botão confirmar
    document.getElementById('excluirFornecedorNome').textContent = nome;
    document.getElementById('btnConfirmarExclusao').dataset.fornecedorId = id; // Armazena no botão

    const modal = new bootstrap.Modal(document.getElementById('modalConfirmarExclusao'));
    modal.show();
}

/**
 * Confirma a exclusão do fornecedor
 */
function confirmarExclusaoFornecedor() {
    const id = document.getElementById('btnConfirmarExclusao').dataset.fornecedorId; // Pega do botão
    if (!id) return;

    toggleLoading(true);

    axios.delete(API_ROUTES.FORNECEDOR_DETALHES(id))
        .then(response => {
            showNotification('Fornecedor excluído com sucesso!', 'success');

            // Fechar modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalConfirmarExclusao'));
            modal.hide();

            // Recarregar lista (pode voltar para a página 1 ou ficar na atual)
            // Se ficar na atual e ela ficar vazia, precisa tratar
            carregarFornecedores();
        })
        .catch(error => {
            console.error('Erro ao excluir fornecedor:', error);
            const mensagem = error.response?.data?.error || 'Erro ao excluir fornecedor';
            showNotification(mensagem, 'danger');

            // Fechar modal de confirmação mesmo com erro
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalConfirmarExclusao'));
            modal.hide();
        })
        .finally(() => {
            toggleLoading(false);
            delete document.getElementById('btnConfirmarExclusao').dataset.fornecedorId; // Limpa o ID
        });
}

/**
 * Alterna o status de ativo/inativo do fornecedor
 * @param {number} id - ID do fornecedor
 */
function alternarStatusFornecedor(id) {
    toggleLoading(true);

    axios.post(API_ROUTES.FORNECEDOR_ALTERNAR_STATUS(id))
        .then(response => {
            showNotification(`Fornecedor ${response.data.ativo ? 'ativado' : 'desativado'} com sucesso!`, 'success');
            // Recarrega a lista na página atual para refletir a mudança
            carregarFornecedores();
        })
        .catch(error => {
            console.error('Erro ao alterar status do fornecedor:', error);
            showNotification('Erro ao alterar status do fornecedor', 'danger');
        })
        .finally(() => {
            toggleLoading(false);
        });
}

/**
 * Busca e exibe os produtos de um fornecedor específico no modal.
 * @param {number} id - ID do fornecedor.
 * @param {string} nome - Nome do fornecedor.
 * @param {number} page - Página de produtos a ser carregada.
 */
function verProdutosFornecedor(id, nome, page = 1) {
    const modalNome = document.getElementById('fornecedorProdutosNome');
    const tabelaProdutos = document.getElementById('produtos-fornecedor-tabela');
    const paginacaoContainer = document.getElementById('paginacao-produtos-fornecedor');

    if (modalNome) modalNome.textContent = nome;
    if (tabelaProdutos) tabelaProdutos.innerHTML = `<tr><td colspan="5" class="text-center">Carregando produtos...</td></tr>`; // Colspan 5
    if (paginacaoContainer) paginacaoContainer.innerHTML = ''; // Limpa paginação anterior

    currentProdutosFornecedorPage = page; // Atualiza a página atual do modal

    toggleLoading(true); // Pode ser redundante se o modal já tiver spinner

    axios.get(API_ROUTES.FORNECEDOR_PRODUTOS(id), {
        params: {
            page: currentProdutosFornecedorPage,
            per_page: 5 // Define quantos produtos mostrar por página no modal
        }
    })
    .then(response => {
        const data = response.data;
        const produtos = data.produtos || [];
        const totalPagesProdutos = data.pages || 1;

        if (tabelaProdutos) {
            tabelaProdutos.innerHTML = ''; // Limpa o 'Carregando...'
            if (produtos.length === 0) {
                tabelaProdutos.innerHTML = `<tr><td colspan="5" class="text-center">Nenhum produto encontrado para este fornecedor.</td></tr>`;
            } else {
                produtos.forEach(produto => {
                    const precoCompra = produto.preco_compra ? `R$ ${produto.preco_compra.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '-';
                    const precoVenda = produto.preco ? `R$ ${produto.preco.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '-';
                    tabelaProdutos.innerHTML += `
                        <tr>
                            <td>${produto.nome || '-'} (${produto.codigo || 'S/C'})</td>
                            <td>${produto.categoria || 'N/A'}</td>
                            <td>${precoCompra}</td>
                            <td>${precoVenda}</td>
                            <td>${produto.estoque}</td>
                        </tr>
                    `;
                });
            }
        }

        // Renderiza a paginação para os produtos dentro do modal
        if (paginacaoContainer && totalPagesProdutos > 1) {
             let paginationHtml = '';
             // Prev
             paginationHtml += `<li class="page-item ${currentProdutosFornecedorPage === 1 ? 'disabled' : ''}"><a class="page-link" href="#" onclick="verProdutosFornecedor(${id}, '${nome}', ${currentProdutosFornecedorPage - 1})">&laquo;</a></li>`;
             // Numbers (simple example)
             for (let i = 1; i <= totalPagesProdutos; i++) {
                 paginationHtml += `<li class="page-item ${i === currentProdutosFornecedorPage ? 'active' : ''}"><a class="page-link" href="#" onclick="verProdutosFornecedor(${id}, '${nome}', ${i})">${i}</a></li>`;
             }
             // Next
             paginationHtml += `<li class="page-item ${currentProdutosFornecedorPage === totalPagesProdutos ? 'disabled' : ''}"><a class="page-link" href="#" onclick="verProdutosFornecedor(${id}, '${nome}', ${currentProdutosFornecedorPage + 1})">&raquo;</a></li>`;
             paginacaoContainer.innerHTML = paginationHtml;
        }


        // Abre o modal (se não for chamado pela paginação interna)
        if (page === 1) { // Só abre na primeira chamada
             const modal = new bootstrap.Modal(document.getElementById('modalProdutosFornecedor'));
             modal.show();
        }
    })
    .catch(error => {
        console.error(`Erro ao buscar produtos do fornecedor ${id}:`, error);
        showNotification('Erro ao carregar produtos do fornecedor.', 'danger');
        if (tabelaProdutos) tabelaProdutos.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Erro ao carregar produtos.</td></tr>`;
    })
    .finally(() => {
        toggleLoading(false);
    });
}


// Funções auxiliares (toggleLoading, showNotification) devem vir de app.js
// Se não vierem, precisam ser definidas aqui ou importadas.
