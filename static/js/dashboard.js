// Configuração global do Axios (se não estiver em app.js, pode ser definida aqui)
// axios.defaults.headers.post['Content-Type'] = 'application/json';

// Variável global para o gráfico de movimentação
let graficoMovimentacao;

/**
 * Inicialização do Dashboard
 * Chamado quando o DOM está completamente carregado.
 */
document.addEventListener("DOMContentLoaded", () => {
  // Configurações iniciais e carregamento de dados.
  // As funções showNotification e toggleLoading são esperadas de app.js
  // Se não estiverem lá, precisam ser definidas ou importadas aqui.

  // Carregar dados iniciais para o dashboard
  carregarEstatisticas();
  carregarProdutosEstoqueBaixoCard(); // Para o card específico de estoque baixo
  carregarProdutosMaisVendidos();
  carregarProdutosMenosVendidos();

  // Configurar interações da UI
  configurarBuscaProdutosDashboard(); // Renomeado para clareza
  configurarFormulariosDashboard(); // Renomeado para clareza

  // Criar ou atualizar o gráfico de movimentação
  criarGraficoMovimentacao();

  // Esconder o spinner de carregamento inicial após um tempo (ou após todas as chamadas async)
  const initialSpinner = document.getElementById("loading-spinner-initial");
  if (initialSpinner) {
    // Idealmente, esconder após a última chamada assíncrona ter completado.
    // Por simplicidade, um timeout pode ser usado, mas não é o ideal.
    // O toggleLoading(false) no finally da última chamada de dados é melhor.
    setTimeout(() => {
      initialSpinner.style.display = "none";
    }, 700); // Ajuste conforme necessário
  }

  // Opcional: Atualizar dados periodicamente
  // setInterval(() => {
  //     carregarEstatisticas();
  //     carregarProdutosEstoqueBaixoCard();
  //     carregarProdutosMaisVendidos();
  //     carregarProdutosMenosVendidos();
  //     criarGraficoMovimentacao(); // Ou uma função de atualização do gráfico
  // }, 300000); // A cada 5 minutos
});

/**
 * Configura a funcionalidade de busca de produtos no dashboard.
 * Nota: A busca no dashboard pode ter um comportamento diferente da busca na página de produtos.
 */
function configurarBuscaProdutosDashboard() {
  const buscaInput = document.getElementById("busca-produto"); // ID do campo de busca no dashboard
  if (!buscaInput) return;

  let debounceTimeout;
  buscaInput.addEventListener("input", (e) => {
    clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(() => {
      const termo = e.target.value.trim();
      if (termo.length > 2 || termo.length === 0) {
        console.log("Termo de busca no dashboard:", termo);
        // Implementar lógica de busca específica para o dashboard se necessário,
        // ou redirecionar para a página de produtos com o termo.
        // Ex: window.location.href = `/produtos/page?termo=${encodeURIComponent(termo)}`;
      }
    }, 500); // Atraso de 500ms
  });
}

/**
 * Carrega as estatísticas principais do dashboard.
 */
function carregarEstatisticas() {
  if (typeof API_ROUTES === "undefined" || !API_ROUTES.DASHBOARD_STATS) {
    console.error(
      "Erro de Configuração: API_ROUTES.DASHBOARD_STATS não está definido. Verifique api-routes.js e a ordem de carregamento dos scripts."
    );
    showNotification("Erro ao carregar estatísticas (Config API).", "danger");
    toggleLoading(false); // Esconder spinner se houver erro crítico
    return;
  }

  toggleLoading(true); // Mostrar spinner geral
  axios
    .get(API_ROUTES.DASHBOARD_STATS)
    .then((response) => {
      const data = response.data;
      if (data) {
        document.getElementById("total-produtos").textContent =
          data.total_produtos || "0";
        document.getElementById("total-categorias").textContent =
          data.total_categorias || "0";
        // O card de "Estoque Baixo" (contagem) é preenchido por carregarProdutosEstoqueBaixoCard.
        document.getElementById("valor-estoque").textContent = `R$ ${(
          data.valor_total_estoque || 0
        ).toLocaleString("pt-BR", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })}`;
      }
    })
    .catch((error) => {
      console.error(
        "Erro ao carregar estatísticas:",
        error.response ? error.response.data : error.message
      );
      showNotification("Falha ao carregar estatísticas.", "danger");
    })
    .finally(() => {
      // Não esconder o spinner aqui; deixar para a última função de carregamento de dados.
    });
}

