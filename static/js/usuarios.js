/**
 * GEP - Gerenciamento de Usuários
 * Script para a página de gerenciamento de usuários.
 */

// Variáveis globais para este script
let currentSearchTermUsuarios = "";
let allUsersData = []; // Para armazenar a lista completa de usuários para filtragem no cliente

document.addEventListener("DOMContentLoaded", () => {
  // window.initialUsersData e window.currentUserInfo são injetados pelo template HTML
  // e devem estar disponíveis aqui.
  carregarUsuarios(); // Carrega os dados (injetados ou via API)
  configurarBuscaUsuarios();
  configurarModaisUsuarios();
});

/**
 * Carrega os usuários.
 * Primeiro tenta usar os dados injetados (window.initialUsersData).
 * Se não disponíveis ou se forceApiCall for true, busca via API.
 * @param {boolean} forceApiCall - Força a busca via API mesmo que dados injetados existam.
 */
function carregarUsuarios(forceApiCall = false) {
  toggleLoading(true); // Mostra o spinner

  const processAndRenderData = (data) => {
    allUsersData = data; // Armazena a lista completa para filtragem
    renderizarTabelaUsuarios(allUsersData); // renderizarTabelaUsuarios aplicará o filtro de busca atual

    // Atualiza a contagem total de usuários (independente do filtro)
    const totalUsuariosElement = document.getElementById("total-usuarios");
    if (totalUsuariosElement) {
      totalUsuariosElement.textContent = `Total: ${allUsersData.length} usuários`;
    }
    toggleLoading(false); // Esconde o spinner
  };

  // Verifica se os dados injetados existem e se não é para forçar a chamada da API
  if (
    !forceApiCall &&
    typeof window.initialUsersData !== "undefined" &&
    window.initialUsersData !== null
  ) {
    console.log("Carregando usuários a partir de dados injetados globalmente.");
    processAndRenderData(window.initialUsersData);
    // Opcional: Limpar os dados injetados após o primeiro uso para garantir que
    // recarregamentos subsequentes (se houver) usem a API para dados frescos.
    // Contudo, para a busca no cliente, é melhor manter allUsersData.
    // window.initialUsersData = null;
  } else {
    console.log("Carregando usuários via API.");
    axios
      .get(API_ROUTES.USUARIOS_LISTAR) // GET /auth/usuarios (deve retornar JSON)
      .then((response) => {
        const usuarios = response.data.usuarios || [];
        processAndRenderData(usuarios);
      })
      .catch((error) => {
        console.error(
          "Erro ao carregar usuários via API:",
          error.response ? error.response.data : error.message
        );
        showNotification("Falha ao carregar lista de usuários.", "danger");
        const tabelaBody = document.getElementById("usuarios-tabela");
        if (tabelaBody) {
          tabelaBody.innerHTML = `<tr><td colspan="7" class="text-center text-danger">Erro ao carregar usuários. Tente novamente.</td></tr>`;
        }
        allUsersData = []; // Limpa dados em caso de erro
        const totalUsuariosElement = document.getElementById("total-usuarios");
        if (totalUsuariosElement) {
          totalUsuariosElement.textContent = `Total: 0 usuários`;
        }
        toggleLoading(false); // Esconde o spinner
      });
  }
}

/**
 * Renderiza a tabela de usuários com base nos dados fornecidos e no termo de busca atual.
 * @param {Array} usuariosParaRenderizar - A lista completa de usuários (geralmente allUsersData).
 */
