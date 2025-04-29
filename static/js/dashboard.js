// Configuração global do Axios
axios.defaults.headers.post['Content-Type'] = 'application/json';

// Variáveis globais para os gráficos
let graficoMovimentacao;

// Configuração inicial
document.addEventListener('DOMContentLoaded', () => {
    // Configurar tema escuro/claro (mantido aqui ou em app.js se for global)
    // setupThemeManager(); // Assumindo que está em app.js ou é chamado lá

    // Carregar dados iniciais
    carregarEstatisticas();
    carregarProdutosMaisVendidos(); // Renomeado de carregarCategorias se for o caso
    carregarProdutosMenosVendidos(); // Renomeado de carregarProdutosEstoqueBaixo se for o caso
    carregarProdutosEstoqueBaixoCard(); // Função específica para o card de estoque baixo
    // carregarRelatorios(); // Se houver dados de relatórios a carregar inicialmente

    // Configurar eventos
    configurarBuscaProdutos(); // Mantido se a busca estiver no dashboard
    configurarFormularios(); // Mantido se os modais do dashboard tiverem JS específico aqui

    // Criar gráfico de movimentação
    criarGraficoMovimentacao();

    // Ocultar spinner de carregamento inicial APÓS tudo carregar
    // toggleLoading(false); // Movido para o final das chamadas async se necessário

    // Atualizar dados periodicamente
    setInterval(() => {
        carregarEstatisticas();
        carregarProdutosEstoqueBaixoCard();
        carregarProdutosMaisVendidos();
        carregarProdutosMenosVendidos();
    }, 300000); // 5 minutos

    // Esconde o spinner inicial após um pequeno delay para garantir que o DOM está pronto
    // Ou melhor, esconder dentro do 'then' ou 'finally' das chamadas async iniciais
    const initialSpinner = document.getElementById('loading-spinner-initial');
    if (initialSpinner) {
         // Idealmente, esconder isso quando os dados essenciais forem carregados
         // Exemplo simples: esconder após um tempo
         setTimeout(() => {
             initialSpinner.style.display = 'none';
         }, 500); // Ajuste o tempo conforme necessário
    }
});

/**
 * Configura o gerenciamento de tema (escuro/claro)
 */
function setupThemeManager() {
    const themeToggle = document.getElementById('theme-toggle');
    
    // Verificar se há uma preferência salva no localStorage
    const currentTheme = localStorage.getItem('theme');
    
    if (currentTheme) {
        // Se houver uma preferência salva, aplicá-la
        document.documentElement.setAttribute('data-theme', currentTheme);
        updateThemeToggleIcon(currentTheme);
    } else {
        // Caso contrário, usar dark mode como padrão
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
        updateThemeToggleIcon('dark');
    }
    
    // Configurar o evento de clique no botão de alternar tema
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            // Verifica o tema atual
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            // Alterna o tema
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            // Atualiza o ícone do botão
            updateThemeToggleIcon(newTheme);
            
            // Atualiza os gráficos para o novo tema
            atualizarTemaGraficos(newTheme);
        });
    }
}

/**
 * Atualiza o ícone do botão de alternância de tema
 * @param {string} theme - O tema atual ('dark' ou 'light')
 */
function updateThemeToggleIcon(theme) {
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        // Limpa o conteúdo atual do botão
        themeToggle.innerHTML = '';
        
        // Adiciona o ícone apropriado com base no tema
        const icon = document.createElement('i');
        icon.className = theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
        themeToggle.appendChild(icon);
    }
}

/**
 * Atualiza cores dos gráficos para combinar com o tema atual
 * @param {string} theme - O tema atual ('dark' ou 'light')
 */
function atualizarTemaGraficos(theme) {
    // Atualiza cores globais do Chart.js
    if (theme === 'dark') {
        Chart.defaults.color = '#dfe6e9';
        Chart.defaults.borderColor = '#2d3436';
    } else {
        Chart.defaults.color = '#555';
        Chart.defaults.borderColor = '#eaeaea';
    }

    // Recriar o gráfico de movimentação
    criarGraficoMovimentacao();
}

