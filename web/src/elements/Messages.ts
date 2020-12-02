import { LitElement, html, customElement, TemplateResult } from "lit-element";
import { DefaultClient } from "../api/client";

const LEVEL_ICON_MAP: { [key: string]: string } = {
    error: "fas fa-exclamation-circle",
    warning: "fas fa-exclamation-triangle",
    success: "fas fa-check-circle",
    info: "fas fa-info",
};

const ID = function (prefix: string) {
    return prefix + Math.random().toString(36).substr(2, 9);
};

interface Message {
    level_tag: string;
    tags: string;
    message: string;
}

@customElement("pb-messages")
export class Messages extends LitElement {
    url = DefaultClient.makeUrl(["root", "messages"]);

    messageSocket?: WebSocket;
    retryDelay = 200;

    createRenderRoot(): ShadowRoot | Element {
        return this;
    }

    constructor() {
        super();
        try {
            this.connect();
        } catch (error) {
            console.warn(`authentik/messages: failed to connect to ws ${error}`);
        }
    }

    firstUpdated(): void {
        this.fetchMessages();
    }

    connect(): void {
        const wsUrl = `${window.location.protocol.replace("http", "ws")}//${
            window.location.host
        }/ws/client/`;
        this.messageSocket = new WebSocket(wsUrl);
        this.messageSocket.addEventListener("open", () => {
            console.debug(`authentik/messages: connected to ${wsUrl}`);
        });
        this.messageSocket.addEventListener("close", (e) => {
            console.debug(`authentik/messages: closed ws connection: ${e}`);
            setTimeout(() => {
                console.debug(`authentik/messages: reconnecting ws in ${this.retryDelay}ms`);
                this.connect();
            }, this.retryDelay);
            this.retryDelay = this.retryDelay * 2;
        });
        this.messageSocket.addEventListener("message", (e) => {
            const data = JSON.parse(e.data);
            this.renderMessage(data);
        });
        this.messageSocket.addEventListener("error", (e) => {
            console.warn(`authentik/messages: error ${e}`);
            this.retryDelay = this.retryDelay * 2;
        });
    }

    /* Fetch messages which were stored in the session.
     * This mostly gets messages which were created when the user arrives/leaves the site
     * and especially the login flow */
    fetchMessages(): Promise<void> {
        console.debug("authentik/messages: fetching messages over direct api");
        return fetch(this.url)
            .then((r) => r.json())
            .then((r: Message[]) => {
                r.forEach((m: Message) => {
                    this.renderMessage(m);
                });
            });
    }

    renderMessage(message: Message): void {
        const container = <HTMLElement>this.querySelector(".pf-c-alert-group");
        if (!container) {
            console.warn("authentik/messages: failed to find container");
            return;
        }
        const id = ID("pb-message");
        const el = document.createElement("template");
        el.innerHTML = `<li id=${id} class="pf-c-alert-group__item">
            <div class="pf-c-alert pf-m-${message.level_tag} ${message.level_tag === "error" ? "pf-m-danger" : ""}">
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
        container.appendChild(el.content.firstChild!); // eslint-disable-line
    }

    render(): TemplateResult {
        return html`<ul class="pf-c-alert-group pf-m-toast"></ul>`;
    }
}
