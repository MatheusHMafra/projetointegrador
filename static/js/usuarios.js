let currentSearchTermUsuarios = "";
let allUsersData = [];

document.addEventListener("DOMContentLoaded", () => {
  carregarUsuarios();
  configurarBuscaUsuarios();
  configurarModaisUsuarios();
});

function carregarUsuarios(forceApiCall = false) {
  toggleLoading(true);

  const processAndRenderData = (data) => {
    allUsersData = data;
    renderizarTabelaUsuarios(allUsersData);

    const totalUsuariosElement = document.getElementById("total-usuarios");
    if (totalUsuariosElement) {
      totalUsuariosElement.textContent = `Total: ${allUsersData.length} usuários`;
    }
    toggleLoading(false);
  };

  if (
    !forceApiCall &&
    typeof window.initialUsersData !== "undefined" &&
    window.initialUsersData !== null
  ) {
    console.log("Carregando usuários a partir de dados injetados globalmente.");
    processAndRenderData(window.initialUsersData);
  } else {
    console.log("Carregando usuários via API.");
    axios
      .get(API_ROUTES.USUARIOS_LISTAR)
      .then((response) => {
        const usuarios = response.data.usuarios || [];
        processAndRenderData(usuarios);
      })
      .catch((error) => {
        console.error(
          "Erro ao carregar usuários via API:",
          error.response ? error.response.data : error.message,
        );
        showNotification("Falha ao carregar lista de usuários.", "danger");
        const tabelaBody = document.getElementById("usuarios-tabela");
        if (tabelaBody) {
          tabelaBody.innerHTML = `<tr><td colspan="7" class="text-center text-danger">Erro ao carregar usuários. Tente novamente.</td></tr>`;
        }
        allUsersData = [];
        const totalUsuariosElement = document.getElementById("total-usuarios");
        if (totalUsuariosElement) {
          totalUsuariosElement.textContent = `Total: 0 usuários`;
        }
        toggleLoading(false);
      });
  }
}

function renderizarTabelaUsuarios(usuariosParaRenderizar) {
  const tabelaBody = document.getElementById("usuarios-tabela");
  if (!tabelaBody) {
    console.error("Elemento #usuarios-tabela não encontrado no DOM.");
    return;
  }
  tabelaBody.innerHTML = "";

  const termoBuscaNormalizado = currentSearchTermUsuarios.toLowerCase();
  const usuariosFiltrados = termoBuscaNormalizado
    ? usuariosParaRenderizar.filter(
        (user) =>
          (user.nome &&
            user.nome.toLowerCase().includes(termoBuscaNormalizado)) ||
          (user.email &&
            user.email.toLowerCase().includes(termoBuscaNormalizado)),
      )
    : usuariosParaRenderizar;

  if (usuariosFiltrados.length === 0) {
    const mensagem = currentSearchTermUsuarios
      ? `Nenhum usuário encontrado para "${currentSearchTermUsuarios}".`
      : "Nenhum usuário cadastrado.";
    tabelaBody.innerHTML = `<tr><td colspan="7" class="text-center">${mensagem}</td></tr>`;
  } else {
    usuariosFiltrados.forEach((usuario) => {
      const statusClass = usuario.ativo ? "success" : "secondary";
      const statusText = usuario.ativo ? "Ativo" : "Inativo";

      const formatarData = (dataISO) => {
        if (!dataISO) return "N/A";
        try {
          return new Date(dataISO).toLocaleString("pt-BR", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          });
        } catch (e) {
          console.warn("Erro ao formatar data:", dataISO, e);
          return dataISO;
        }
      };

      const ultimoAcesso = formatarData(usuario.ultimo_acesso);
      const dataCriacao = formatarData(usuario.data_criacao);

      const disableDelete =
        window.currentUserInfo &&
        Number(usuario.id) === Number(window.currentUserInfo.id);

      const row = `
                <tr>
                    <td>${usuario.nome || "N/A"}</td>
                    <td>${usuario.email || "N/A"}</td>
                    <td>${
                      usuario.nivel_acesso
                        ? usuario.nivel_acesso.charAt(0).toUpperCase() +
                          usuario.nivel_acesso.slice(1)
                        : "N/A"
                    }</td>
                    <td><span class="badge bg-${statusClass}">${statusText}</span></td>
                    <td>${dataCriacao}</td>
                    <td>${ultimoAcesso}</td>
                    <td class="text-end">
                      <div class="dropdown d-inline-block">
                        <button class="btn btn-sm btn-outline-secondary table-actions-toggle" type="button" data-bs-toggle="dropdown" data-bs-boundary="viewport" aria-expanded="false" title="Mais ações">
                          <i class="fas fa-ellipsis-v"></i>
                        </button>
                        <ul class="dropdown-menu dropdown-menu-end">
                          <li>
                            <button class="dropdown-item" type="button" onclick="abrirModalEditarUsuario(${usuario.id})">
                              <i class="fas fa-edit me-2"></i>Editar
                            </button>
                          </li>
                          <li><hr class="dropdown-divider"></li>
                          <li>
                            <button class="dropdown-item text-danger" type="button"
                              onclick="confirmarExclusaoUsuarioModal(${usuario.id}, '${String(usuario.nome || "").replace(/'/g, "\\'")}')"
                              ${disableDelete ? "disabled" : ""}>
                              <i class="fas fa-trash-alt me-2"></i>Excluir
                            </button>
                          </li>
                        </ul>
                      </div>
                    </td>
                </tr>
            `;
      tabelaBody.innerHTML += row;
    });
  }

  const totalUsuariosElement = document.getElementById("total-usuarios");
  if (totalUsuariosElement) {
    const totalGeral = usuariosParaRenderizar.length;
    const totalAtivos = usuariosParaRenderizar.filter((u) => u.ativo).length;
    const totalInativos = totalGeral - totalAtivos;
    totalUsuariosElement.textContent = `Total: ${totalGeral} usuários | Ativos: ${totalAtivos} | Inativos: ${totalInativos} (mostrando ${usuariosFiltrados.length})`;
  }
  inicializarDropdownsTabela();
}

