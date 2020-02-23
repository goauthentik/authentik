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
document.querySelectorAll(".pf-c-modal-box [data-modal-close]").forEach((b) => {
    b.addEventListener("click", (e) => {
        const parentContainer = e.target.closest('.pf-c-backdrop');
        parentContainer.setAttribute("hidden", true);
    });
});

// CodeMirror
document.querySelectorAll(".codemirror").forEach((cm) => {
    let cmMode = 'xml';
    if ('data-cm-mode' in cm.attributes) {
        cmMode = cm.attributes['data-cm-mode'].value;
    }
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
        .replace(/[^\w ]+/g, '')
        .replace(/ +/g, '-');
};

document.querySelectorAll("input[name=name]").forEach((input) => {
    input.addEventListener("input", (e) => {
        const form = e.target.closest("form");
        const slugField = form.querySelector("input[name=slug]");
        slugField.value = convertToSlug(slugField.value);
    });
});

// Dynamic Array field logic
window.addEventListener('load', function () {

    function addRemoveEventListener(widgetElement) {
        widgetElement.querySelectorAll('.array-remove').forEach(function (element) {
            element.addEventListener('click', function () {
                this.parentNode.parentNode.remove();
            });
        });
    }

    document.querySelectorAll('.dynamic-array-widget').forEach(function (widgetElement) {

        addRemoveEventListener(widgetElement);

        widgetElement.querySelector('.add-array-item').addEventListener('click', function () {
            var first = widgetElement.querySelector('.array-item');
            var newElement = first.cloneNode(true);
            var id_parts = newElement.querySelector('input').getAttribute('id').split('_');
            var id = id_parts.slice(0, -1).join('_') + '_' + String(parseInt(id_parts.slice(-1)[0]) + 1);
            newElement.querySelector('input').setAttribute('id', id);
            newElement.querySelector('input').value = '';

            addRemoveEventListener(newElement);
            first.parentElement.insertBefore(newElement, first.parentNode.lastChild);
        });

    });

});