function renderizarTabelaUsuarios(usuariosParaRenderizar) {
  const tabelaBody = document.getElementById("usuarios-tabela");
  if (!tabelaBody) {
    console.error("Elemento #usuarios-tabela não encontrado no DOM.");
    return;
  }
  tabelaBody.innerHTML = ""; // Limpa a tabela antes de renderizar

  // Aplica o filtro de busca atual aos dados fornecidos
  const termoBuscaNormalizado = currentSearchTermUsuarios.toLowerCase();
  const usuariosFiltrados = termoBuscaNormalizado
    ? usuariosParaRenderizar.filter(
        (user) =>
          (user.nome &&
            user.nome.toLowerCase().includes(termoBuscaNormalizado)) ||
          (user.email &&
            user.email.toLowerCase().includes(termoBuscaNormalizado))
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

      // Função auxiliar para formatar datas
      const formatarData = (dataISO) => {
        if (!dataISO) return "N/A";
        try {
          // As datas do SQLite (CURRENT_TIMESTAMP) são strings 'YYYY-MM-DD HH:MM:SS'
          // O construtor Date() do JS geralmente lida bem com isso.
          return new Date(dataISO).toLocaleString("pt-BR", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          });
        } catch (e) {
          console.warn("Erro ao formatar data:", dataISO, e);
          return dataISO; // Fallback para a string original se a formatação falhar
        }
      };

      const ultimoAcesso = formatarData(usuario.ultimo_acesso);
      const dataCriacao = formatarData(usuario.data_criacao);

      // Desabilitar botão de exclusão para o próprio usuário logado
      // Acessa window.currentUserInfo que foi injetado no HTML
      const disableDelete =
        window.currentUserInfo && usuario.id === window.currentUserInfo.id;

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
                        <button class="btn btn-sm btn-primary me-1" onclick="abrirModalEditarUsuario(${
                          usuario.id
                        })" title="Editar">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" 
                                onclick="confirmarExclusaoUsuarioModal(${
                                  usuario.id
                                }, '${String(usuario.nome || "").replace(
        /'/g,
        "\\'"
      )}')" 
                                title="Excluir" 
                                ${disableDelete ? "disabled" : ""}>
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </td>
                </tr>
            `;
      tabelaBody.innerHTML += row;
    });
  }
  // Atualiza a contagem de usuários exibidos após o filtro
  const totalUsuariosElement = document.getElementById("total-usuarios");
  if (totalUsuariosElement) {
    const totalGeral = usuariosParaRenderizar.length; // Total antes do filtro
    totalUsuariosElement.textContent = `Total: ${totalGeral} usuários (mostrando ${usuariosFiltrados.length})`;
  }
}

/**
 * Configura a funcionalidade de busca de usuários com debounce.
 * A busca agora filtra os dados já carregados em `allUsersData`.
 */
function configurarBuscaUsuarios() {
  const buscaInputEl = document.getElementById("busca-usuario");
  let debounceTimeout;

  if (buscaInputEl) {
    buscaInputEl.addEventListener("input", (e) => {
      clearTimeout(debounceTimeout);
      debounceTimeout = setTimeout(() => {
        currentSearchTermUsuarios = e.target.value.trim().toLowerCase();
        // Re-renderiza a tabela com os dados já armazenados em allUsersData, aplicando o filtro
        renderizarTabelaUsuarios(allUsersData);
      }, 300); // Atraso para não filtrar a cada tecla digitada
    });
  }
}

/**
 * Configura os eventos e a lógica dos modais de usuários (Editar, Excluir).
 */
function configurarModaisUsuarios() {
  // Modal Editar Usuário
  const modalEditarEl = document.getElementById("modalEditarUsuario");
  const formEditarEl = document.getElementById("formEditarUsuario");
  const btnAtualizarUsuarioEl = document.getElementById("btnAtualizarUsuario");

  if (modalEditarEl && formEditarEl && btnAtualizarUsuarioEl) {
    btnAtualizarUsuarioEl.addEventListener("click", () => {
      if (formEditarEl.checkValidity()) {
        // Validação básica do HTML5
        submeterFormularioEditarUsuario();
      } else {
        formEditarEl.reportValidity(); // Mostra erros de validação do HTML5
      }
    });
  }

  // Modal Confirmar Exclusão Usuário
  const btnConfirmarExclusaoEl = document.getElementById(
    "btnConfirmarExclusaoUsuario"
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

/**
 * Abre o modal de edição preenchido com os dados do usuário.
 * @param {number} usuarioId - ID do usuário a ser editado.
 */
function abrirModalEditarUsuario(usuarioId) {
  toggleLoading(true);
  // A API /auth/usuarios/{id} já retorna JSON e é usada para obter os dados mais recentes.
  axios
    .get(API_ROUTES.USUARIO_DETALHES(usuarioId))
    .then((response) => {
      const usuario = response.data.usuario; // A API /auth/usuarios/{id} retorna { usuario: {...} }
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
      document.getElementById("editSenhaUsuario").value = ""; // Limpar campo de senha sempre
      document.getElementById("editSenhaUsuario").placeholder =
        "Deixe em branco para não alterar";

      const modalEl = document.getElementById("modalEditarUsuario");
      if (modalEl) new bootstrap.Modal(modalEl).show();
    })
    .catch((error) => {
      console.error(
        "Erro ao carregar dados do usuário para edição:",
        error.response ? error.response.data : error.message
      );
      showNotification(
        "Falha ao carregar dados do usuário para edição.",
        "danger"
      );
    })
    .finally(() => {
      toggleLoading(false);
    });
}

/**
 * Submete o formulário de edição do usuário.
 */
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
    // Só envia senha se não estiver vazia
    dadosUsuarioAtualizado.senha = novaSenha;
  }

  if (!dadosUsuarioAtualizado.nome || !dadosUsuarioAtualizado.email) {
    showNotification("Nome e Email são obrigatórios.", "warning");
    toggleLoading(false);
    return;
  }

  axios
    .put(API_ROUTES.USUARIO_DETALHES(usuarioId), dadosUsuarioAtualizado) // PUT /auth/usuarios/{id}
    .then((response) => {
      showNotification(
        response.data.message || "Usuário atualizado com sucesso!",
        "success"
      );
      const modalEl = document.getElementById("modalEditarUsuario");
      if (modalEl && bootstrap.Modal.getInstance(modalEl)) {
        // Verifica se o modal existe e está instanciado
        bootstrap.Modal.getInstance(modalEl).hide();
      }
      carregarUsuarios(true); // Força recarregar da API para ter os dados mais recentes
    })
    .catch((error) => {
      console.error(
        "Erro ao atualizar usuário:",
        error.response ? error.response.data : error.message
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

/**
 * Prepara e abre o modal de confirmação de exclusão para usuários.
 * @param {number} usuarioId - ID do usuário a ser excluído.
 * @param {string} nomeUsuario - Nome do usuário.
 */
function confirmarExclusaoUsuarioModal(usuarioId, nomeUsuario) {
  // Verificar se é o usuário logado antes de abrir o modal
  // Acessa window.currentUserInfo que foi injetado no HTML
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

/**
 * Confirma e executa a exclusão do usuário.
 * @param {number} usuarioId - ID do usuário a ser excluído.
 */
function executarExclusaoUsuario(usuarioId) {
  if (!usuarioId) return;

  // Segurança adicional: não permitir exclusão do próprio usuário (já verificado no botão e ao abrir modal)
  // Acessa window.currentUserInfo que foi injetado no HTML
  if (
    window.currentUserInfo &&
    parseInt(usuarioId) === window.currentUserInfo.id
  ) {
    showNotification("Não é permitido excluir o próprio usuário.", "danger");
    const modalConfirmacao = document.getElementById(
      "modalConfirmarExclusaoUsuario"
    );
    if (modalConfirmacao && bootstrap.Modal.getInstance(modalConfirmacao)) {
      bootstrap.Modal.getInstance(modalConfirmacao).hide();
    }
    return;
  }

  toggleLoading(true);
  axios
    .delete(API_ROUTES.USUARIO_DETALHES(usuarioId)) // DELETE /auth/usuarios/{id}
    .then((response) => {
      showNotification(
        response.data.message || "Usuário excluído com sucesso!",
        "success"
      );
      const modalEl = document.getElementById("modalConfirmarExclusaoUsuario");
      if (modalEl && bootstrap.Modal.getInstance(modalEl)) {
        // Verifica se o modal existe e está instanciado
        bootstrap.Modal.getInstance(modalEl).hide();
      }
      carregarUsuarios(true); // Força recarregar da API para ter os dados mais recentes
    })
    .catch((error) => {
      console.error(
        "Erro ao excluir usuário:",
        error.response ? error.response.data : error.message
      );
      const msg = error.response?.data?.error || "Erro ao excluir usuário.";
      showNotification(msg, "danger");
      // Mesmo com erro, fechar o modal de confirmação
      const modalEl = document.getElementById("modalConfirmarExclusaoUsuario");
      if (modalEl && bootstrap.Modal.getInstance(modalEl)) {
        bootstrap.Modal.getInstance(modalEl).hide();
      }
    })
    .finally(() => {
      toggleLoading(false);
    });
}
