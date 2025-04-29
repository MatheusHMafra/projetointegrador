// Estado do sidebar (se está colapsado ou não no modo desktop)
let sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';

/**
 * Configuração do comportamento do sidebar (toggle e backdrop)
 */
function configurarSidebar() {
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const body = document.body;

    // Aplica o estado inicial (colapsado/expandido) no carregamento da página (apenas desktop)
    if (window.innerWidth >= 992) {
        body.classList.toggle('sidebar-collapsed', sidebarCollapsed);
    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            if (window.innerWidth < 992) {
                // Modo mobile: mostrar/ocultar sidebar com classe 'sidebar-show'
                body.classList.toggle('sidebar-show');

                // Adicionar/remover backdrop
                const existingBackdrop = document.querySelector('.sidebar-backdrop');
                if (body.classList.contains('sidebar-show')) {
                    if (!existingBackdrop) {
                        const backdrop = document.createElement('div');
                        backdrop.classList.add('sidebar-backdrop');
                        backdrop.addEventListener('click', () => {
                            body.classList.remove('sidebar-show');
                            backdrop.remove();
                        });
                        body.appendChild(backdrop);
                    }
                } else {
                    if (existingBackdrop) existingBackdrop.remove();
                }
            } else {
                // Modo desktop: colapsar/expandir sidebar com classe 'sidebar-collapsed'
                sidebarCollapsed = !sidebarCollapsed;
                body.classList.toggle('sidebar-collapsed', sidebarCollapsed);
                // Salva o estado no localStorage
                localStorage.setItem('sidebarCollapsed', sidebarCollapsed);
            }
        });
    }

    // Remove o backdrop se a janela for redimensionada para desktop enquanto o sidebar mobile estiver aberto
    window.addEventListener('resize', () => {
        if (window.innerWidth >= 992) {
            const backdrop = document.querySelector('.sidebar-backdrop');
            if (backdrop) {
                body.classList.remove('sidebar-show');
                backdrop.remove();
            }
            // Garante que a classe de colapso esteja correta no modo desktop
             body.classList.toggle('sidebar-collapsed', sidebarCollapsed);
        } else {
             // Remove a classe de colapso no modo mobile
             body.classList.remove('sidebar-collapsed');
        }
    });
}

// Inicializa a configuração da sidebar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', configurarSidebar);
