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
            if (href && href.startsWith('#')) {
                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    // if link carries data-doc attribute, also switch panel
                    const doc = this.getAttribute('data-doc');
                    if (doc) {
                        showDocPanel(doc);
                    }
                }
            }
        });
    });

    // doc panel switching inside the Documentazione section
    const docToggles = document.querySelectorAll('.doc-toggle');
    const docPanels = document.querySelectorAll('.doc-panel');

    function showDocPanel(name) {
        docPanels.forEach(p => {
            p.classList.remove('active');
            p.setAttribute('aria-hidden', 'true');
        });
        const active = document.getElementById(name === 'diapositive' ? 'panel-diapositive' : 'panel-candidatura');
        if (active) {
            active.classList.add('active');
            active.setAttribute('aria-hidden', 'false');
        }

        docToggles.forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-show') === (name === 'diapositive' ? 'diapositive' : 'candidatura'));
            btn.setAttribute('aria-selected', btn.classList.contains('active') ? 'true' : 'false');
        });
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
            // default anchor behaviour will scroll; also switch doc panel
            const doc = this.getAttribute('data-doc');
            if (doc) {
                showDocPanel(doc);
            }
            // close dropdown visually
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
});