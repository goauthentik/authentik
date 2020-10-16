import { LitElement, html } from 'lit-element';

const LEVEL_ICON_MAP = {
    "error": "fas fa-exclamation-circle",
    "warning": "fas fa-exclamation-triangle",
    "success": "fas fa-check-circle",
    "info": "fas fa-info",
};

let ID = function (prefix) {
    return prefix + Math.random().toString(36).substr(2, 9);
};

export function updateMessages() {
    document.querySelector("pb-messages").setAttribute("touch", Date.now());
}

class Messages extends LitElement {

    static get properties() {
        return {
            url: { type: String },
            messages: { type: Array },
            touch: { type: Object },
        };
    }

    set touch(value) {
        this.firstUpdated();
    }

    createRenderRoot() {
        return this;
    }

    firstUpdated() {
        return fetch(this.url).then(r => r.json()).then(r => this.messages = r);
    }

    renderMessage(message) {
        const id = ID("pb-message");
        const el = document.createElement("template");
        el.innerHTML = `<li id=${id} class="pf-c-alert-group__item">
            <div class="pf-c-alert pf-m-${message.level_tag} ${message.level_tag === 'error' ? 'pf-m-danger': ''}">
                <div class="pf-c-alert__icon">
                    <i class="${LEVEL_ICON_MAP[message.level_tag]}"></i>
                </div>
                <p class="pf-c-alert__title">
                    ${message.message}
                </p>
            </div>
        </li>`;
        setTimeout(() => {
            this.querySelector(`#${id}`).remove();
        }, 1500);
        return el.content.firstChild;
    }

    render() {
        if (this.messages === undefined) {
            return html`<ul class="pf-c-alert-group pf-m-toast"></ul>`;
        }
        return html`<ul class="pf-c-alert-group pf-m-toast">${this.messages.map(item => this.renderMessage(item))}</ul>`;
    }
}

customElements.define('pb-messages', Messages);
