import { CSSResult, LitElement, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import AKGlobal from "@goauthentik/web/authentik.css";
import PFLabel from "@patternfly/patternfly/components/Label/label.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export enum PFColor {
    Green = "pf-m-green",
    Orange = "pf-m-orange",
    Red = "pf-m-red",
    Grey = "",
}

@customElement("ak-label")
export class Label extends LitElement {
    @property()
    color: PFColor = PFColor.Grey;

    @property()
    icon?: string;

    static get styles(): CSSResult[] {
        return [PFBase, PFLabel, AKGlobal];
    }

    getDefaultIcon(): string {
        switch (this.color) {
            case PFColor.Green:
                return "fa-check";
            case PFColor.Orange:
                return "fa-exclamation-triangle";
            case PFColor.Red:
                return "fa-times";
            case PFColor.Grey:
                return "fa-question-circle";
            default:
                return "";
        }
    }

    render(): TemplateResult {
        return html`<span class="pf-c-label ${this.color}">
            <span class="pf-c-label__content">
                <span class="pf-c-label__icon">
                    <i
                        class="fas fa-fw ${this.icon || this.getDefaultIcon()}"
                        aria-hidden="true"
                    ></i>
                </span>
                <slot></slot>
            </span>
        </span>`;
    }
}
