// Configuração global do Axios (se aplicável a toda a aplicação)
axios.defaults.headers.post['Content-Type'] = 'application/json';
// Adicionar token CSRF se estiver usando Flask-WTF com AJAX
// axios.defaults.headers.common['X-CSRFToken'] = '{{ csrf_token() }}'; // Isso precisa ser setado no template HTML

/**
 * Inicialização Geral da Aplicação
 * Chamado em todas as páginas que incluem app.js
 */
document.addEventListener('DOMContentLoaded', function() {
    // Configuração do gerenciamento de tema (escuro/claro)
    setupThemeManager();

    // Outras inicializações globais podem ir aqui
    // Ex: configurar tooltips do Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // REMOVER qualquer chamada a configurarSidebar() daqui
});

/**
 * Configura o gerenciamento de tema (escuro/claro)
 */
function setupThemeManager() {
    const themeToggle = document.getElementById('theme-toggle');
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');

    // Função interna para aplicar o tema e atualizar o ícone
    const applyTheme = (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        updateThemeToggleIcon(theme);
        // Disparar um evento customizado para que outros scripts (como dashboard.js) possam reagir
        document.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: theme } }));
    };

    // Verificar se há uma preferência salva no localStorage
    const currentTheme = localStorage.getItem('theme');

    if (currentTheme) {
        applyTheme(currentTheme);
    } else {
        // Se não houver preferência salva, usar o padrão do sistema ou 'dark'
        // applyTheme(prefersDarkScheme.matches ? 'dark' : 'light');
        applyTheme('dark'); // Definindo 'dark' como padrão inicial se nada estiver salvo
    }

    // Configurar o evento de clique no botão de alternar tema
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            applyTheme(newTheme);
        });
    }

     // Opcional: Ouvir mudanças no tema do sistema operacional
    // prefersDarkScheme.addEventListener('change', (e) => {
    //     // Só muda se não houver preferência explícita do usuário salva
    //     if (!localStorage.getItem('theme')) {
    //         applyTheme(e.matches ? 'dark' : 'light');
    //     }
    // });
}

/**
 * Atualiza o ícone do botão de alternância de tema
 * @param {string} theme - O tema atual ('dark' ou 'light')
 */
function updateThemeToggleIcon(theme) {
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.innerHTML = ''; // Limpa o conteúdo atual
        const icon = document.createElement('i');
        icon.className = theme === 'light' ? 'fas fa-moon' : 'fas fa-sun'; // Lua para tema claro, Sol para tema escuro
        themeToggle.appendChild(icon);
        themeToggle.title = theme === 'light' ? 'Mudar para tema escuro' : 'Mudar para tema claro';
    }
}

/**
 * Função global para mostrar notificações (pode ser usada por qualquer página)
 * @param {string} message - A mensagem a ser exibida.
 * @param {string} type - O tipo de notificação (success, danger, warning, info). Padrão: 'success'.
 */
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    if (!notification) {
        console.warn('Elemento de notificação #notification não encontrado.');
        return;
    }
    notification.textContent = message;
    // Garante que classes antigas sejam removidas antes de adicionar novas
    notification.className = `alert alert-${type} notification-popup`; // Reinicia as classes
    notification.style.display = 'block';
    notification.style.opacity = 1; // Garante visibilidade

    // Ocultar a notificação após 3 segundos com fade out
    setTimeout(() => {
        notification.style.opacity = 0;
        // Espera a transição de opacidade terminar para esconder o elemento
        setTimeout(() => {
             notification.style.display = 'none';
        }, 300); // Tempo deve corresponder à transição CSS para 'opacity'
    }, 3000);
}


/**
 * Função global para mostrar/ocultar o spinner de carregamento de ações
 * @param {boolean} show - True para mostrar, false para ocultar.
 */
function toggleLoading(show = true) {
    const spinner = document.getElementById('loading-spinner');
     if (!spinner) {
        console.warn('Elemento de loading spinner #loading-spinner não encontrado.');
        return;
    }
    spinner.style.display = show ? 'flex' : 'none';
}


// Adicionar listener para o evento 'themeChanged' para que outros módulos possam reagir
// Exemplo: Atualizar gráficos no dashboard.js quando o tema mudar
document.addEventListener('themeChanged', (event) => {
    const newTheme = event.detail.theme;
    // console.log(`Tema alterado para: ${newTheme}`); // Para debug
    // Chamar funções que precisam se adaptar ao tema, se existirem na página atual
    if (typeof atualizarTemaGraficos === 'function') {
        atualizarTemaGraficos(newTheme);
    }
    // Adicionar outras funções de atualização de UI se necessário
});

// ... (outras funções globais, se houver) ...
