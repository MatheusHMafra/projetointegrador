let graficoMovimentacao;
let graficoMaisVendidos;
let graficoMenosVendidos;
let graficoEntradasClassificacao;
let graficoSaidasClassificacao;

document.addEventListener("DOMContentLoaded", () => {
  configurarBuscaProdutosDashboard();
  configurarFormulariosDashboard();
  inicializarListenersEstoque();

  const initialSpinner = document.getElementById("loading-spinner-initial");

  Promise.all([
    carregarEstatisticas(),
    carregarProdutosMaisVendidos(),
    carregarProdutosMenosVendidos(),
    criarGraficoMovimentacao(),
  ])
    .catch((error) => {
      console.warn(
        "Uma ou mais APIs falharam, mas o dashboard continuará carregando.",
        error,
      );
    })
    .finally(() => {
      if (initialSpinner) {
        initialSpinner.style.display = "none";
      }
    });
});

function configurarBuscaProdutosDashboard() {
  const buscaInput = document.getElementById("busca-produto");
  if (!buscaInput) return;

  let debounceTimeout;
  buscaInput.addEventListener("input", (e) => {
    clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(() => {
      const termo = e.target.value.trim();
      if (termo.length > 2 || termo.length === 0) {
        console.log("Termo de busca no dashboard:", termo);
      }
    }, 500);
  });
}

function carregarEstatisticas() {
  if (typeof API_ROUTES === "undefined" || !API_ROUTES.DASHBOARD_STATS) {
    console.error(
      "Erro de Configuração: API_ROUTES.DASHBOARD_STATS não definido.",
    );
    return Promise.reject("API_ROUTES.DASHBOARD_STATS não definido.");
  }

  return axios
    .get(API_ROUTES.DASHBOARD_STATS)
    .then((response) => {
      const data = response.data || {};
      const totalProdutosEl = document.getElementById("total-produtos");
      const totalCategoriasEl = document.getElementById("total-categorias");
      const valorEstoqueEl = document.getElementById("valor-estoque");
      const estoqueBaixoEl = document.getElementById("estoque-baixo");

      if (totalProdutosEl)
        totalProdutosEl.textContent = data.total_produtos ?? "0";
      if (totalCategoriasEl)
        totalCategoriasEl.textContent = data.total_categorias ?? "0";
      if (estoqueBaixoEl)
        estoqueBaixoEl.textContent = data.produtos_estoque_baixo ?? "0";
      if (valorEstoqueEl) {
        valorEstoqueEl.textContent = `R$ ${(
          data.valor_total_estoque || 0
        ).toLocaleString("pt-BR", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })}`;
      }

      const inativosEl = document.getElementById("produtos-inativos");
      if (inativosEl && data.produtos_inativos !== undefined) {
        inativosEl.textContent = data.produtos_inativos || "0";
      }

      criarGraficoClassificacao(
        "graficoEntradasClassificacao",
        data.entradas_por_classificacao,
        true,
      );
      criarGraficoClassificacao(
        "graficoSaidasClassificacao",
        data.saidas_por_classificacao,
        false,
      );
    })
    .catch((error) => {
      console.error(
        "Erro ao carregar estatísticas:",
        error.response ? error.response.data : error.message,
      );
      showNotification("Falha ao carregar estatísticas.", "danger");
    });
}

function carregarProdutosMaisVendidos() {
  if (typeof API_ROUTES === "undefined" || !API_ROUTES.PRODUTOS_MAIS_VENDIDOS) {
    console.error(
      "Erro de Configuração: API_ROUTES.PRODUTOS_MAIS_VENDIDOS não definido.",
    );
    return Promise.reject("PRODUTOS_MAIS_VENDIDOS não definido.");
  }

  return axios
    .get(API_ROUTES.PRODUTOS_MAIS_VENDIDOS, { params: { per_page: 5 } })
    .then((response) => {
      const produtos = response.data.produtos || [];
      const canvas = document.getElementById("graficoMaisVendidos");
      if (!canvas) return;
      const ctx = canvas.getContext("2d");

      if (graficoMaisVendidos) {
        graficoMaisVendidos.destroy();
      }

      const labels = produtos.map((p) => p.nome || p.produto_nome || "N/A");
      const values = produtos.map((p) => p.total_vendido || 0);

      const theme =
        document.documentElement.getAttribute("data-theme") || "dark";
      const fontColor = theme === "dark" ? "#dfe6e9" : "#495057";
      const barColor = theme === "dark" ? "#2ecc71" : "#28a745";
      const gridColor =
        theme === "dark" ? "rgba(255, 255, 255, 0.1)" : "rgba(0, 0, 0, 0.08)";

      graficoMaisVendidos = new Chart(ctx, {
        type: "bar",
        data: {
          labels: labels,
          datasets: [
            {
              label: "Qtd. Vendida",
              data: values,
              backgroundColor: barColor,
              borderRadius: 5,
              borderWidth: 0,
            },
          ],
        },
        options: {
          indexAxis: "y",
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
          },
          scales: {
            x: {
              grid: { color: gridColor },
              ticks: { color: fontColor, precision: 0 },
            },
            y: {
              grid: { display: false },
              ticks: { color: fontColor },
            },
          },
        },
      });
    })
    .catch((error) => {
      console.error(
        "Erro ao carregar produtos mais vendidos:",
        error.response ? error.response.data : error.message,
      );
    });
}

