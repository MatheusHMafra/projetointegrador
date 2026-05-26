document.addEventListener("DOMContentLoaded", () => {
  inicializarFormRelatorios();
  toggleLoading(false);
});

function inicializarFormRelatorios() {
  const reportTypeSelect = document.getElementById("report-type");
  const form = document.getElementById("relatorio-config-form");

  if (reportTypeSelect) {
    reportTypeSelect.addEventListener("change", (e) => {
      const val = e.target.value;

      document
        .querySelectorAll(".option-field")
        .forEach((el) => (el.style.display = "none"));

      if (val === "vendas") {
        document
          .querySelectorAll(".sales-option")
          .forEach((el) => (el.style.display = "block"));
      } else if (val === "estoque") {
        document
          .querySelectorAll(".stock-option")
          .forEach((el) => (el.style.display = "block"));
      } else if (val === "fornecedores") {
        document
          .querySelectorAll(".supplier-option")
          .forEach((el) => (el.style.display = "block"));
      }
    });
  }

  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      gerarRelatorio();
    });
  }
}

function gerarRelatorio() {
  const reportType = document.getElementById("report-type").value;
  if (!reportType) return;

  toggleLoading(true);

  const dateStr = new Date().toLocaleString("pt-BR");
  document.getElementById("print-report-date").textContent = dateStr;

  if (reportType === "vendas") {
    const limit = document.getElementById("sales-limit").value;
    axios
      .get("/relatorios/vendas/produtos", { params: { limit } })
      .then((response) => {
        const data = response.data;
        renderizarRelatorioVendas(data);
      })
      .catch((error) => {
        console.error("Erro ao gerar relatório de vendas:", error);
        showNotification("Falha ao gerar relatório de vendas.", "danger");
      })
      .finally(() => {
        toggleLoading(false);
      });
  } else if (reportType === "estoque") {
    const status = document.getElementById("stock-status").value;
    axios
      .get("/relatorios/estoque/niveis", { params: { status, per_page: 500 } })
      .then((response) => {
        const data = response.data;
        renderizarRelatorioEstoque(data, status);
      })
      .catch((error) => {
        console.error("Erro ao gerar relatório de estoque:", error);
        showNotification("Falha ao gerar relatório de estoque.", "danger");
      })
      .finally(() => {
        toggleLoading(false);
      });
  } else if (reportType === "fornecedores") {
    const status = document.getElementById("supplier-status").value;
    axios
      .get("/relatorios/fornecedores/resumo", {
        params: { status, per_page: 500 },
      })
      .then((response) => {
        const data = response.data;
        renderizarRelatorioFornecedores(data, status);
      })
      .catch((error) => {
        console.error("Erro ao gerar relatório de fornecedores:", error);
        showNotification("Falha ao gerar relatório de fornecedores.", "danger");
      })
      .finally(() => {
        toggleLoading(false);
      });
  } else if (reportType === "fornecedores_produtos") {
    axios
      .get("/relatorios/fornecedores/produtos")
      .then((response) => {
        const data = response.data;
        renderizarRelatorioProdutosPorFornecedor(data);
      })
      .catch((error) => {
        console.error(
          "Erro ao gerar relatório de produtos por fornecedor:",
          error,
        );
        showNotification(
          "Falha ao gerar relatório de produtos por fornecedor.",
          "danger",
        );
      })
      .finally(() => {
        toggleLoading(false);
      });
  } else if (reportType === "vendas_operadores") {
    axios
      .get("/relatorios/vendas/operadores")
      .then((response) => {
        const data = response.data;
        renderizarRelatorioVendasPorOperador(data);
      })
      .catch((error) => {
        console.error("Erro ao gerar relatório de vendas por operador:", error);
        showNotification(
          "Falha ao gerar relatório de vendas por operador.",
          "danger",
        );
      })
      .finally(() => {
        toggleLoading(false);
      });
  }
}