/**
 * Carrega a contagem e uma lista resumida de produtos com estoque baixo para o card específico.
 */
function carregarProdutosEstoqueBaixoCard() {
  // Esta função também usa API_ROUTES.DASHBOARD_STATS se essa rota já inclui
  // a contagem e uma pequena lista de produtos com estoque baixo.
  // Se for uma rota separada, ajuste API_ROUTES.PRODUTOS_ESTOQUE_BAIXO_LISTA.
  if (typeof API_ROUTES === "undefined" || !API_ROUTES.DASHBOARD_STATS) {
    // Assumindo que DASHBOARD_STATS inclui essa info
    console.error(
      "Erro de Configuração: API_ROUTES.DASHBOARD_STATS (para estoque baixo) não definido."
    );
    return; // Não mostra notificação para não poluir, mas loga o erro.
  }

  axios
    .get(API_ROUTES.DASHBOARD_STATS) // Ou API_ROUTES.PRODUTOS_ESTOQUE_BAIXO_LISTA
    .then((response) => {
      const data = response.data;
      if (data) {
        // Atualiza a contagem no card de estatísticas
        document.getElementById("estoque-baixo").textContent =
          data.produtos_estoque_baixo || "0";

        // Popula a lista no card "Estoque Baixo"
        const listaEstoqueBaixoEl = document.getElementById(
          "estoque-baixo-lista"
        );
        if (listaEstoqueBaixoEl) {
          listaEstoqueBaixoEl.innerHTML = ""; // Limpar lista anterior
          // Supondo que a API DASHBOARD_STATS retorne `data.produtos_estoque_baixo_lista_dashboard`
          const produtosBaixo =
            data.produtos_estoque_baixo_lista_dashboard || []; // Use um nome de chave apropriado

          if (produtosBaixo.length > 0) {
            produtosBaixo.slice(0, 5).forEach((produto) => {
              // Mostrar até 5 itens
              const li = document.createElement("li");
              li.className =
                "list-group-item d-flex justify-content-between align-items-center";
              li.innerHTML = `
                                <small>${produto.nome}</small>
                                <span class="badge bg-warning rounded-pill">${produto.estoque}</span>
                            `;
              listaEstoqueBaixoEl.appendChild(li);
            });
          } else if (parseInt(data.produtos_estoque_baixo || 0) > 0) {
            listaEstoqueBaixoEl.innerHTML =
              '<li class="list-group-item text-center text-muted small">Ver detalhes na página de produtos.</li>';
          } else {
            listaEstoqueBaixoEl.innerHTML =
              '<li class="list-group-item text-center text-muted small">Nenhum produto com estoque baixo.</li>';
          }
        }
      }
    })
    .catch((error) => {
      console.error(
        "Erro ao carregar dados de estoque baixo para o card:",
        error.response ? error.response.data : error.message
      );
      const listaEstoqueBaixoEl = document.getElementById(
        "estoque-baixo-lista"
      );
      if (listaEstoqueBaixoEl)
        listaEstoqueBaixoEl.innerHTML =
          '<li class="list-group-item text-center text-danger small">Erro ao carregar.</li>';
    });
}

/**
 * Carrega a lista de produtos mais vendidos para a tabela do dashboard.
 */
