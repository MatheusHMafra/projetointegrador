document.addEventListener("DOMContentLoaded", () => {
  if (
    typeof API_ROUTES === "undefined" ||
    !API_ROUTES.ESTOQUE_MOVIMENTACOES_LISTAR
  ) {
    console.error(
      "API_ROUTES ou API_ROUTES.ESTOQUE_MOVIMENTACOES_LISTAR não definido.",
    );
    showNotification(
      "Erro de configuração de API. Verifique o console.",
      "danger",
    );
    return;
  }

  carregarMovimentacoes();
  configurarFiltrosMovimentacoes();
});

let currentPageMov = 1;
const perPageMov = 15;

function carregarMovimentacoes(page = 1, filtros = {}) {
  currentPageMov = page;
  const placeholder = document.getElementById("movimentacoes-placeholder");
  const tabelaCorpo = document.getElementById("movimentacoes-tabela-corpo");
  const paginacaoNav = document.getElementById("paginacao-movimentacoes-nav");

  toggleLoading(true);
  if (placeholder) placeholder.textContent = "Carregando movimentações...";
  if (tabelaCorpo) tabelaCorpo.innerHTML = "";

  let params = { page: currentPageMov, per_page: perPageMov, ...filtros };

  Object.keys(params).forEach((key) => {
    if (
      params[key] === "" ||
      params[key] === null ||
      params[key] === undefined
    ) {
      delete params[key];
    }
  });

  if (params.produto_id_ou_nome) {
    if (!isNaN(parseInt(params.produto_id_ou_nome))) {
      params.produto_id = parseInt(params.produto_id_ou_nome);
    } else {
      console.warn(
        "Filtro por nome de produto não implementado diretamente na API de movimentações. Filtro por nome ignorado.",
      );
      delete params.produto_id_ou_nome;
    }
    delete params.produto_id_ou_nome;
  }

  axios
    .get(API_ROUTES.ESTOQUE_MOVIMENTACOES_LISTAR, { params })
    .then((response) => {
      const data = response.data;
      if (data && data.movimentacoes) {
        const totalRegistrosEl = document.getElementById("total-registros");
        if (totalRegistrosEl && data.total !== undefined) {
          totalRegistrosEl.textContent = `Total: ${data.total}`;
        }
        montarTabelaMovimentacoes(data.movimentacoes);
        montarPaginacaoMovimentacoes(
          data.total,
          data.pages,
          data.page,
          data.per_page,
        );
        if (data.movimentacoes.length === 0 && placeholder) {
          placeholder.textContent =
            "Nenhuma movimentação encontrada para os filtros aplicados.";
          tabelaCorpo.innerHTML = `<tr><td colspan="10" class="text-center">${placeholder.textContent}</td></tr>`;
        }
        if (paginacaoNav)
          paginacaoNav.style.display =
            data.movimentacoes.length > 0 ? "block" : "none";
      } else {
        if (placeholder)
          placeholder.textContent =
            "Não foi possível carregar as movimentações.";
        if (tabelaCorpo)
          tabelaCorpo.innerHTML = `<tr><td colspan="10" class="text-center">${placeholder.textContent}</td></tr>`;
      }
    })
    .catch((error) => {
      console.error("Erro ao carregar movimentações:", error);
      const errorMsg =
        error.response?.data?.error || "Falha ao carregar movimentações.";
      showNotification(errorMsg, "danger");
      if (placeholder) placeholder.textContent = errorMsg;
      if (tabelaCorpo)
        tabelaCorpo.innerHTML = `<tr><td colspan="10" class="text-center text-danger">${errorMsg}</td></tr>`;
    })
    .finally(() => {
      toggleLoading(false);
    });
}

const MAP_CLASSIFICACAO = {
  reposicao: "Reposição",
  devolucao: "Devolução Cliente",
  venda: "Venda",
  roubo: "Roubo",
  dano: "Dano / Avaria",
  devolucao_fornecedor: "Devol. Fornecedor",
  descarte: "Descarte",
  outro: "Outro Motivo",
};

function montarTabelaMovimentacoes(movimentacoes) {
  const tabelaCorpo = document.getElementById("movimentacoes-tabela-corpo");
  if (!tabelaCorpo) return;
  tabelaCorpo.innerHTML = "";

  if (movimentacoes.length === 0) {
    tabelaCorpo.innerHTML =
      '<tr><td colspan="10" class="text-center">Nenhuma movimentação encontrada.</td></tr>';
    return;
  }

  movimentacoes.forEach((mov) => {
    const tr = document.createElement("tr");
    const classificacaoFmt =
      MAP_CLASSIFICACAO[mov.classificacao] || mov.classificacao || "-";
    tr.innerHTML = `
            <td>${mov.id}</td>
            <td>
                ${mov.produto ? `${mov.produto.nome || "N/A"} <small class="text-muted d-block">(${mov.produto.codigo || "S/Cód."})</small>` : "Produto não encontrado"}
            </td>
            <td><span class="badge bg-${getBadgeClassForTipo(mov.tipo)}">${mov.tipo.charAt(0).toUpperCase() + mov.tipo.slice(1)}</span></td>
            <td><span class="badge bg-secondary">${classificacaoFmt}</span></td>
            <td>${mov.quantidade}</td>
            <td>${mov.estoque_anterior !== null ? mov.estoque_anterior : "N/A"}</td>
            <td>${mov.estoque_atual !== null ? mov.estoque_atual : "N/A"}</td>
            <td>${mov.data || "N/A"}</td>
            <td>${mov.usuario ? mov.usuario.nome || "Sistema" : "Sistema"}</td>
        `;

    const tdObs = document.createElement("td");
    if (mov.observacao) {
      tdObs.innerHTML = `
                <div class="d-flex align-items-center gap-1">
                    <span class="text-truncate" style="max-width: 150px;">${mov.observacao}</span>
                    <button class="btn btn-xs btn-outline-primary py-0 px-1 btn-ver-obs" style="font-size: 0.75rem;" title="Ver Observação Completa">
                        <i class="fas fa-eye"></i>
                    </button>
                </div>
            `;
      tdObs.querySelector(".btn-ver-obs").addEventListener("click", () => {
        mostrarPopupObservacao(mov.observacao);
      });
    } else {
      tdObs.textContent = "-";
    }
    tr.appendChild(tdObs);

    tabelaCorpo.appendChild(tr);
  });
}

