// Button Dropdowns
document.querySelectorAll("button.pf-c-dropdown__toggle").forEach((b) => {
    b.addEventListener('click', (e) => {
        const parent = e.target.closest('.pf-c-dropdown');
        const menu = parent.querySelector('.pf-c-dropdown__menu');
        menu.hidden = !menu.hidden;
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
document.querySelectorAll(".pf-c-modal-box [data-modal-close]").forEach(b => {
    b.addEventListener("click", (e) => {
        const parentContainer = e.target.closest('.pf-c-backdrop');
        parentContainer.setAttribute("hidden", true);
    });
});