function carregarProdutosMaisVendidos() {
  if (typeof API_ROUTES === "undefined" || !API_ROUTES.PRODUTOS_MAIS_VENDIDOS) {
    console.error(
      "Erro de Configuração: API_ROUTES.PRODUTOS_MAIS_VENDIDOS não definido."
    );
    const tabela = document.getElementById("mais-vendidos-tabela");
    if (tabela)
      tabela.innerHTML =
        '<tr><td colspan="3" class="text-center text-danger small">Erro de configuração (API).</td></tr>';
    return;
  }

  axios
    .get(API_ROUTES.PRODUTOS_MAIS_VENDIDOS, { params: { per_page: 5 } }) // Limitar a 5 itens para o dashboard
    .then((response) => {
      const produtos = response.data.produtos || []; // A API /produtos/mais-vendidos retorna { produtos: [...] }
      const tabela = document.getElementById("mais-vendidos-tabela");
      tabela.innerHTML = ""; // Limpar
      if (produtos.length > 0) {
        produtos.forEach((produto) => {
          const row = `<tr>
                                    <td><small>${
                                      produto.nome || produto.produto_nome
                                    }</small></td>
                                    <td><small>${
                                      produto.categoria_nome || "N/A"
                                    }</small></td>
                                    <td><small>${
                                      produto.total_vendido !== undefined
                                        ? produto.total_vendido
                                        : "N/A"
                                    }</small></td>
                                 </tr>`;
          tabela.innerHTML += row;
        });
      } else {
        tabela.innerHTML =
          '<tr><td colspan="3" class="text-center small">Nenhum produto vendido recentemente.</td></tr>';
      }
    })
    .catch((error) => {
      console.error(
        "Erro ao carregar produtos mais vendidos:",
        error.response ? error.response.data : error.message
      );
      const tabela = document.getElementById("mais-vendidos-tabela");
      if (tabela)
        tabela.innerHTML =
          '<tr><td colspan="3" class="text-center text-danger small">Falha ao carregar dados.</td></tr>';
    });
}

/**
 * Carrega a lista de produtos menos vendidos para a tabela do dashboard.
 */
function carregarProdutosMenosVendidos() {
  if (
    typeof API_ROUTES === "undefined" ||
    !API_ROUTES.PRODUTOS_MENOS_VENDIDOS
  ) {
    console.error(
      "Erro de Configuração: API_ROUTES.PRODUTOS_MENOS_VENDIDOS não definido."
    );
    const tabela = document.getElementById("menos-vendidos-tabela");
    if (tabela)
      tabela.innerHTML =
        '<tr><td colspan="3" class="text-center text-danger small">Erro de configuração (API).</td></tr>';
    toggleLoading(false); // Esconder spinner se esta for a última chamada de dados
    return;
  }

  axios
    .get(API_ROUTES.PRODUTOS_MENOS_VENDIDOS, { params: { per_page: 5 } }) // Limitar a 5 itens
    .then((response) => {
      const produtos = response.data.produtos || []; // A API /produtos/menos-vendidos retorna { produtos: [...] }
      const tabela = document.getElementById("menos-vendidos-tabela");
      tabela.innerHTML = ""; // Limpar
      if (produtos.length > 0) {
        produtos.forEach((produto) => {
          const row = `<tr>
                                    <td><small>${
                                      produto.nome || produto.produto_nome
                                    }</small></td>
                                    <td><small>${
                                      produto.categoria_nome || "N/A"
                                    }</small></td>
                                    <td><small>${
                                      produto.total_vendido !== undefined
                                        ? produto.total_vendido
                                        : "N/A"
                                    }</small></td>
                                 </tr>`;
          tabela.innerHTML += row;
        });
      } else {
        tabela.innerHTML =
          '<tr><td colspan="3" class="text-center small">Nenhum dado de produtos menos vendidos.</td></tr>';
      }
    })
    .catch((error) => {
      console.error(
        "Erro ao carregar produtos menos vendidos:",
        error.response ? error.response.data : error.message
      );
      const tabela = document.getElementById("menos-vendidos-tabela");
      if (tabela)
        tabela.innerHTML =
          '<tr><td colspan="3" class="text-center text-danger small">Falha ao carregar dados.</td></tr>';
    })
    .finally(() => {
      toggleLoading(false); // Esconder o spinner geral aqui, assumindo que esta é a última função de carregamento.
    });
}