function getBadgeClassForTipo(tipo) {
  switch (tipo) {
    case "entrada":
      return "success";
    case "saida":
      return "danger";
    case "ajuste":
      return "info";
    case "venda":
      return "warning";
    default:
      return "secondary";
  }
}

function montarPaginacaoMovimentacoes(
  totalItems,
  totalPages,
  currentPage,
  itemsPerPage,
) {
  const paginacaoLista = document.getElementById(
    "paginacao-movimentacoes-lista",
  );
  const paginacaoNav = document.getElementById("paginacao-movimentacoes-nav");

  if (!paginacaoLista || !paginacaoNav) return;
  paginacaoLista.innerHTML = "";

  if (totalPages <= 1) {
    paginacaoNav.style.display = "none";
    return;
  }
  paginacaoNav.style.display = "block";

  const prevLi = document.createElement("li");
  prevLi.className = `page-item ${currentPage === 1 ? "disabled" : ""}`;
  prevLi.innerHTML = `<a class="page-link" href="#" data-page="${currentPage - 1}">Anterior</a>`;
  if (currentPage > 1) {
    prevLi.querySelector("a").addEventListener("click", (e) => {
      e.preventDefault();
      carregarMovimentacoes(currentPage - 1, getCurrentFiltersMov());
    });
  }
  paginacaoLista.appendChild(prevLi);

  let inicio = Math.max(1, currentPage - 2);
  let fim = Math.min(totalPages, currentPage + 2);

  if (currentPage <= 3) {
    fim = Math.min(totalPages, 5);
  }
  if (currentPage >= totalPages - 2) {
    inicio = Math.max(1, totalPages - 4);
  }

  for (let i = inicio; i <= fim; i++) {
    const li = document.createElement("li");
    li.className = `page-item ${i === currentPage ? "active" : ""}`;
    li.innerHTML = `<a class="page-link" href="#" data-page="${i}">${i}</a>`;
    if (i !== currentPage) {
      li.querySelector("a").addEventListener("click", (e) => {
        e.preventDefault();
        carregarMovimentacoes(i, getCurrentFiltersMov());
      });
    }
    paginacaoLista.appendChild(li);
  }

  const nextLi = document.createElement("li");
  nextLi.className = `page-item ${currentPage === totalPages ? "disabled" : ""}`;
  nextLi.innerHTML = `<a class="page-link" href="#" data-page="${currentPage + 1}">Próximo</a>`;
  if (currentPage < totalPages) {
    nextLi.querySelector("a").addEventListener("click", (e) => {
      e.preventDefault();
      carregarMovimentacoes(currentPage + 1, getCurrentFiltersMov());
    });
  }
  paginacaoLista.appendChild(nextLi);
}

function configurarFiltrosMovimentacoes() {
  const formFiltros = document.getElementById("filtros-movimentacoes-form");
  const btnLimparFiltros = document.getElementById("limpar-filtros");

  if (formFiltros) {
    formFiltros.addEventListener("submit", (event) => {
      event.preventDefault();
      carregarMovimentacoes(1, getCurrentFiltersMov());
    });
  }

  if (btnLimparFiltros) {
    btnLimparFiltros.addEventListener("click", () => {
      if (formFiltros) formFiltros.reset();
      carregarMovimentacoes(1, {});
    });
  }
}

function getCurrentFiltersMov() {
  const filtros = {};
  const classificacaoSelect = document.getElementById("filtro-classificacao");
  const dataInicioInput = document.getElementById("filtro-data-inicio");
  const dataFimInput = document.getElementById("filtro-data-fim");

  if (classificacaoSelect && classificacaoSelect.value) {
    filtros.classificacao = classificacaoSelect.value;
  }
  if (dataInicioInput && dataInicioInput.value) {
    filtros.data_inicio = dataInicioInput.value;
  }
  if (dataFimInput && dataFimInput.value) {
    filtros.data_fim = dataFimInput.value;
  }
  return filtros;
}

function mostrarPopupObservacao(texto) {
  const modalEl = document.getElementById("modalObservacao");
  const textoEl = document.getElementById("textoObservacao");
  if (modalEl && textoEl) {
    textoEl.textContent = texto;
    const modal = new bootstrap.Modal(modalEl);
    modal.show();
  }
}