function configurarBuscaUsuarios() {
  const buscaInputEl = document.getElementById("busca-usuario");
  let debounceTimeout;

  if (buscaInputEl) {
    buscaInputEl.addEventListener("input", (e) => {
      clearTimeout(debounceTimeout);
      debounceTimeout = setTimeout(() => {
        currentSearchTermUsuarios = e.target.value.trim().toLowerCase();

        renderizarTabelaUsuarios(allUsersData);
      }, 300);
    });
  }
}

function configurarModaisUsuarios() {
  const modalEditarEl = document.getElementById("modalEditarUsuario");
  const formEditarEl = document.getElementById("formEditarUsuario");
  const btnAtualizarUsuarioEl = document.getElementById("btnAtualizarUsuario");

  if (modalEditarEl && formEditarEl && btnAtualizarUsuarioEl) {
    btnAtualizarUsuarioEl.addEventListener("click", () => {
      if (formEditarEl.checkValidity()) {
        submeterFormularioEditarUsuario();
      } else {
        formEditarEl.reportValidity();
      }
    });
  }

  const btnConfirmarExclusaoEl = document.getElementById(
    "btnConfirmarExclusaoUsuario",
  );
  if (btnConfirmarExclusaoEl) {
    btnConfirmarExclusaoEl.addEventListener("click", () => {
      const usuarioId = btnConfirmarExclusaoEl.dataset.usuarioId;
      if (usuarioId) {
        executarExclusaoUsuario(usuarioId);
      }
    });
  }
}

function abrirModalEditarUsuario(usuarioId) {
  toggleLoading(true);

  axios
    .get(API_ROUTES.USUARIO_DETALHES(usuarioId))
    .then((response) => {
      const usuario = response.data.usuario;
      if (!usuario) {
        showNotification("Usuário não encontrado para edição.", "warning");
        toggleLoading(false);
        return;
      }
      document.getElementById("editUsuarioId").value = usuario.id;
      document.getElementById("editNomeUsuario").value = usuario.nome || "";
      document.getElementById("editEmailUsuario").value = usuario.email || "";
      document.getElementById("editNivelAcessoUsuario").value =
        usuario.nivel_acesso || "operador";
      document.getElementById("editAtivoUsuario").checked = usuario.ativo;
      document.getElementById("editSenhaUsuario").value = "";
      document.getElementById("editSenhaUsuario").placeholder =
        "Deixe em branco para não alterar";

      const modalEl = document.getElementById("modalEditarUsuario");
      if (modalEl) new bootstrap.Modal(modalEl).show();
    })
    .catch((error) => {
      console.error(
        "Erro ao carregar dados do usuário para edição:",
        error.response ? error.response.data : error.message,
      );
      showNotification(
        "Falha ao carregar dados do usuário para edição.",
        "danger",
      );
    })
    .finally(() => {
      toggleLoading(false);
    });
}

