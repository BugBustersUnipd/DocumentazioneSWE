document.addEventListener('DOMContentLoaded', function () {
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(a => {
        a.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            const doc = this.getAttribute('data-doc');
            if (href && href.startsWith('#')) {
                const target = document.querySelector(href);
                if (target) {
                    if (doc) {
                        e.preventDefault();
                        showDocPanel(doc);
                        return;
                    }

                    e.preventDefault();
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
        });
    });

    // Doc panel switching inside the Documentazione section
    const docToggles = document.querySelectorAll('.doc-toggle');
    const docPanels = document.querySelectorAll('.doc-panel');

    function scrollToElement(el) {
        if (!el) return;
        const header = document.querySelector('header');
        const headerHeight = header ? header.getBoundingClientRect().height : 110;
        const rect = el.getBoundingClientRect();
        const y = rect.top + window.pageYOffset - (headerHeight + 12);
        window.scrollTo({ top: y, behavior: 'auto' });
    }

    function showDocPanel(name) {
        // Hide all panels
        docPanels.forEach(p => {
            p.classList.remove('active');
            p.setAttribute('aria-hidden', 'true');
        });
        
        // Show selected panel
        const panelId = 'panel-' + name;
        const active = document.getElementById(panelId);
        if (active) {
            active.classList.add('active');
            active.setAttribute('aria-hidden', 'false');
        } else {
            // Fallback to candidatura if panel not found
            const fallback = document.getElementById('panel-candidatura');
            if (fallback) {
                fallback.classList.add('active');
                fallback.setAttribute('aria-hidden', 'false');
            }
        }

        // Update doc toggle buttons
        docToggles.forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-show') === name);
            btn.setAttribute('aria-selected', btn.classList.contains('active') ? 'true' : 'false');
        });

        // Scroll to the "Documentazione" title
        const docTitle = document.querySelector('#candidatura .page-title');
        scrollToElement(docTitle);
        
        // Focus the title for accessibility
        if (docTitle) {
            docTitle.setAttribute('tabindex', '-1');
            try { 
                docTitle.focus({ preventScroll: true }); 
            } catch (_) { 
                docTitle.focus(); 
            }
        }
    }

    // Add click handlers to doc toggle buttons
    docToggles.forEach(btn => {
        btn.addEventListener('click', function(e) {
            const show = this.getAttribute('data-show');
            showDocPanel(show);
        });
    });

    // Announce page load to screen readers
    const mainContent = document.getElementById('main-content');
    if (mainContent) {
        mainContent.setAttribute('aria-live', 'polite');
    }
});