import { gettext } from "django";
import { CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { Provider } from "authentik-api";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";

import "../../elements/buttons/ModalButton";
import "../../elements/Spinner";
import "../../elements/forms/ModalForm";
import "../../pages/applications/ApplicationForm";

@customElement("ak-provider-related-application")
export class RelatedApplicationButton extends LitElement {

    static get styles(): CSSResult[] {
        return [PFBase, PFButton];
    }

    @property({attribute: false})
    provider?: Provider;

    render(): TemplateResult {
        if (this.provider?.assignedApplicationSlug) {
            return html`<a href="#/core/applications/${this.provider.assignedApplicationSlug}">
                ${this.provider.assignedApplicationName}
            </a>`;
        }
        return html`<ak-forms-modal>
            <span slot="submit">
                ${gettext("Create")}
            </span>
            <span slot="header">
                ${gettext("Create Application")}
            </span>
            <ak-application-form slot="form" .provider=${this.provider?.pk}>
            </ak-application-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">
                ${gettext("Create")}
            </button>
        </ak-forms-modal>`;
    }

}