function submeterFormularioEditarUsuario() {
  const usuarioId = document.getElementById("editUsuarioId").value;
  if (!usuarioId) {
    showNotification("ID do usuário para edição não encontrado.", "danger");
    return;
  }
  toggleLoading(true);

  const dadosUsuarioAtualizado = {
    nome: document.getElementById("editNomeUsuario").value.trim(),
    email: document.getElementById("editEmailUsuario").value.trim(),
    nivel_acesso: document.getElementById("editNivelAcessoUsuario").value,
    ativo: document.getElementById("editAtivoUsuario").checked,
  };

  const novaSenha = document.getElementById("editSenhaUsuario").value;
  if (novaSenha && novaSenha.trim() !== "") {
    dadosUsuarioAtualizado.senha = novaSenha;
  }

  if (!dadosUsuarioAtualizado.nome || !dadosUsuarioAtualizado.email) {
    showNotification("Nome e Email são obrigatórios.", "warning");
    toggleLoading(false);
    return;
  }

  axios
    .put(API_ROUTES.USUARIO_DETALHES(usuarioId), dadosUsuarioAtualizado)
    .then((response) => {
      showNotification(
        response.data.message || "Usuário atualizado com sucesso!",
        "success",
      );
      const modalEl = document.getElementById("modalEditarUsuario");
      if (modalEl) {
        const modal =
          bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
        modal.hide();
      }
      carregarUsuarios(true);
    })
    .catch((error) => {
      console.error(
        "Erro ao atualizar usuário:",
        error.response ? error.response.data : error.message,
      );
      const msg =
        error.response?.data?.error ||
        "Erro desconhecido ao atualizar usuário.";
      showNotification(msg, "danger");
    })
    .finally(() => {
      toggleLoading(false);
    });
}

function confirmarExclusaoUsuarioModal(usuarioId, nomeUsuario) {
  if (window.currentUserInfo && usuarioId === window.currentUserInfo.id) {
    showNotification("Você não pode excluir seu próprio usuário.", "warning");
    return;
  }
  document.getElementById("nomeUsuarioExcluir").textContent = nomeUsuario;
  document.getElementById("btnConfirmarExclusaoUsuario").dataset.usuarioId =
    usuarioId;

  const modalEl = document.getElementById("modalConfirmarExclusaoUsuario");
  if (modalEl) new bootstrap.Modal(modalEl).show();
}

function executarExclusaoUsuario(usuarioId) {
  if (!usuarioId) return;

  if (
    window.currentUserInfo &&
    parseInt(usuarioId) === window.currentUserInfo.id
  ) {
    showNotification("Não é permitido excluir o próprio usuário.", "danger");
    const modalConfirmacao = document.getElementById(
      "modalConfirmarExclusaoUsuario",
    );
    if (modalConfirmacao && bootstrap.Modal.getInstance(modalConfirmacao)) {
      bootstrap.Modal.getInstance(modalConfirmacao).hide();
    }
    return;
  }

  toggleLoading(true);
  axios
    .delete(API_ROUTES.USUARIO_DETALHES(usuarioId))
    .then((response) => {
      showNotification(
        response.data.message || "Usuário excluído com sucesso!",
        "success",
      );
      const modalEl = document.getElementById("modalConfirmarExclusaoUsuario");
      if (modalEl) {
        const modal =
          bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
        modal.hide();
      }
      carregarUsuarios(true);
    })
    .catch((error) => {
      console.error(
        "Erro ao excluir usuário:",
        error.response ? error.response.data : error.message,
      );
      const msg = error.response?.data?.error || "Erro ao excluir usuário.";
      showNotification(msg, "danger");

      const modalEl = document.getElementById("modalConfirmarExclusaoUsuario");
      if (modalEl) {
        const modal =
          bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
        modal.hide();
      }
    })
    .finally(() => {
      toggleLoading(false);
    });
}
