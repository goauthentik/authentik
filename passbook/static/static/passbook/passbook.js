// Button Dropdowns
document.querySelectorAll("button.pf-c-dropdown__toggle").forEach((b) => {
    b.addEventListener('click', (e) => {
        const parent = e.target.closest('.pf-c-dropdown');
        const menu = parent.querySelector('.pf-c-dropdown__menu');
        menu.hidden = !menu.hidden;
    });
});

// Search clearing
document.querySelectorAll("input[type=search]").forEach((si) => {
    si.addEventListener("search", (e) => {
        if (si.value === "") {
            si.parentElement.submit();
        }
    });
});

// Fetch from data-attributes
document.querySelectorAll("[data-pb-fetch-fill]").forEach((el) => {
    const url = el.dataset.pbFetchFill;
    const key = el.dataset.pbFetchKey;
    fetch(url).then(r => r.json()).then(r => {
        el.textContent = r[key];
        el.value = r[key];
    });
});

// Modal
document.querySelectorAll("[data-target='modal']").forEach((m) => {
    m.addEventListener("click", (e) => {
        const parentContainer = e.target.closest('[data-target="modal"]');
        const modalId = parentContainer.attributes['data-modal'].value;
        document.querySelector(`#${modalId}`).removeAttribute("hidden");
    });
});
document.querySelectorAll(".pf-c-modal-box [data-modal-close]").forEach((b) => {
    b.addEventListener("click", (e) => {
        const parentContainer = e.target.closest('.pf-c-backdrop');
        parentContainer.setAttribute("hidden", true);
    });
});

// Make Checkbox label click trigger checkbox toggle
document.querySelectorAll(".pf-c-check__label").forEach((checkLabel) => {
    checkLabel.addEventListener("click", (e) => {
        const checkbox = e.target.parentElement.querySelector("input[type=checkbox]");
        checkbox.checked = !checkbox.checked;
    });
});

// CodeMirror
document.querySelectorAll(".codemirror").forEach((cm) => {
    let cmMode = 'xml';
    if ('data-cm-mode' in cm.attributes) {
        cmMode = cm.attributes['data-cm-mode'].value;
    }
    // https://github.com/codemirror/CodeMirror/issues/5092
    cm.removeAttribute("required");
    CodeMirror.fromTextArea(cm, {
        mode: cmMode,
        theme: 'monokai',
        lineNumbers: false,
        readOnly: cm.readOnly,
        autoRefresh: true,
    });
});

// Automatic slug fields
const convertToSlug = (text) => {
    return text
        .toLowerCase()
        .replace(/ /g, '-')
        .replace(/[^\w-]+/g, '');
};

document.querySelectorAll("input[name=name]").forEach((input) => {
    input.addEventListener("input", (e) => {
        const form = e.target.closest("form");
        if (form === null) {
            return;
        }
        const slugField = form.querySelector("input[name=slug]");
        slugField.value = convertToSlug(e.target.value);
    });
});

// Hamburger Menu
document.querySelectorAll(".pf-c-page__header-brand-toggle>button").forEach((toggle) => {
    toggle.addEventListener("click", (e) => {
        const sidebar = document.querySelector(".pf-c-page__sidebar");
        if (sidebar.classList.contains("pf-m-expanded")) {
            // Sidebar already expanded
            sidebar.classList.remove("pf-m-expanded");
            sidebar.style.zIndex = 0;
        } else {
            // Sidebar not expanded yet
            sidebar.classList.add("pf-m-expanded");
            sidebar.style.zIndex = 200;
        }
    });
});

// Collapsable Menus in Sidebar
document.querySelectorAll(".pf-m-expandable>.pf-c-nav__link").forEach((menu) => {
    menu.addEventListener("click", (e) => {
        e.preventDefault();
        menu.parentElement.classList.toggle("pf-m-expanded");
    });
});
