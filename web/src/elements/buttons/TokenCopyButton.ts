import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import { CoreApi } from "authentik-api";
import { ERROR_CLASS, PRIMARY_CLASS, SUCCESS_CLASS } from "../../constants";
import { DEFAULT_CONFIG } from "../../api/Config";
import AKGlobal from "../../authentik.css";

@customElement("ak-token-copy-button")
export class TokenCopyButton extends LitElement {
    @property()
    identifier?: string;

    @property()
    buttonClass: string = PRIMARY_CLASS;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFButton,
            AKGlobal,
            css`
                button {
                    transition: background-color 0.3s ease 0s;
                }
            `,
        ];
    }

    onClick(): void {
        if (!this.identifier) {
            this.buttonClass = ERROR_CLASS;
            setTimeout(() => {
                this.buttonClass = PRIMARY_CLASS;
            }, 1500);
            return;
        }
        new CoreApi(DEFAULT_CONFIG).coreTokensViewKey({
            identifier: this.identifier
        }).then((token) => {
            if (!token.key) {
                this.buttonClass = ERROR_CLASS;
                return;
            }
            navigator.clipboard.writeText(token.key).then(() => {
                this.buttonClass = SUCCESS_CLASS;
                setTimeout(() => {
                    this.buttonClass = PRIMARY_CLASS;
                }, 1500);
            });
        });
    }

    render(): TemplateResult {
        return html`<button @click=${() => this.onClick()} class="pf-c-button ${this.buttonClass}">
            <slot></slot>
        </button>`;
    }
}