// Função para mostrar notificação
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `alert alert-${type} notification-popup`;
    notification.style.display = 'block';
    
    // Ocultar a notificação após 3 segundos
    setTimeout(() => {
        notification.style.display = 'none';
    }, 3000);
}

// Função para mostrar/ocultar spinner de carregamento
function toggleLoading(show = true) {
    const spinner = document.getElementById('loading-spinner');
    spinner.style.display = show ? 'flex' : 'none';
}

// Configurar busca de produtos
function configurarBuscaProdutos() {
    const buscaInput = document.getElementById('busca-produto');
    
    if (!buscaInput) return;
    
    // Debounce para evitar muitas requisições
    let timeout;
    buscaInput.addEventListener('input', (e) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            const query = e.target.value.trim();
            if (query.length > 2) {
                buscarProdutos(query);
            }
        }, 500);
    });
}

// Função para buscar produtos
function buscarProdutos(query) {
    toggleLoading(true);
    axios.get(`/produtos/busca?q=${encodeURIComponent(query)}`)
        .then(response => {
            showNotification(`${response.data.produtos.length} produto(s) encontrado(s).`);
            // Aqui você pode mostrar os resultados da busca
        })
        .catch(error => {
            console.error('Erro ao buscar produtos:', error);
            showNotification('Erro ao buscar produtos.', 'danger');
        })
        .finally(() => {
            toggleLoading(false);
        });
}

