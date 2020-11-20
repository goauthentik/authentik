import { LitElement, html, customElement, property } from 'lit-element';

const LEVEL_ICON_MAP: { [key: string]: string } = {
    "error": "fas fa-exclamation-circle",
    "warning": "fas fa-exclamation-triangle",
    "success": "fas fa-check-circle",
    "info": "fas fa-info",
};

let ID = function (prefix: string) {
    return prefix + Math.random().toString(36).substr(2, 9);
};

export function updateMessages() {
    const messageElement = <Messages>document?.querySelector("pb-messages");
    messageElement.fetchMessages();
}

interface Message {
    level_tag: string;
    message: string;
}

@customElement("pb-messages")
export class Messages extends LitElement {

    @property()
    url: string = "";

    @property()
    messages: string[] = [];

    createRenderRoot() {
        return this;
    }

    firstUpdated() {
        this.fetchMessages();
    }

    fetchMessages() {
        return fetch(this.url).then(r => r.json()).then(r => this.messages = r).then((r) => {
            const container = <HTMLElement>this.querySelector(".pf-c-alert-group")!;
            r.forEach((message: Message) => {
                const messageElement = this.renderMessage(message);
                container.appendChild(messageElement);
            });
        });
    }

    renderMessage(message: Message): ChildNode {
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
            this.querySelector(`#${id}`)?.remove();
        }, 1500);
        return el.content.firstChild!;
    }

    render() {
        return html`<ul class="pf-c-alert-group pf-m-toast"></ul>`;
    }
}
