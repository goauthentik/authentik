import { CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFLabel from "@patternfly/patternfly/components/Label/label.css";
import AKGlobal from "../authentik.css";

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

    @property()
    text?: string;

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
                        class="fas ${this.text ? "fa-fw" : ""} ${this.icon ||
                        this.getDefaultIcon()}"
                        aria-hidden="true"
                    ></i>
                </span>
                ${this.text || ""}
            </span>
        </span>`;
    }
}
