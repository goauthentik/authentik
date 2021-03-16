import { CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import PFEmptyState from "@patternfly/patternfly/components/EmptyState/empty-state.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import FA from "@fortawesome/fontawesome-free/css/fontawesome.css";

@customElement("ak-empty-state")
export class EmptyState extends LitElement {

    @property({type: String})
    icon = "";

    @property()
    header?: string;

    static get styles(): CSSResult[] {
        return [PFEmptyState, PFBase, FA];
    }

    render(): TemplateResult {
        return html`<div class="pf-c-empty-state">
            <div class="pf-c-empty-state__content">
                <i class="pf-icon fa ${this.icon || "fa-question-circle"} pf-c-empty-state__icon" aria-hidden="true"></i>
                <h1 class="pf-c-title pf-m-lg">
                    ${this.header}
                </h1>
                <div class="pf-c-empty-state__body">
                    <slot name="body"></slot>
                </div>
                <div class="pf-c-empty-state__primary">
                    <slot name="primary"></slot>
                </div>
            </div>
        </div>`;
    }

}
