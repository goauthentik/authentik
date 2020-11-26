import { LitElement, html, customElement, property } from "lit-element";

const LEVEL_ICON_MAP: { [key: string]: string } = {
    error: "fas fa-exclamation-circle",
    warning: "fas fa-exclamation-triangle",
    success: "fas fa-check-circle",
    info: "fas fa-info",
};

let ID = function (prefix: string) {
    return prefix + Math.random().toString(36).substr(2, 9);
};

interface Message {
    levelTag: string;
    tags: string[];
    message: string;
}

@customElement("pb-messages")
export class Messages extends LitElement {
    @property()
    url: string = "";

    @property()
    messages: string[] = [];

    messageSocket?: WebSocket;

    createRenderRoot() {
        return this;
    }

    constructor() {
        super();
        this.connect();
    }

    connect() {
        const wsUrl = `${window.location.protocol.replace("http", "ws")}//${
            window.location.host
        }/ws/client/`;
        this.messageSocket = new WebSocket(wsUrl);
        this.messageSocket.addEventListener("open", (e) => {
            console.debug(`passbook/messages: connected to ${wsUrl}`);
        });
        this.messageSocket.addEventListener("close", (e) => {
            console.debug(`passbook/messages: closed ws connection: ${e}`);
            setTimeout(() => {
                console.debug(`passbook/messages: reconnecting ws`);
                this.connect();
            }, 1000);
        });
        this.messageSocket.addEventListener("message", (e) => {
            const container = <HTMLElement>(
                this.querySelector(".pf-c-alert-group")!
            );
            const data = JSON.parse(e.data);
            const messageElement = this.renderMessage(data);
            container.appendChild(messageElement);
        });
    }

    renderMessage(message: Message): ChildNode {
        const id = ID("pb-message");
        const el = document.createElement("template");
        el.innerHTML = `<li id=${id} class="pf-c-alert-group__item">
            <div class="pf-c-alert pf-m-${message.levelTag} ${
            message.levelTag === "error" ? "pf-m-danger" : ""
        }">
                <div class="pf-c-alert__icon">
                    <i class="${LEVEL_ICON_MAP[message.levelTag]}"></i>
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