/**
 * Cria ou atualiza o gráfico de movimentação de estoque.
 */
function criarGraficoMovimentacao() {
  if (
    typeof API_ROUTES === "undefined" ||
    !API_ROUTES.ESTOQUE_MOVIMENTACOES_GRAFICO
  ) {
    console.error(
      "Erro de Configuração: API_ROUTES.ESTOQUE_MOVIMENTACOES_GRAFICO não definido."
    );
    const canvas = document.getElementById("graficoMovimentacao");
    if (canvas) {
      const ctx = canvas.getContext("2d");
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.font = "14px Roboto, sans-serif"; // Usar a fonte do tema
      ctx.fillStyle =
        document.documentElement.getAttribute("data-theme") === "dark"
          ? "#dfe6e9"
          : "#555";
      ctx.textAlign = "center";
      ctx.fillText(
        "Erro ao carregar dados do gráfico (Config API).",
        canvas.width / 2,
        canvas.height / 2
      );
    }
    return;
  }

  axios
    .get(API_ROUTES.ESTOQUE_MOVIMENTACOES_GRAFICO, { params: { dias: 30 } }) // Padrão de 30 dias
    .then((response) => {
      const data = response.data;
      const canvas = document.getElementById("graficoMovimentacao");
      if (!canvas) {
        console.error("Elemento canvas 'graficoMovimentacao' não encontrado.");
        return;
      }
      const ctx = canvas.getContext("2d");

      if (graficoMovimentacao) {
        // Destruir gráfico anterior para evitar sobreposição
        graficoMovimentacao.destroy();
      }

      const theme =
        document.documentElement.getAttribute("data-theme") || "dark";
      const gridColor =
        theme === "dark" ? "rgba(255, 255, 255, 0.1)" : "rgba(0, 0, 0, 0.08)";
      const fontColor = theme === "dark" ? "#dfe6e9" : "#495057";
      const entradaColor = theme === "dark" ? "#2ecc71" : "#28a745"; // Verde
      const saidaColor = theme === "dark" ? "#e74c3c" : "#dc3545"; // Vermelho

      graficoMovimentacao = new Chart(ctx, {
        type: "line",
        data: {
          labels: data.labels || [],
          datasets: [
            {
              label: "Entradas",
              data: data.entradas || [],
              borderColor: entradaColor,
              backgroundColor: Chart.helpers
                .color(entradaColor)
                .alpha(0.2)
                .rgbString(), // Cor com opacidade
              fill: true,
              tension: 0.3,
              pointBackgroundColor: entradaColor,
              pointRadius: 3,
              pointHoverRadius: 5,
            },
            {
              label: "Saídas",
              data: data.saidas || [],
              borderColor: saidaColor,
              backgroundColor: Chart.helpers
                .color(saidaColor)
                .alpha(0.2)
                .rgbString(),
              fill: true,
              tension: 0.3,
              pointBackgroundColor: saidaColor,
              pointRadius: 3,
              pointHoverRadius: 5,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: "top",
              labels: { color: fontColor, usePointStyle: true, padding: 20 },
            },
            tooltip: {
              mode: "index",
              intersect: false,
              backgroundColor: theme === "dark" ? "#343a40" : "#fff",
              titleColor: fontColor,
              bodyColor: fontColor,
              borderColor: gridColor,
              borderWidth: 1,
              padding: 10,
              cornerRadius: 4,
            },
          },
          scales: {
            y: {
              beginAtZero: true,
              grid: { color: gridColor, zeroLineColor: gridColor },
              ticks: { color: fontColor, precision: 0 }, // Sem casas decimais para quantidade
            },
            x: {
              grid: { display: false }, // Opcional: remover grade vertical
              ticks: { color: fontColor },
            },
          },
          animation: {
            duration: 800, // Duração da animação
          },
        },
      });
    })
    .catch((error) => {
      console.error(
        "Erro ao carregar dados do gráfico de movimentação:",
        error.response ? error.response.data : error.message
      );
      const canvas = document.getElementById("graficoMovimentacao");
      if (canvas) {
        const ctx = canvas.getContext("2d");
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.font = "14px Roboto, sans-serif";
        ctx.fillStyle =
          document.documentElement.getAttribute("data-theme") === "dark"
            ? "#dfe6e9"
            : "#555";
        ctx.textAlign = "center";
        ctx.fillText(
          "Falha ao carregar dados do gráfico.",
          canvas.width / 2,
          canvas.height / 2
        );
      }
    });
}