function renderizarRelatorioVendas(data) {
  const outputCard = document.getElementById("report-output-card");
  const container = document.getElementById("report-content");
  const printTitle = document.getElementById("print-report-title");

  printTitle.textContent = "Relatório de Vendas de Produtos";
  container.innerHTML = "";

  let html = `
        <h4 class="mb-3 text-success border-bottom pb-2 mt-2"><i class="fas fa-chart-line me-2"></i>Produtos Mais Vendidos</h4>
        <div class="table-responsive mb-5">
            <table class="table table-bordered table-striped">
                <thead>
                    <tr>
                        <th>Código</th>
                        <th>Produto</th>
                        <th>Categoria</th>
                        <th class="text-center">Quantidade Vendida</th>
                        <th class="text-center">Estoque Atual</th>
                    </tr>
                </thead>
                <tbody>
    `;

  const maisVendidos = data.mais_vendidos || [];
  if (maisVendidos.length === 0) {
    html += `<tr><td colspan="5" class="text-center text-muted">Nenhum produto vendido no período.</td></tr>`;
  } else {
    maisVendidos.forEach((item) => {
      html += `
                <tr>
                    <td>${item.produto_codigo || "-"}</td>
                    <td>${item.produto_nome}</td>
                    <td>${item.categoria_nome || "Sem categoria"}</td>
                    <td class="text-center fw-bold text-success">${item.total_vendido}</td>
                    <td class="text-center">${item.estoque_atual}</td>
                </tr>
            `;
    });
  }
  html += `</tbody></table></div>`;

  html += `
        <h4 class="mb-3 text-warning border-bottom pb-2"><i class="fas fa-chart-bar me-2"></i>Produtos Menos Vendidos (Dentre os que tiveram vendas)</h4>
        <div class="table-responsive mb-5">
            <table class="table table-bordered table-striped">
                <thead>
                    <tr>
                        <th>Código</th>
                        <th>Produto</th>
                        <th>Categoria</th>
                        <th class="text-center">Quantidade Vendida</th>
                        <th class="text-center">Estoque Atual</th>
                    </tr>
                </thead>
                <tbody>
    `;

  const menosVendidos = data.menos_vendidos_com_venda || [];
  if (menosVendidos.length === 0) {
    html += `<tr><td colspan="5" class="text-center text-muted">Nenhum produto com vendas registrado.</td></tr>`;
  } else {
    menosVendidos.forEach((item) => {
      html += `
                <tr>
                    <td>${item.produto_codigo || "-"}</td>
                    <td>${item.produto_nome}</td>
                    <td>${item.categoria_nome || "Sem categoria"}</td>
                    <td class="text-center fw-bold text-warning">${item.total_vendido}</td>
                    <td class="text-center">${item.estoque_atual}</td>
                </tr>
            `;
    });
  }
  html += `</tbody></table></div>`;

  html += `
        <h4 class="mb-3 text-danger border-bottom pb-2"><i class="fas fa-exclamation-circle me-2"></i>Produtos Sem Vendas</h4>
        <div class="table-responsive">
            <table class="table table-bordered table-striped">
                <thead>
                    <tr>
                        <th>Código</th>
                        <th>Produto</th>
                        <th>Categoria</th>
                        <th class="text-center">Quantidade Vendida</th>
                        <th class="text-center">Estoque Atual</th>
                    </tr>
                </thead>
                <tbody>
    `;

  const naoVendidos = data.nao_vendidos || [];
  if (naoVendidos.length === 0) {
    html += `<tr><td colspan="5" class="text-center text-muted">Todos os produtos ativos tiveram vendas.</td></tr>`;
  } else {
    naoVendidos.forEach((item) => {
      html += `
                <tr>
                    <td>${item.produto_codigo || "-"}</td>
                    <td>${item.produto_nome}</td>
                    <td>${item.categoria_nome || "Sem categoria"}</td>
                    <td class="text-center text-danger">0</td>
                    <td class="text-center">${item.estoque_atual}</td>
                </tr>
            `;
    });
  }
  html += `</tbody></table></div>`;

  container.innerHTML = html;
  outputCard.style.display = "block";
}