// Carregar estatísticas do dashboard
function carregarEstatisticas() {
    // VERIFICAÇÃO ADICIONADA
    if (typeof API_ROUTES === 'undefined' || !API_ROUTES.stats) {
        console.error('API_ROUTES ou API_ROUTES.stats não está definido. Verifique o carregamento de api-routes.js.');
        showNotification('Erro crítico: Configuração de API não encontrada.', 'danger');
        toggleLoading(false); // Esconde o spinner se não puder continuar
        return; // Interrompe a função
    }

    toggleLoading(true); // Mostrar spinner antes da chamada
    axios.get(API_ROUTES.stats)
        .then(response => {
            const data = response.data;
            if (data) {
                document.getElementById('total-produtos').textContent = data.total_produtos || '0';
                document.getElementById('total-categorias').textContent = data.total_categorias || '0';
                document.getElementById('estoque-baixo').textContent = data.produtos_estoque_baixo || '0';
                document.getElementById('valor-estoque').textContent = `R$ ${(data.valor_total_estoque || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            }
        })
        .catch(error => {
            console.error('Erro ao carregar estatísticas:', error);
            showNotification('Erro ao carregar estatísticas.', 'danger');
        })
        .finally(() => {
             // Esconder spinner movido para a última função de carregamento (ex: carregarProdutosMenosVendidos)
        });
}

// Carregar produtos com estoque baixo para o CARD específico
function carregarProdutosEstoqueBaixoCard() {
    // VERIFICAÇÃO ADICIONADA (assumindo que usa a mesma rota de stats)
    if (typeof API_ROUTES === 'undefined' || !API_ROUTES.stats) {
        console.error('API_ROUTES ou API_ROUTES.stats não está definido para estoque baixo.');
        return;
    }
    axios.get(API_ROUTES.stats) // Ou uma rota específica se houver
        .then(response => {
            if (response.data) {
                document.getElementById('estoque-baixo').textContent = response.data.produtos_estoque_baixo || '0';
            }
        })
        .catch(error => {
            console.error('Erro ao carregar contagem de estoque baixo:', error);
        });
}


// Carregar produtos mais vendidos
function carregarProdutosMaisVendidos() {
    // VERIFICAÇÃO ADICIONADA
    if (typeof API_ROUTES === 'undefined' || !API_ROUTES.produtosMaisVendidos) {
        console.error('API_ROUTES ou API_ROUTES.produtosMaisVendidos não está definido.');
        document.getElementById('mais-vendidos-tabela').innerHTML = '<tr><td colspan="3" class="text-center text-danger">Erro config API.</td></tr>';
        return;
    }
    axios.get(API_ROUTES.produtosMaisVendidos)
        .then(response => {
            const produtos = response.data;
            const tabela = document.getElementById('mais-vendidos-tabela');
            tabela.innerHTML = ''; // Limpa a tabela
            if (produtos && produtos.length > 0) {
                console.log('Produtos mais vendidos:', produtos); // Para debug
                produtos.forEach(produto => {
                    const row = `<tr>
                                    <td>${produto.nome}</td>
                                    <td>${produto.categoria?.nome || 'N/A'}</td>
                                    <td>${produto.total_vendido !== undefined ? produto.total_vendido : 'N/A'}</td>
                                 </tr>`;
                    tabela.innerHTML += row;
                });
            } else {
                tabela.innerHTML = '<tr><td colspan="3" class="text-center">Nenhum produto encontrado.</td></tr>';
            }
        })
        .catch(error => {
            console.error('Erro ao carregar produtos mais vendidos:', error);
            document.getElementById('mais-vendidos-tabela').innerHTML = '<tr><td colspan="3" class="text-center text-danger">Erro ao carregar dados.</td></tr>';
        });
}

// Carregar produtos menos vendidos
function carregarProdutosMenosVendidos() {
    // VERIFICAÇÃO ADICIONADA
    if (typeof API_ROUTES === 'undefined' || !API_ROUTES.produtosMenosVendidos) {
        console.error('API_ROUTES ou API_ROUTES.produtosMenosVendidos não está definido.');
        document.getElementById('menos-vendidos-tabela').innerHTML = '<tr><td colspan="3" class="text-center text-danger">Erro config API.</td></tr>';
        toggleLoading(false); // Esconde o spinner aqui se esta for a última chamada
        return;
    }
    axios.get(API_ROUTES.produtosMenosVendidos)
        .then(response => {
            const produtos = response.data;
            const tabela = document.getElementById('menos-vendidos-tabela');
            tabela.innerHTML = ''; // Limpa a tabela
            if (produtos && produtos.length > 0) {
                produtos.forEach(produto => {
                    const row = `<tr>
                                    <td>${produto.nome}</td>
                                    <td>${produto.categoria?.nome || 'N/A'}</td>
                                    <td>${produto.total_vendido !== undefined ? produto.total_vendido : 'N/A'}</td>
                                 </tr>`;
                    tabela.innerHTML += row;
                });
            } else {
                tabela.innerHTML = '<tr><td colspan="3" class="text-center">Nenhum produto encontrado.</td></tr>';
            }
        })
        .catch(error => {
            console.error('Erro ao carregar produtos menos vendidos:', error);
            document.getElementById('menos-vendidos-tabela').innerHTML = '<tr><td colspan="3" class="text-center text-danger">Erro ao carregar dados.</td></tr>';
        })
         .finally(() => {
             // Esconder o spinner geral aqui, pois esta é a última função de carregamento inicial
             toggleLoading(false);
         });
}


// Criar gráfico de movimentação
function criarGraficoMovimentacao() {
    // VERIFICAÇÃO ADICIONADA
    if (typeof API_ROUTES === 'undefined' || !API_ROUTES.movimentacoesRecentes) {
        console.error('API_ROUTES ou API_ROUTES.movimentacoesRecentes não está definido.');
        // Opcional: Limpar ou mostrar erro no canvas
        const canvas = document.getElementById('graficoMovimentacao');
        if(canvas) {
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillText("Erro ao carregar dados (API Config)", 10, 50);
        }
        return;
    }
    axios.get(API_ROUTES.movimentacoesRecentes)
        .then(response => {
            const data = response.data; // Espera-se { labels: [], entradas: [], saidas: [] }
            const ctx = document.getElementById('graficoMovimentacao').getContext('2d');

            // Destruir gráfico anterior se existir
            if (graficoMovimentacao) {
                graficoMovimentacao.destroy();
            }

             // Cores baseadas no tema atual
            const theme = document.documentElement.getAttribute('data-theme') || 'dark';
            const gridColor = theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
            const fontColor = theme === 'dark' ? '#dfe6e9' : '#555';
            const entradaColor = theme === 'dark' ? '#2ecc71' : '#28a745'; // Verde
            const saidaColor = theme === 'dark' ? '#e74c3c' : '#dc3545'; // Vermelho


            graficoMovimentacao = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels || [],
                    datasets: [
                        {
                            label: 'Entradas',
                            data: data.entradas || [],
                            borderColor: entradaColor,
                            backgroundColor: `${entradaColor}33`, // Verde com opacidade
                            fill: true,
                            tension: 0.3
                        },
                        {
                            label: 'Saídas',
                            data: data.saidas || [],
                            borderColor: saidaColor,
                            backgroundColor: `${saidaColor}33`, // Vermelho com opacidade
                            fill: true,
                            tension: 0.3
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                             labels: {
                                color: fontColor // Cor da legenda
                            }
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: gridColor // Cor da grade Y
                            },
                            ticks: {
                                color: fontColor // Cor dos ticks Y
                            }
                        },
                         x: {
                             grid: {
                                color: gridColor // Cor da grade X
                            },
                            ticks: {
                                color: fontColor // Cor dos ticks X
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
             console.error('Erro ao carregar dados do gráfico:', error);
             // Opcional: Mostrar mensagem de erro no lugar do gráfico
        });
}

// Função para atualizar cores dos gráficos ao mudar tema (pode ficar aqui ou em app.js)
function atualizarTemaGraficos(theme) {
    // Atualiza cores globais do Chart.js (se necessário, mas a configuração por gráfico é mais segura)
    // Chart.defaults.color = theme === 'dark' ? '#dfe6e9' : '#555';
    // Chart.defaults.borderColor = theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';

    // Recriar o gráfico de movimentação para aplicar novas cores
    if (document.getElementById('graficoMovimentacao')) {
        criarGraficoMovimentacao();
    }
    // Recriar outros gráficos se houver
}


// Configurar formulários dos modais (Adicionar Produto, Entrada, Saída)
function configurarFormularios() {
    // Exemplo: Modal Adicionar Produto
    const modalAdicionar = document.getElementById('modalAdicionarProduto');
    if (modalAdicionar) {
        const form = modalAdicionar.querySelector('form'); // Assumindo que há um form
        const btnSalvar = document.getElementById('btnSalvarProduto');

        if (form && btnSalvar) {
            btnSalvar.addEventListener('click', () => {
                // Validar formulário
                if (!form.checkValidity()) {
                    form.reportValidity();
                    return;
                }

                // VERIFICAÇÃO ADICIONADA
                if (typeof API_ROUTES === 'undefined' || !API_ROUTES.produtos) {
                    console.error('API_ROUTES ou API_ROUTES.produtos não está definido para salvar produto.');
                    showNotification('Erro crítico: Configuração de API não encontrada.', 'danger');
                    return;
                }

                toggleLoading(true);
                const dadosProduto = {
                    nome: document.getElementById('nomeProduto').value,
                    codigo_barras: document.getElementById('codigoBarrasProduto').value,
                    categoria_id: document.getElementById('categoriaProduto').value,
                    fornecedor_id: document.getElementById('fornecedorProduto').value, // Certifique-se que este campo existe
                    preco_venda: parseFloat(document.getElementById('precoProduto').value),
                    preco_compra: parseFloat(document.getElementById('precoCompraProduto').value) || null,
                    quantidade: parseInt(document.getElementById('estoqueProduto').value) || 0,
                    estoque_minimo: parseInt(document.getElementById('estoqueMinimoProduto').value) || 0,
                    descricao: document.getElementById('descricaoProduto').value,
                    // Adicione outros campos se necessário (unidade, localização, etc.)
                };

                axios.post(API_ROUTES.produtos, dadosProduto)
                    .then(response => {
                        showNotification(response.data.mensagem || 'Produto adicionado com sucesso!', 'success');
                        bootstrap.Modal.getInstance(modalAdicionar).hide();
                        form.reset();
                        // Atualizar dados relevantes (estatísticas, talvez a lista de produtos se visível)
                        carregarEstatisticas();
                        // Se houver uma tabela de produtos recentes no dashboard, atualizá-la
                    })
                    .catch(error => {
                        console.error("Erro ao adicionar produto:", error);
                        const errorMsg = error.response?.data?.erro || 'Erro ao adicionar produto. Verifique os dados e tente novamente.';
                        showNotification(errorMsg, 'danger');
                    })
                    .finally(() => {
                        toggleLoading(false);
                    });
            });
        }
         // Carregar categorias e fornecedores para os selects do modal
        modalAdicionar.addEventListener('show.bs.modal', () => {
            // VERIFICAÇÃO ADICIONADA
            if (typeof API_ROUTES === 'undefined') {
                 console.error('API_ROUTES não definido ao abrir modal para carregar opções.');
                 // Opcional: Desabilitar ou mostrar erro nos selects
            } else {
                 carregarOpcoesCategorias('categoriaProduto');
                 carregarOpcoesFornecedores('fornecedorProduto'); // Certifique-se que este select existe
            }
        });
    }

    // Configurar Modal Entrada Produto (se existir formulário)
    const modalEntrada = document.getElementById('modalEntradaProduto');
    // ... Lógica similar para o formulário de entrada ...


    // Configurar Modal Saída Produto (se existir formulário)
    const modalSaida = document.getElementById('modalSaidaProduto');
     // ... Lógica similar para o formulário de saída ...

}

// Função para carregar opções de categorias em um select
function carregarOpcoesCategorias(selectId) {
    const select = document.getElementById(selectId);
    if (!select) return;

    // VERIFICAÇÃO ADICIONADA
    if (typeof API_ROUTES === 'undefined' || !API_ROUTES.categorias) {
        console.error('API_ROUTES ou API_ROUTES.categorias não está definido.');
        select.innerHTML = '<option value="">Erro config API</option>';
        return;
    }

    axios.get(API_ROUTES.categorias)
        .then(response => {
            select.innerHTML = '<option value="">Selecione...</option>'; // Opção padrão
            response.data.forEach(cat => {
                select.innerHTML += `<option value="${cat.id}">${cat.nome}</option>`;
            });
        })
        .catch(error => {
            console.error(`Erro ao carregar categorias para ${selectId}:`, error);
            select.innerHTML = '<option value="">Erro ao carregar</option>';
        });
}

// Função para carregar opções de fornecedores em um select
function carregarOpcoesFornecedores(selectId) {
     const select = document.getElementById(selectId);
    if (!select) return;

    // VERIFICAÇÃO ADICIONADA
    if (typeof API_ROUTES === 'undefined' || !API_ROUTES.fornecedores) {
        console.error('API_ROUTES ou API_ROUTES.fornecedores não está definido.');
        select.innerHTML = '<option value="">Erro config API</option>';
        return;
    }

    axios.get(API_ROUTES.fornecedores) // Certifique-se que a rota existe
        .then(response => {
            select.innerHTML = '<option value="">Selecione...</option>'; // Opção padrão
            response.data.forEach(forn => {
                 // Assumindo que a API retorna id e nome_fantasia ou razao_social
                select.innerHTML += `<option value="${forn.id}">${forn.nome_fantasia || forn.razao_social}</option>`;
            });
        })
        .catch(error => {
            console.error(`Erro ao carregar fornecedores para ${selectId}:`, error);
            select.innerHTML = '<option value="">Erro ao carregar</option>';
        });
}

// ... (outras funções específicas do dashboard, como carregarRelatorios, etc.) ...