function carregarProdutosMenosVendidos() {
  if (
    typeof API_ROUTES === "undefined" ||
    !API_ROUTES.PRODUTOS_MENOS_VENDIDOS
  ) {
    console.error(
      "Erro de Configuração: API_ROUTES.PRODUTOS_MENOS_VENDIDOS não definido.",
    );
    return Promise.reject("PRODUTOS_MENOS_VENDIDOS não definido.");
  }

  return axios
    .get(API_ROUTES.PRODUTOS_MENOS_VENDIDOS, { params: { per_page: 5 } })
    .then((response) => {
      const produtos = response.data.produtos || [];
      const canvas = document.getElementById("graficoMenosVendidos");
      if (!canvas) return;
      const ctx = canvas.getContext("2d");

      if (graficoMenosVendidos) {
        graficoMenosVendidos.destroy();
      }

      const labels = produtos.map((p) => p.nome || p.produto_nome || "N/A");
      const values = produtos.map((p) => p.total_vendido || 0);

      const theme =
        document.documentElement.getAttribute("data-theme") || "dark";
      const fontColor = theme === "dark" ? "#dfe6e9" : "#495057";
      const barColor = theme === "dark" ? "#e74c3c" : "#dc3545";
      const gridColor =
        theme === "dark" ? "rgba(255, 255, 255, 0.1)" : "rgba(0, 0, 0, 0.08)";

      graficoMenosVendidos = new Chart(ctx, {
        type: "bar",
        data: {
          labels: labels,
          datasets: [
            {
              label: "Qtd. Vendida",
              data: values,
              backgroundColor: barColor,
              borderRadius: 5,
              borderWidth: 0,
            },
          ],
        },
        options: {
          indexAxis: "y",
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
          },
          scales: {
            x: {
              grid: { color: gridColor },
              ticks: { color: fontColor, precision: 0 },
            },
            y: {
              grid: { display: false },
              ticks: { color: fontColor },
            },
          },
        },
      });
    })
    .catch((error) => {
      console.error(
        "Erro ao carregar produtos menos vendidos:",
        error.response ? error.response.data : error.message,
      );
    });
}

function criarGraficoMovimentacao() {
  if (
    typeof API_ROUTES === "undefined" ||
    !API_ROUTES.ESTOQUE_MOVIMENTACOES_GRAFICO
  ) {
    console.error(
      "Erro de Configuração: API_ROUTES.ESTOQUE_MOVIMENTACOES_GRAFICO não definido.",
    );
    return Promise.reject("ESTOQUE_MOVIMENTACOES_GRAFICO não definido.");
  }

  return axios
    .get(API_ROUTES.ESTOQUE_MOVIMENTACOES_GRAFICO, { params: { dias: 30 } })
    .then((response) => {
      const data = response.data || {};
      const canvas = document.getElementById("graficoMovimentacao");
      if (!canvas) return;
      const ctx = canvas.getContext("2d");

      if (graficoMovimentacao) {
        graficoMovimentacao.destroy();
      }

      const theme =
        document.documentElement.getAttribute("data-theme") || "dark";
      const gridColor =
        theme === "dark" ? "rgba(255, 255, 255, 0.1)" : "rgba(0, 0, 0, 0.08)";
      const fontColor = theme === "dark" ? "#dfe6e9" : "#495057";
      const entradaColor = theme === "dark" ? "#2ecc71" : "#28a745";
      const saidaColor = theme === "dark" ? "#e74c3c" : "#dc3545";

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
                .alpha(0.1)
                .rgbString(),
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
                .alpha(0.1)
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
              ticks: { color: fontColor, precision: 0 },
            },
            x: {
              grid: { display: false },
              ticks: { color: fontColor },
            },
          },
        },
      });
    })
    .catch((error) => {
      console.error(
        "Erro ao carregar dados do gráfico de movimentação:",
        error.response ? error.response.data : error.message,
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
          canvas.height / 2,
        );
      }
    });
}

