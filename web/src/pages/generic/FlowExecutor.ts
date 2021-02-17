import { gettext } from "django";
import { LitElement, html, customElement, property, TemplateResult } from "lit-element";
import { unsafeHTML } from "lit-html/directives/unsafe-html";
import { SentryIgnoredError } from "../../common/errors";
import { getCookie } from "../../utils";
import "../../elements/stages/identification/IdentificationStage";

enum ChallengeTypes {
    native = "native",
    response = "response",
    shell = "shell",
    redirect = "redirect",
}

interface Challenge {
    type: ChallengeTypes;
    args: { [key: string]: string };
    component: string;
}

@customElement("ak-flow-executor")
export class FlowExecutor extends LitElement {
    @property()
    flowBodyUrl = "";

    @property({attribute: false})
    flowBody?: TemplateResult;

    createRenderRoot(): Element | ShadowRoot {
        return this;
    }

    constructor() {
        super();
        this.addEventListener("ak-flow-submit", () => {
            this.submit();
        });
    }

    submit(formData?: FormData): void {
        const csrftoken = getCookie("authentik_csrf");
        const request = new Request(this.flowBodyUrl, {
            headers: {
                "X-CSRFToken": csrftoken,
            },
        });
        fetch(request, {
            method: "POST",
            mode: "same-origin",
            body: formData,
        })
            .then((response) => {
                return response.json();
            })
            .then((data) => {
                this.updateCard(data);
            })
            .catch((e) => {
                this.errorMessage(e);
            });
    }

    firstUpdated(): void {
        fetch(this.flowBodyUrl)
            .then((r) => {
                if (r.status === 404) {
                    // Fallback when the flow does not exist, just redirect to the root
                    window.location.pathname = "/";
                } else if (!r.ok) {
                    throw new SentryIgnoredError(r.statusText);
                }
                return r;
            })
            .then((r) => {
                return r.json();
            })
            .then((r) => {
                this.updateCard(r);
            })
            .catch((e) => {
                // Catch JSON or Update errors
                this.errorMessage(e);
            });
    }

    async updateCard(data: Challenge): Promise<void> {
        switch (data.type) {
        case ChallengeTypes.redirect:
            console.debug(`authentik/flows: redirecting to ${data.args.to}`);
            window.location.assign(data.args.to || "");
            break;
        case ChallengeTypes.shell:
            this.flowBody = html`${unsafeHTML(data.args.body)}`;
            await this.requestUpdate();
            this.checkAutofocus();
            this.loadFormCode();
            this.setFormSubmitHandlers();
            break;
        case ChallengeTypes.native:
            switch (data.component) {
                case "ak-stage-identification":
                    this.flowBody = html`<ak-stage-identification .host=${this} .args=${data.args}></ak-stage-identification>`;
                    break;
                default:
                    break;
            }
            // this.flowBody = html`${unsafeHTML(`<${data.component} .args="${data.args}"></${data.component}>`)}`;
            break;
        default:
            console.debug(`authentik/flows: unexpected data type ${data.type}`);
            break;
        }
    }

    loadFormCode(): void {
        this.querySelectorAll("script").forEach((script) => {
            const newScript = document.createElement("script");
            newScript.src = script.src;
            document.head.appendChild(newScript);
        });
    }

    checkAutofocus(): void {
        const autofocusElement = <HTMLElement>this.querySelector("[autofocus]");
        if (autofocusElement !== null) {
            autofocusElement.focus();
        }
    }

    updateFormAction(form: HTMLFormElement): boolean {
        for (let index = 0; index < form.elements.length; index++) {
            const element = <HTMLInputElement>form.elements[index];
            if (element.value === form.action) {
                console.debug(
                    "authentik/flows: Found Form action URL in form elements, not changing form action."
                );
                return false;
            }
        }
        form.action = this.flowBodyUrl;
        console.debug(`authentik/flows: updated form.action ${this.flowBodyUrl}`);
        return true;
    }

    checkAutosubmit(form: HTMLFormElement): void {
        if ("autosubmit" in form.attributes) {
            return form.submit();
        }
    }

    setFormSubmitHandlers(): void {
        this.querySelectorAll("form").forEach((form) => {
            console.debug(`authentik/flows: Checking for autosubmit attribute ${form}`);
            this.checkAutosubmit(form);
            console.debug(`authentik/flows: Setting action for form ${form}`);
            this.updateFormAction(form);
            console.debug(`authentik/flows: Adding handler for form ${form}`);
            form.addEventListener("submit", (e) => {
                e.preventDefault();
                const formData = new FormData(form);
                this.flowBody = undefined;
                this.submit(formData);
            });
            form.classList.add("ak-flow-wrapped");
        });
    }

    errorMessage(error: string): void {
        this.flowBody = html`
            <style>
                .ak-exception {
                    font-family: monospace;
                    overflow-x: scroll;
                }
            </style>
            <header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">
                    ${gettext("Whoops!")}
                </h1>
            </header>
            <div class="pf-c-login__main-body">
                <h3>${gettext("Something went wrong! Please try again later.")}</h3>
                <pre class="ak-exception">${error}</pre>
            </div>`;
    }

    loading(): TemplateResult {
        return html` <div class="pf-c-login__main-body ak-loading">
            <span class="pf-c-spinner" role="progressbar" aria-valuetext="Loading...">
                <span class="pf-c-spinner__clipper"></span>
                <span class="pf-c-spinner__lead-ball"></span>
                <span class="pf-c-spinner__tail-ball"></span>
            </span>
        </div>`;
    }

    render(): TemplateResult {
        if (this.flowBody) {
            return this.flowBody;
        }
        return this.loading();
    }
}
