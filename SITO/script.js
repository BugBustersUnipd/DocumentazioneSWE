document.addEventListener('DOMContentLoaded', function () {
    // New navigation and internal documentation switch
    const dropdown = document.querySelector('.dropdown');
    const dropdownToggle = dropdown?.querySelector('.dropdown-toggle');
    const dropdownMenu = dropdown?.querySelector('.dropdown-menu');
    const dropdownItems = dropdown?.querySelectorAll('.dropdown-item');

    // Smooth scroll for anchor links that should go to sections
    document.querySelectorAll('a[href^="#"]').forEach(a => {
        a.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            const doc = this.getAttribute('data-doc');
            if (href && href.startsWith('#')) {
                const target = document.querySelector(href);
                if (target) {
                    // if the link is meant to switch an internal doc panel, let showDocPanel
                    // handle activation and scrolling to the specific panel
                    if (doc) {
                        e.preventDefault();
                        showDocPanel(doc);
                        return;
                    }

                    // otherwise perform a normal smooth scroll to the target section
                    e.preventDefault();
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
        });
    });

    // doc panel switching inside the Documentazione section
    const docToggles = document.querySelectorAll('.doc-toggle');
    const docPanels = document.querySelectorAll('.doc-panel');

    function scrollToElement(el) {
        if (!el) return;
        const header = document.querySelector('header');
        const headerHeight = header ? header.getBoundingClientRect().height : 110; // fallback
        const rect = el.getBoundingClientRect();
        const y = rect.top + window.pageYOffset - (headerHeight + 12);
        window.scrollTo({ top: y, behavior: 'auto' });
    }

    function showDocPanel(name) {
        // generic panel switcher: panel id is 'panel-' + name
        docPanels.forEach(p => {
            p.classList.remove('active');
            p.setAttribute('aria-hidden', 'true');
        });
        const panelId = 'panel-' + name;
        const active = document.getElementById(panelId);
        if (active) {
            active.classList.add('active');
            active.setAttribute('aria-hidden', 'false');
        } else {
            // fallback to candidatura if panel not found
            const fallback = document.getElementById('panel-candidatura');
            if (fallback) {
                fallback.classList.add('active');
                fallback.setAttribute('aria-hidden', 'false');
            }
        }

        // update doc toggle buttons (the top tabs)
        docToggles.forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-show') === name);
            btn.setAttribute('aria-selected', btn.classList.contains('active') ? 'true' : 'false');
        });

        // update dropdown items active state if present
        dropdownItems?.forEach(it => {
            const itDoc = it.getAttribute('data-doc');
            if (itDoc === name) {
                it.classList.add('active');
            } else {
                it.classList.remove('active');
            }
        });

        // scroll to the "Documentazione" title (not the whole section)
        const docTitle = document.querySelector('#candidatura .page-title');
        scrollToElement(docTitle);
        // focus the title for a11y
        if (docTitle) {
            docTitle.setAttribute('tabindex', '-1');
            try { docTitle.focus({ preventScroll: true }); } catch (_) { docTitle.focus(); }
        }
    }

    docToggles.forEach(btn => {
        btn.addEventListener('click', function(e) {
            const show = this.getAttribute('data-show');
            showDocPanel(show);
        });
    });

    // Wire dropdown items to scroll and switch panel
    dropdownItems?.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const doc = this.getAttribute('data-doc');
            if (doc) {
                showDocPanel(doc);
            }
            dropdown.classList.remove('active');
        });
    });

    // Dropdown open/close behavior
    if (dropdownToggle && dropdown) {
        dropdownToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const isActive = dropdown.classList.toggle('active');
            this.setAttribute('aria-expanded', isActive ? 'true' : 'false');
            if (isActive) {
                const first = dropdown.querySelector('.dropdown-item');
                first?.focus();
            }
        });

        document.addEventListener('click', function(e) {
            if (!dropdown.contains(e.target)) {
                dropdown.classList.remove('active');
                dropdownToggle.setAttribute('aria-expanded', 'false');
            }
        });
    }

    // Announce page load to screen readers
    const mainContent = document.getElementById('main-content');
    if (mainContent) {
        mainContent.setAttribute('aria-live', 'polite');
    }

    // ===== CONTROLLO HASH ALL'AVVIO =====
    // Controlla l'hash all'avvio per attivare la tab corretta
    function checkHashOnLoad() {
        const hash = window.location.hash.substring(1); // Rimuove il #
        if (hash && ['candidatura', 'diapositive', 'rtb'].includes(hash)) {
            showDocPanel(hash);
        }
    }
    
    // Chiama la funzione all'avvio
    checkHashOnLoad();
    
    // Aggiungi listener per cambiamenti dell'hash
    window.addEventListener('hashchange', checkHashOnLoad);

    // ===== GESTIONE STATO DEI DETAILS (MANTIENE GLI ELEMENTI ESPANSI) =====
    function saveDetailsState() {
        const detailsState = {};
        document.querySelectorAll('details').forEach(details => {
            const id = details.id || details.querySelector('summary')?.textContent?.trim();
            if (id) {
                detailsState[id] = details.open;
            }
        });
        localStorage.setItem('detailsState', JSON.stringify(detailsState));
    }

    function restoreDetailsState() {
        const savedState = localStorage.getItem('detailsState');
        if (savedState) {
            const detailsState = JSON.parse(savedState);
            
            document.querySelectorAll('details').forEach(details => {
                const id = details.id || details.querySelector('summary')?.textContent?.trim();
                if (id && detailsState[id] === true) {
                    // Usa setTimeout per assicurarsi che il DOM sia completamente pronto
                    setTimeout(() => {
                        details.open = true;
                    }, 10);
                }
            });
        }
    }

    // Ripristina lo stato dei details al caricamento della pagina
    restoreDetailsState();
    
    // Salva lo stato dei details quando cambiano
    document.querySelectorAll('details').forEach(details => {
        details.addEventListener('toggle', saveDetailsState);
    });

    // ===== FUNZIONALITÀ TORNA SU =====
    const tornaSuBtn = document.getElementById('tornaSuBtn');

    function mostraTornaSuBtn() {
        if (window.scrollY > 300) {
            tornaSuBtn.style.display = 'flex';
            setTimeout(() => {
                tornaSuBtn.classList.add('visible');
            }, 10);
        } else {
            tornaSuBtn.classList.remove('visible');
            setTimeout(() => {
                if (!tornaSuBtn.classList.contains('visible')) {
                    tornaSuBtn.style.display = 'none';
                }
            }, 300);
        }
    }

    function scrollToTop() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    }

    if (tornaSuBtn) {
        window.addEventListener('scroll', mostraTornaSuBtn);
        tornaSuBtn.addEventListener('click', scrollToTop);
        // Controllo iniziale
        mostraTornaSuBtn();
    }

    // ===== FUNZIONALITÀ MODALITÀ SCURA/CHIARA =====
    const temaToggleBtn = document.getElementById('temaToggleBtn');
    const temaIcon = temaToggleBtn?.querySelector('.icon');

    // SEMPRE TEMA CHIARO ALL'APERTURA - IGNORA QUALSIASI PREFERENZA SALVATA
    function applicaTema(tema) {
        if (tema === 'dark') {
            document.body.classList.add('dark-theme');
            if (temaIcon) temaIcon.textContent = '☀️';
            temaToggleBtn?.classList.add('dark');
        } else {
            document.body.classList.remove('dark-theme');
            if (temaIcon) temaIcon.textContent = '🌙';
            temaToggleBtn?.classList.remove('dark');
        }
        
        // NON SALVIAMO LA PREFERENZA IN LOCALSTORAGE
    }

    // Cambia il tema
    function cambiaTema() {
        const temaAttuale = document.body.classList.contains('dark-theme') ? 'dark' : 'light';
        const nuovoTema = temaAttuale === 'dark' ? 'light' : 'dark';
        
        applicaTema(nuovoTema);
    }

    // Inizializza SEMPRE con il tema chiaro
    applicaTema('light');
    
    // Aggiungi event listener al pulsante
    if (temaToggleBtn) {
        temaToggleBtn.addEventListener('click', cambiaTema);
    }
});