function atualizarTemaGraficos() {
  criarGraficoMovimentacao();
  carregarProdutosMaisVendidos();
  carregarProdutosMenosVendidos();
  carregarEstatisticas();
}

function criarGraficoClassificacao(canvasId, dados, isEntrada) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  if (
    canvasId === "graficoEntradasClassificacao" &&
    graficoEntradasClassificacao
  ) {
    graficoEntradasClassificacao.destroy();
  }
  if (canvasId === "graficoSaidasClassificacao" && graficoSaidasClassificacao) {
    graficoSaidasClassificacao.destroy();
  }

  const theme = document.documentElement.getAttribute("data-theme") || "dark";
  const fontColor = theme === "dark" ? "#dfe6e9" : "#495057";

  const mapLabels = isEntrada
    ? {
        reposicao: "Reposição",
        devolucao: "Devolução Cliente",
        outro: "Outro Motivo",
      }
    : {
        venda: "Venda",
        roubo: "Roubo",
        dano: "Dano / Avaria",
        devolucao_fornecedor: "Devol. Fornecedor",
        descarte: "Descarte",
        outro: "Outro Motivo",
      };

  const colors = isEntrada
    ? ["#2ecc71", "#3498db", "#95a5a6"]
    : ["#f1c40f", "#e74c3c", "#e67e22", "#9b59b6", "#d35400", "#95a5a6"];

  const labels = [];
  const values = [];

  Object.keys(dados || {}).forEach((key) => {
    labels.push(mapLabels[key] || key);
    values.push(dados[key] || 0);
  });

  if (labels.length === 0) {
    labels.push("Nenhuma movimentação");
    values.push(0);
  }

  const chart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [
        {
          data: values,
          backgroundColor: colors.slice(0, labels.length),
          borderWidth: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "right",
          labels: { color: fontColor, boxWidth: 12 },
        },
      },
    },
  });

  if (canvasId === "graficoEntradasClassificacao") {
    graficoEntradasClassificacao = chart;
  } else {
    graficoSaidasClassificacao = chart;
  }
}

function atualizarDadosDashboard() {
  carregarEstatisticas();
  criarGraficoMovimentacao();
  carregarProdutosMaisVendidos();
  carregarProdutosMenosVendidos();
}

