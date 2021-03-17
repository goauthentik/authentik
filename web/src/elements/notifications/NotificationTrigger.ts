import { CSSResult, customElement, html, LitElement, TemplateResult } from "lit-element";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";

@customElement("ak-notification-trigger")
export class NotificationRule extends LitElement {

    static get styles(): CSSResult[] {
        return [PFBase, PFDropdown];
    }

    constructor() {
        super();
        this.addEventListener("click", () => {
            this.dispatchEvent(
                new CustomEvent("ak-notification-toggle", {
                    bubbles: true,
                    composed: true,
                })
            );
        });
    }

    render(): TemplateResult {
        // TODO: Show icon with red dot when unread notifications exist
        return html`<i class="fas fa-bell pf-c-dropdown__toggle-icon" aria-hidden="true"></i>`;
    }

}