/**
 * Atualiza as cores dos gráficos quando o tema da aplicação é alterado.
 * Esta função é chamada pelo listener de evento 'themeChanged' em app.js.
 * @param {string} newTheme - O novo tema ('dark' ou 'light').
 */
function atualizarTemaGraficos(newTheme) {
  if (document.getElementById("graficoMovimentacao")) {
    criarGraficoMovimentacao(); // Recria o gráfico, que pegará as cores do tema atual
  }
  // Adicionar lógica para atualizar outros gráficos se houver
}

/**
 * Configura os formulários dos modais do dashboard (ex: Adicionar Produto Rápido).
 */
function configurarFormulariosDashboard() {
  const modalAdicionarProdutoEl = document.getElementById(
    "modalAdicionarProduto"
  );
  if (modalAdicionarProdutoEl) {
    const formAdicionarProduto = modalAdicionarProdutoEl.querySelector(
      "#formAdicionarProduto"
    );
    // O botão de salvar já está dentro do form, então o evento 'submit' do form é suficiente.

    if (formAdicionarProduto) {
      formAdicionarProduto.addEventListener("submit", (event) => {
        event.preventDefault(); // Prevenir o comportamento padrão de submissão do formulário

        if (typeof API_ROUTES === "undefined" || !API_ROUTES.PRODUTOS_LISTAR) {
          // POST para /produtos
          console.error(
            "Erro de Configuração: API_ROUTES.PRODUTOS_LISTAR (para POST) não definido."
          );
          showNotification("Erro de configuração ao salvar produto.", "danger");
          return;
        }

        toggleLoading(true);
        const dadosProduto = {
          nome: document.getElementById("nomeProduto").value,
          categoria_id: document.getElementById("categoriaProduto").value,
          preco: parseFloat(document.getElementById("precoProduto").value), // Preço de Venda
          preco_compra:
            parseFloat(document.getElementById("precoCompraProduto").value) ||
            null,
          estoque:
            parseInt(document.getElementById("estoqueProduto").value) || 0, // Estoque Inicial
          estoque_minimo:
            parseInt(document.getElementById("estoqueMinimoProduto").value) ||
            0,
          descricao: document.getElementById("descricaoProduto").value,
          // Adicionar 'codigo' se o campo existir no formulário e for opcional
          // codigo: document.getElementById('codigoProdutoModal').value || undefined,
        };

        axios
          .post(API_ROUTES.PRODUTOS_LISTAR, dadosProduto)
          .then((response) => {
            showNotification(
              response.data.message || "Produto adicionado com sucesso!",
              "success"
            );
            bootstrap.Modal.getInstance(modalAdicionarProdutoEl).hide();
            formAdicionarProduto.reset();
            // Atualizar dados relevantes no dashboard
            carregarEstatisticas();
            // Se a lista de produtos mais/menos vendidos puder ser afetada, recarregá-las
            // carregarProdutosMaisVendidos();
            // carregarProdutosMenosVendidos();
          })
          .catch((error) => {
            console.error(
              "Erro ao adicionar produto via modal:",
              error.response ? error.response.data : error.message
            );
            const errorMsg =
              error.response?.data?.error ||
              "Erro ao adicionar produto. Verifique os dados.";
            showNotification(errorMsg, "danger");
          })
          .finally(() => {
            toggleLoading(false);
          });
      });
    }

    // Carregar opções para selects quando o modal for aberto
    modalAdicionarProdutoEl.addEventListener("show.bs.modal", () => {
      if (typeof API_ROUTES === "undefined") {
        console.error(
          "API_ROUTES não definido ao abrir modal Adicionar Produto para carregar opções."
        );
        return;
      }
      carregarOpcoesCategoriasParaModal("categoriaProduto"); // ID do select no modal
      // Se houver select de fornecedor no modal:
      // carregarOpcoesFornecedoresParaModal('fornecedorProdutoModal');
    });
  }
  // Configurar outros modais (Entrada, Saída, Relatórios) se eles tiverem formulários
}