function renderizarRelatorioEstoque(data, statusFiltro) {
  const outputCard = document.getElementById("report-output-card");
  const container = document.getElementById("report-content");
  const printTitle = document.getElementById("print-report-title");

  let statusLabel = "Todos";
  if (statusFiltro === "baixo") statusLabel = "Apenas Estoque Baixo";
  else if (statusFiltro === "ok") statusLabel = "Apenas Estoque Adequado";
  else if (statusFiltro === "excesso") statusLabel = "Apenas Estoque Excessivo";

  printTitle.textContent = `Relatório de Níveis de Estoque (${statusLabel})`;
  container.innerHTML = "";

  let html = `
        <div class="table-responsive">
            <table class="table table-bordered table-striped mb-0">
                <thead>
                    <tr>
                        <th>Código</th>
                        <th>Produto</th>
                        <th>Categoria</th>
                        <th>Fornecedor</th>
                        <th class="text-center">Mínimo</th>
                        <th class="text-center">Atual</th>
                        <th class="text-center">Status</th>
                    </tr>
                </thead>
                <tbody>
    `;

  const produtos = data.produtos_niveis_estoque || [];
  if (produtos.length === 0) {
    html += `<tr><td colspan="7" class="text-center text-muted">Nenhum produto encontrado com os filtros atuais.</td></tr>`;
  } else {
    produtos.forEach((item) => {
      let statusBadge = "";
      if (item.status_estoque === "baixo") {
        statusBadge = '<span class="badge bg-danger">Baixo</span>';
      } else if (item.status_estoque === "ok") {
        statusBadge = '<span class="badge bg-success">Adequado</span>';
      } else {
        statusBadge = '<span class="badge bg-info">Excesso</span>';
      }

      html += `
                <tr>
                    <td>${item.codigo || "-"}</td>
                    <td>${item.nome}</td>
                    <td>${item.categoria_nome || "N/A"}</td>
                    <td>${item.fornecedor_nome || "N/A"}</td>
                    <td class="text-center">${item.estoque_minimo}</td>
                    <td class="text-center fw-bold">${item.estoque}</td>
                    <td class="text-center">${statusBadge}</td>
                </tr>
            `;
    });
  }
  html += `</tbody></table></div>`;

  container.innerHTML = html;
  outputCard.style.display = "block";
}