function configurarFormulariosDashboard() {
  const modalAdicionarProdutoEl = document.getElementById(
    "modalAdicionarProduto",
  );
  if (!modalAdicionarProdutoEl) return;

  const formAdicionarProduto = modalAdicionarProdutoEl.querySelector(
    "#formAdicionarProduto",
  );
  if (formAdicionarProduto) {
    formAdicionarProduto.addEventListener("submit", (event) => {
      event.preventDefault();

      if (typeof API_ROUTES === "undefined" || !API_ROUTES.PRODUTOS_LISTAR) {
        console.error(
          "Erro de Configuração: API_ROUTES.PRODUTOS_LISTAR (POST) não definido.",
        );
        showNotification("Erro de configuração ao salvar produto.", "danger");
        return;
      }

      toggleLoading(true);
      const dadosProduto = {
        codigo: document.getElementById("codigoProduto")?.value?.trim() || null,
        nome: document.getElementById("nomeProduto")?.value?.trim() || null,
        categoria_id:
          document.getElementById("categoriaProduto")?.value || null,
        fornecedor_id: document.getElementById("fornecedorProduto")?.value
          ? parseInt(document.getElementById("fornecedorProduto").value, 10)
          : null,
        preco: parseFloat(document.getElementById("precoProduto")?.value),
        preco_compra:
          parseFloat(document.getElementById("precoCompraProduto")?.value) ||
          null,
        estoque: parseInt(
          document.getElementById("estoqueProduto")?.value || "0",
          10,
        ),
        estoque_minimo: parseInt(
          document.getElementById("estoqueMinimoProduto")?.value || "0",
          10,
        ),
        descricao: document.getElementById("descricaoProduto")?.value || "",
      };

      if (
        !dadosProduto.nome ||
        !dadosProduto.categoria_id ||
        !dadosProduto.preco ||
        !dadosProduto.codigo ||
        !dadosProduto.fornecedor_id
      ) {
        showNotification(
          "Código, Nome, Categoria, Fornecedor e Preço de Venda são obrigatórios.",
          "warning",
        );
        toggleLoading(false);
        return;
      }

      if (
        dadosProduto.preco_compra !== null &&
        dadosProduto.preco_compra <= 0
      ) {
        showNotification(
          "O preço de compra deve ser maior que zero.",
          "warning",
        );
        toggleLoading(false);
        return;
      }
      if (dadosProduto.preco <= 0) {
        showNotification(
          "O preço de venda deve ser maior que zero.",
          "warning",
        );
        toggleLoading(false);
        return;
      }
      if (dadosProduto.estoque < 0) {
        showNotification("O estoque não pode ser negativo.", "warning");
        toggleLoading(false);
        return;
      }
      if (dadosProduto.estoque_minimo < 0) {
        showNotification("O estoque mínimo não pode ser negativo.", "warning");
        toggleLoading(false);
        return;
      }

      axios
        .post(API_ROUTES.PRODUTOS_LISTAR, dadosProduto)
        .then((response) => {
          showNotification(
            response.data.message || "Produto adicionado com sucesso!",
            "success",
          );
          bootstrap.Modal.getInstance(modalAdicionarProdutoEl).hide();
          formAdicionarProduto.reset();
          carregarEstatisticas();
        })
        .catch((error) => {
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

  modalAdicionarProdutoEl.addEventListener("show.bs.modal", () => {
    carregarOpcoesCategoriasParaModal("categoriaProduto");
    carregarOpcoesFornecedoresParaModal("fornecedorProduto");
  });
}

function carregarOpcoesCategoriasParaModal(selectId) {
  const selectEl = document.getElementById(selectId);
  if (!selectEl) return;

  if (typeof API_ROUTES === "undefined" || !API_ROUTES.CATEGORIAS_LISTAR) {
    console.error(
      "Erro de Configuração: API_ROUTES.CATEGORIAS_LISTAR não definido.",
    );
    selectEl.innerHTML = '<option value="">Erro Config API</option>';
    return;
  }

  axios
    .get(API_ROUTES.CATEGORIAS_LISTAR)
    .then((response) => {
      selectEl.innerHTML =
        '<option value="">Selecione uma categoria...</option>';
      (response.data || []).forEach((categoria) => {
        selectEl.innerHTML += `<option value="${categoria.id}">${categoria.nome}</option>`;
      });
    })
    .catch(() => {
      selectEl.innerHTML = '<option value="">Falha ao carregar</option>';
    });
}

function carregarOpcoesFornecedoresParaModal(selectId) {
  const selectEl = document.getElementById(selectId);
  if (!selectEl) return;

  if (typeof API_ROUTES === "undefined" || !API_ROUTES.FORNECEDORES_LISTAR) {
    console.error(
      "Erro de Configuração: API_ROUTES.FORNECEDORES_LISTAR não definido.",
    );
    selectEl.innerHTML = '<option value="">Erro Config API</option>';
    return;
  }

  axios
    .get(API_ROUTES.FORNECEDORES_LISTAR, {
      params: { ativo: "true", per_page: 200 },
    })
    .then((response) => {
      selectEl.innerHTML =
        '<option value="">Selecione um fornecedor...</option>';
      const fornecedores = response.data.fornecedores || [];
      fornecedores.forEach((fornecedor) => {
        selectEl.innerHTML += `<option value="${fornecedor.id}">${fornecedor.nome}</option>`;
      });
    })
    .catch(() => {
      selectEl.innerHTML = '<option value="">Falha ao carregar</option>';
    });
}

function inicializarListenersEstoque() {
  const modalEntrada = document.getElementById("modalEntradaProduto");
  const modalSaida = document.getElementById("modalSaidaProduto");
  const btnSubmeterEntrada = document.getElementById("btnSubmeterEntrada");
  const btnSubmeterSaida = document.getElementById("btnSubmeterSaida");

  const userLevel = (window.currentUserInfo?.level || "").toLowerCase();
  const isOperador = userLevel === "operador";

  if (modalEntrada) {
    modalEntrada.addEventListener("show.bs.modal", () => {
      carregarProdutosParaSelect("produtoEntrada");
    });
  }

  if (modalSaida) {
    modalSaida.addEventListener("show.bs.modal", () => {
      carregarProdutosParaSelect("produtoSaida");
      // Se for operador, restringir classificação apenas para venda
      const classificacaoContainer = document.getElementById("classificacaoSaidaContainer");
      const classificacaoSelect = document.getElementById("classificacaoSaida");
      if (isOperador) {
        if (classificacaoSelect) {
          classificacaoSelect.value = "venda";
        }
        if (classificacaoContainer) {
          classificacaoContainer.style.display = "none";
        }
      } else {
        if (classificacaoContainer) {
          classificacaoContainer.style.display = "block";
        }
      }
    });
  }

  if (btnSubmeterEntrada) {
    btnSubmeterEntrada.addEventListener("click", submeterEntradaProduto);
  }

  if (btnSubmeterSaida) {
    btnSubmeterSaida.addEventListener("click", submeterSaidaProduto);
  }
}

function carregarProdutosParaSelect(selectId) {
  const select = document.getElementById(selectId);
  if (!select) return;

  if (typeof API_ROUTES === "undefined" || !API_ROUTES.PRODUTOS_LISTAR) {
    select.innerHTML = '<option value="">Erro ao carregar</option>';
    return;
  }

  axios
    .get(API_ROUTES.PRODUTOS_LISTAR, { params: { per_page: 500 } })
    .then((response) => {
      const produtos = response.data.produtos || [];
      select.innerHTML = '<option value="">Selecione um produto...</option>';
      produtos.forEach((produto) => {
        const ativo = produto.ativo === undefined ? true : !!produto.ativo;
        if (ativo) {
          select.innerHTML += `<option value="${produto.id}">${produto.nome} (Est: ${produto.estoque || 0})</option>`;
        }
      });
    })
    .catch(() => {
      select.innerHTML = '<option value="">Falha ao carregar</option>';
    });
}

function submeterEntradaProduto() {
  const produtoId = document.getElementById("produtoEntrada")?.value;
  const quantidade = document.getElementById("qtdEntrada")?.value;
  const motivo =
    document.getElementById("motivoEntrada")?.value?.trim() || "Entrada manual";
  const classificacao = document.getElementById("classificacaoEntrada")?.value;

  if (!produtoId || !quantidade || parseInt(quantidade, 10) <= 0) {
    showNotification("Dados inválidos para entrada.", "warning");
    return;
  }

  if (typeof API_ROUTES === "undefined" || !API_ROUTES.ESTOQUE_ENTRADA) {
    showNotification("Erro de configuração ao registrar entrada.", "danger");
    return;
  }

  toggleLoading(true);
  axios
    .post(API_ROUTES.ESTOQUE_ENTRADA, {
      produto_id: parseInt(produtoId, 10),
      quantidade: parseInt(quantidade, 10),
      observacao: motivo,
      classificacao: classificacao,
    })
    .then((response) => {
      showNotification(
        response.data.message || "Entrada registrada com sucesso!",
        "success",
      );
      const modal = bootstrap.Modal.getInstance(
        document.getElementById("modalEntradaProduto"),
      );
      if (modal) modal.hide();
      document.getElementById("formEntradaProduto")?.reset();
      atualizarDadosDashboard();
    })
    .catch((error) => {
      showNotification(
        error.response?.data?.error || "Erro ao registrar entrada.",
        "danger",
      );
    })
    .finally(() => {
      toggleLoading(false);
    });
}

function submeterSaidaProduto() {
  const produtoId = document.getElementById("produtoSaida")?.value;
  const quantidade = document.getElementById("qtdSaida")?.value;
  const motivo =
    document.getElementById("motivoSaida")?.value?.trim() || "Saída manual";
  const classificacao = document.getElementById("classificacaoSaida")?.value;

  if (!produtoId || !quantidade || parseInt(quantidade, 10) <= 0) {
    showNotification("Dados inválidos para saída.", "warning");
    return;
  }

  if (typeof API_ROUTES === "undefined" || !API_ROUTES.ESTOQUE_SAIDA) {
    showNotification("Erro de configuração ao registrar saída.", "danger");
    return;
  }

  toggleLoading(true);
  axios
    .post(API_ROUTES.ESTOQUE_SAIDA, {
      produto_id: parseInt(produtoId, 10),
      quantidade: parseInt(quantidade, 10),
      observacao: motivo,
      classificacao: classificacao,
    })
    .then((response) => {
      showNotification(
        response.data.message || "Saída registrada com sucesso!",
        "success",
      );
      const modal = bootstrap.Modal.getInstance(
        document.getElementById("modalSaidaProduto"),
      );
      if (modal) modal.hide();
      document.getElementById("formSaidaProduto")?.reset();
      atualizarDadosDashboard();
    })
    .catch((error) => {
      showNotification(
        error.response?.data?.error || "Erro ao registrar saída.",
        "danger",
      );
    })
    .finally(() => {
      toggleLoading(false);
    });
}

document.addEventListener("themeChanged", () => {
  atualizarTemaGraficos();
});
