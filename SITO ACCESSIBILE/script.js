document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    // === GESTIONE TEMA ===
    const themeToggle = document.getElementById('theme-toggle');
    
    // Imposta sempre il tema chiaro di default (ignorando le preferenze di sistema)
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    // Applica il tema chiaro
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeToggleText(currentTheme);

    // Gestione click sul toggle del tema
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeToggleText(newTheme);
            
            // Annuncia il cambio tema per screen reader
            announceToScreenReader(`Tema cambiato a modalità ${newTheme === 'dark' ? 'scura' : 'chiara'}`);
        });

        // Supporto tastiera per il toggle del tema
        themeToggle.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });
    }

    // Aggiorna il testo del toggle del tema
    function updateThemeToggleText(theme) {
        if (themeToggle) {
            const themeText = themeToggle.querySelector('.theme-text');
            if (themeText) {
                // Inverti il testo: se tema chiaro -> "Tema Scuro", se tema scuro -> "Tema Chiaro"
                themeText.textContent = theme === 'light' ? 'Tema Scuro' : 'Tema Chiaro';
            }
            // Aggiorna aria-label
            themeToggle.setAttribute('aria-label', 
                theme === 'light' ? 'Attiva tema scuro' : 'Attiva tema chiaro');
        }
    }

    // === GESTIONE BACK TO TOP ===
    const backToTop = document.querySelector('.back-to-top');
    if (backToTop) {
        backToTop.addEventListener('click', function(e) {
            e.preventDefault();
            const mainContent = document.getElementById('main-content');
            if (mainContent) {
                mainContent.setAttribute('tabindex', '-1');
                mainContent.focus();
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
                setTimeout(() => mainContent.removeAttribute('tabindex'), 1000);
            }
        });
    }

    // === ORDINAMENTO SUBFOLDER (per verbali) ===
    function sortSubfoldersDesc(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const items = Array.from(container.querySelectorAll(':scope > .subfolder'));
        if (items.length === 0) return;
        
        items.sort((a, b) => {
            const ha = (a.querySelector('.folder-header h4') || {}).textContent || '';
            const hb = (b.querySelector('.folder-header h4') || {}).textContent || '';
            
            // Ordinamento numerico-aware in ordine decrescente
            return hb.trim().localeCompare(ha.trim(), undefined, { 
                numeric: true, 
                sensitivity: 'base' 
            });
        });
        
        // Ri-append in ordine ordinato
        items.forEach(item => container.appendChild(item));
    }

    // Applica ordinamento alle sezioni verbali
    sortSubfoldersDesc('verbali-interni-content');
    sortSubfoldersDesc('verbali-esterni-content');

    // === GESTIONE CARTELLE ESPANDIBILI ===
    const folderHeaders = document.querySelectorAll('.folder-header');

    // Annunci per screen reader
    function announceToScreenReader(message) {
        let announcer = document.getElementById('aria-announcer');
        if (!announcer) {
            announcer = document.createElement('div');
            announcer.id = 'aria-announcer';
            announcer.setAttribute('aria-live', 'polite');
            announcer.setAttribute('aria-atomic', 'true');
            announcer.className = 'sr-only';
            document.body.appendChild(announcer);
        }
        
        // Cancella e reimposta il messaggio per forzare l'annuncio
        announcer.textContent = '';
        setTimeout(() => {
            announcer.textContent = message;
        }, 100);
    }

    // Imposta lo stato di espansione
    function setCollapsedState(header, collapsed = true) {
        const folderId = header.getAttribute('data-folder');
        const content = document.getElementById(`${folderId}-content`);
        const toggleIcon = header.querySelector('.toggle-icon');
        
        if (!content) return;

        if (collapsed) {
            content.classList.remove('expanded');
            content.setAttribute('aria-hidden', 'true');
            header.setAttribute('aria-expanded', 'false');
            if (toggleIcon) toggleIcon.textContent = '+';
        } else {
            content.classList.add('expanded');
            content.setAttribute('aria-hidden', 'false');
            header.setAttribute('aria-expanded', 'true');
            if (toggleIcon) toggleIcon.textContent = '−'; // Carattere meno vero
        }
        
        // Annuncia il cambiamento
        const sectionName = header.querySelector('h3, h4')?.textContent || 'sezione';
        const action = collapsed ? 'collassata' : 'espansa';
        announceToScreenReader(`${sectionName} ${action}`);
    }

    // Alterna stato di espansione
    function toggleHeader(header) {
        const folderId = header.getAttribute('data-folder');
        const content = document.getElementById(`${folderId}-content`);
        if (!content) return;
        
        const isExpanded = content.classList.contains('expanded');
        setCollapsedState(header, isExpanded);
    }

    // Inizializza tutti gli header delle cartelle
    folderHeaders.forEach(header => {
        // Assicura che tutti gli attributi ARIA siano presenti
        if (!header.hasAttribute('role')) {
            header.setAttribute('role', 'button');
        }
        if (!header.hasAttribute('tabindex')) {
            header.setAttribute('tabindex', '0');
        }
        if (!header.hasAttribute('aria-expanded')) {
            header.setAttribute('aria-expanded', 'false');
        }

        const folderId = header.getAttribute('data-folder');
        const content = document.getElementById(`${folderId}-content`);
        if (content) {
            if (!content.hasAttribute('aria-hidden')) {
                content.setAttribute('aria-hidden', 'true');
            }
            if (!content.hasAttribute('role')) {
                content.setAttribute('role', 'region');
            }
        }

        // Gestione click
        header.addEventListener('click', function (e) {
            // Ignora click su elementi figli interattivi (come link)
            if (e.target.tagName.toLowerCase() === 'a') return;
            toggleHeader(this);
        });

        // Gestione tastiera
        header.addEventListener('keydown', function (e) {
            switch(e.key) {
                case 'Enter':
                case ' ':
                    e.preventDefault();
                    toggleHeader(this);
                    break;
                case 'Escape':
                    if (this.getAttribute('aria-expanded') === 'true') {
                        setCollapsedState(this, true);
                        this.focus(); // Riporta il focus sull'header
                    }
                    break;
                case 'ArrowDown':
                    if (this.getAttribute('aria-expanded') === 'true') {
                        e.preventDefault();
                        const content = document.getElementById(`${this.getAttribute('data-folder')}-content`);
                        const firstLink = content?.querySelector('a');
                        if (firstLink) {
                            firstLink.focus();
                        }
                    }
                    break;
            }
        });

        // Miglioramento gestione focus
        header.addEventListener('focus', function() {
            this.style.zIndex = '5';
        });

        header.addEventListener('blur', function() {
            this.style.zIndex = '';
        });
    });

    // Gestione avanzata del focus per contenuti espansi
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Tab' && e.target.classList.contains('folder-header')) {
            const content = document.getElementById(e.target.getAttribute('data-folder') + '-content');
            if (content && content.classList.contains('expanded')) {
                const focusableElements = content.querySelectorAll('a, button, [tabindex]:not([tabindex="-1"])');
                if (focusableElements.length > 0) {
                    e.preventDefault();
                    focusableElements[0].focus();
                }
            }
        }
        
        // Gestione Shift+Tab per tornare all'header
        if (e.key === 'Tab' && e.shiftKey && e.target.matches('.folder-content a, .folder-content button')) {
            const content = e.target.closest('.folder-content');
            if (content) {
                const header = document.querySelector(`[data-folder="${content.id.replace('-content', '')}"]`);
                if (header && header.getAttribute('aria-expanded') === 'true') {
                    const firstFocusable = content.querySelector('a, button, [tabindex]:not([tabindex="-1"])');
                    if (firstFocusable === e.target) {
                        e.preventDefault();
                        header.focus();
                    }
                }
            }
        }
    });

    // Inizializza tutti i folder come collassati
    folderHeaders.forEach(header => setCollapsedState(header, true));
    
    // === GESTIONE LINK ESTERNI ===
    document.querySelectorAll('a[target="_blank"]').forEach(link => {
        // Assicura che tutti i link esterni abbiano l'attributo aria-label appropriato
        if (!link.hasAttribute('aria-label')) {
            const linkText = link.textContent.trim();
            link.setAttribute('aria-label', `${linkText} (si apre in una nuova finestra)`);
        }
    });

    // === SUPPORTO PER RIDUZIONE ANIMAZIONI ===
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    
    function handleReduceMotionChange(e) {
        if (e.matches) {
            document.documentElement.style.setProperty('--transition', 'none');
        } else {
            document.documentElement.style.setProperty('--transition', 'all 0.3s ease');
        }
    }
    
    reduceMotion.addListener(handleReduceMotionChange);
    handleReduceMotionChange(reduceMotion);

    console.log('Sistema di accessibilità e tema inizializzati con successo');
});