function renderizarRelatorioFornecedores(data, statusFiltro) {
  const outputCard = document.getElementById("report-output-card");
  const container = document.getElementById("report-content");
  const printTitle = document.getElementById("print-report-title");

  let statusLabel = "Todos";
  if (statusFiltro === "ativos") statusLabel = "Apenas Ativos";
  else if (statusFiltro === "inativos") statusLabel = "Apenas Inativos";

  printTitle.textContent = `Relatório de Resumo de Fornecedores (${statusLabel})`;
  container.innerHTML = "";

  let html = `
        <div class="table-responsive">
            <table class="table table-bordered table-striped mb-0">
                <thead>
                    <tr>
                        <th>Fornecedor</th>
                        <th>CNPJ</th>
                        <th>Telefone / E-mail</th>
                        <th class="text-center">Total Produtos</th>
                        <th class="text-center">Total Estoque</th>
                        <th class="text-end">Valor Total em Estoque</th>
                        <th class="text-center">Status</th>
                    </tr>
                </thead>
                <tbody>
    `;

  const fornecedores = data.fornecedores_resumo || [];
  if (fornecedores.length === 0) {
    html += `<tr><td colspan="7" class="text-center text-muted">Nenhum fornecedor encontrado com os filtros atuais.</td></tr>`;
  } else {
    fornecedores.forEach((item) => {
      const statusBadge = item.ativo
        ? '<span class="badge bg-success">Ativo</span>'
        : '<span class="badge bg-danger">Inativo</span>';
      const valorEstoqueFmt = `R$ ${parseFloat(item.valor_total_estoque || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      const contatoInfo =
        [item.telefone, item.email].filter(Boolean).join(" / ") || "-";

      html += `
                <tr>
                    <td class="fw-bold">${item.fornecedor_nome}</td>
                    <td>${item.cnpj || "-"}</td>
                    <td>${contatoInfo}</td>
                    <td class="text-center">${item.total_produtos}</td>
                    <td class="text-center">${item.total_estoque}</td>
                    <td class="text-end fw-bold">${valorEstoqueFmt}</td>
                    <td class="text-center">${statusBadge}</td>
                </tr>
            `;
    });
  }
  html += `</tbody></table></div>`;

  container.innerHTML = html;
  outputCard.style.display = "block";
}

function imprimirRelatorio() {
  window.print();
}

function renderizarRelatorioProdutosPorFornecedor(data) {
  const outputCard = document.getElementById("report-output-card");
  const container = document.getElementById("report-content");
  const printTitle = document.getElementById("print-report-title");

  printTitle.textContent = "Relatório de Produtos por Fornecedor";
  container.innerHTML = "";

  if (data.length === 0) {
    container.innerHTML =
      '<div class="alert alert-info text-center">Nenhum fornecedor ou produto encontrado.</div>';
    outputCard.style.display = "block";
    return;
  }

  let html = "";
  data.forEach((forn) => {
    html += `
            <div class="mb-4">
                <h5 class="text-primary border-bottom pb-2 mt-3">
                    <i class="fas fa-truck me-2"></i>${forn.nome}
                    <small class="text-muted fs-6 ms-2">(CNPJ: ${forn.cnpj || "-"})</small>
                </h5>
                <div class="table-responsive">
                    <table class="table table-bordered table-striped">
                        <thead>
                            <tr>
                                <th>Código</th>
                                <th>Produto</th>
                                <th class="text-end">Preço Compra</th>
                                <th class="text-end">Preço Venda</th>
                                <th class="text-center">Estoque</th>
                                <th class="text-center">Status</th>
                            </tr>
                        </thead>
                        <tbody>
        `;

    if (forn.produtos.length === 0) {
      html += `<tr><td colspan="6" class="text-center text-muted">Nenhum produto cadastrado para este fornecedor.</td></tr>`;
    } else {
      forn.produtos.forEach((prod) => {
        const statusBadge = prod.ativo
          ? '<span class="badge bg-success">Ativo</span>'
          : '<span class="badge bg-danger">Inativo</span>';
        const precoCompraFmt = prod.preco_compra
          ? `R$ ${parseFloat(prod.preco_compra).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
          : "-";
        const precoVendaFmt = prod.preco
          ? `R$ ${parseFloat(prod.preco).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
          : "-";
        html += `
                    <tr>
                        <td>${prod.codigo || "-"}</td>
                        <td class="fw-bold">${prod.nome}</td>
                        <td class="text-end">${precoCompraFmt}</td>
                        <td class="text-end">${precoVendaFmt}</td>
                        <td class="text-center">${prod.estoque}</td>
                        <td class="text-center">${statusBadge}</td>
                    </tr>
                `;
      });
    }

    html += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;
  });

  container.innerHTML = html;
  outputCard.style.display = "block";
}

function renderizarRelatorioVendasPorOperador(data) {
  const outputCard = document.getElementById("report-output-card");
  const container = document.getElementById("report-content");
  const printTitle = document.getElementById("print-report-title");

  printTitle.textContent = "Relatório de Vendas por Operador";
  container.innerHTML = "";

  let html = `
        <div class="table-responsive mt-3">
            <table class="table table-bordered table-striped">
                <thead>
                    <tr>
                        <th>Operador</th>
                        <th>Nível de Acesso</th>
                        <th class="text-center">Itens Vendidos</th>
                        <th class="text-center">Itens Devolvidos</th>
                        <th class="text-end">Receita Líquida</th>
                    </tr>
                </thead>
                <tbody>
    `;

  if (data.length === 0) {
    html += `<tr><td colspan="5" class="text-center text-muted">Nenhuma venda registrada para os operadores.</td></tr>`;
  } else {
    data.forEach((item) => {
      const receitaFmt = `R$ ${parseFloat(item.receita_total || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      const nivelFmt = item.usuario_nivel
        ? item.usuario_nivel.toUpperCase()
        : "-";
      html += `
                <tr>
                    <td class="fw-bold">${item.usuario_nome} <small class="text-muted d-block">${item.usuario_email}</small></td>
                    <td>${nivelFmt}</td>
                    <td class="text-center text-success fw-bold">${item.total_itens_vendidos || 0}</td>
                    <td class="text-center text-danger">${item.total_itens_devolvidos || 0}</td>
                    <td class="text-end fw-bold">${receitaFmt}</td>
                </tr>
            `;
    });
  }

  html += `</tbody></table></div>`;

  container.innerHTML = html;
  outputCard.style.display = "block";
}