/**
 * Carrega as opções de categorias em um elemento select (específico para modais do dashboard).
 * @param {string} selectId - O ID do elemento select.
 */
function carregarOpcoesCategoriasParaModal(selectId) {
  const selectEl = document.getElementById(selectId);
  if (!selectEl) {
    console.warn(`Select com ID '${selectId}' não encontrado no modal.`);
    return;
  }

  if (typeof API_ROUTES === "undefined" || !API_ROUTES.CATEGORIAS_LISTAR) {
    console.error(
      "Erro de Configuração: API_ROUTES.CATEGORIAS_LISTAR não definido."
    );
    selectEl.innerHTML = '<option value="">Erro Config API</option>';
    return;
  }

  axios
    .get(API_ROUTES.CATEGORIAS_LISTAR)
    .then((response) => {
      selectEl.innerHTML =
        '<option value="">Selecione uma categoria...</option>';
      // A API /produtos/categorias retorna a lista diretamente
      (response.data || []).forEach((categoria) => {
        selectEl.innerHTML += `<option value="${categoria.id}">${categoria.nome}</option>`;
      });
    })
    .catch((error) => {
      console.error(
        `Erro ao carregar categorias para o select '${selectId}':`,
        error.response ? error.response.data : error.message
      );
      selectEl.innerHTML = '<option value="">Falha ao carregar</option>';
    });
}

// Se precisar de fornecedores no modal de "Adicionar Produto" do dashboard:
/*
function carregarOpcoesFornecedoresParaModal(selectId) {
    const selectEl = document.getElementById(selectId);
    if (!selectEl) return;

    if (typeof API_ROUTES === 'undefined' || !API_ROUTES.FORNECEDORES_LISTAR) {
        console.error('Erro de Configuração: API_ROUTES.FORNECEDORES_LISTAR não definido.');
        selectEl.innerHTML = '<option value="">Erro Config API</option>';
        return;
    }
    // Busca apenas fornecedores ativos para o select
    axios.get(API_ROUTES.FORNECEDORES_LISTAR, { params: { ativo: 'true', per_page: 200 } }) // Pegar muitos para preencher select
        .then(response => {
            selectEl.innerHTML = '<option value="">Selecione um fornecedor...</option>';
            const fornecedores = response.data.fornecedores || [];
            fornecedores.forEach(forn => {
                selectEl.innerHTML += `<option value="${forn.id}">${forn.nome}</option>`;
            });
        })
        .catch(error => {
            console.error(`Erro ao carregar fornecedores para o select '${selectId}':`, error);
            selectEl.innerHTML = '<option value="">Falha ao carregar</option>';
        });
}
*/

// Listener para o evento 'themeChanged' (definido em app.js) para atualizar gráficos
document.addEventListener("themeChanged", (event) => {
  const newTheme = event.detail.theme;
  // console.log(`Dashboard: Tema alterado para ${newTheme}, atualizando gráficos.`); // Para debug
  atualizarTemaGraficos(newTheme);
});
