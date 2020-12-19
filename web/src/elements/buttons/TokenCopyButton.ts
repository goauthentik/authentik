import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
// @ts-ignore
import GlobalsStyle from "@patternfly/patternfly/base/patternfly-globals.css";
// @ts-ignore
import ButtonStyle from "@patternfly/patternfly/components/Button/button.css";
import { tokenByIdentifier } from "../../api/Tokens";
import { ColorStyles, ERROR_CLASS, PRIMARY_CLASS, SUCCESS_CLASS } from "../../constants";

@customElement("ak-token-copy-button")
export class TokenCopyButton extends LitElement {
    @property()
    identifier?: string;

    @property()
    buttonClass: string = PRIMARY_CLASS;

    static get styles(): CSSResult[] {
        return [
            GlobalsStyle,
            ButtonStyle,
            ColorStyles,
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
        tokenByIdentifier(this.identifier).then((token) => {
            navigator.clipboard.writeText(token).then(() => {
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
