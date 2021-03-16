import { gettext } from "django";
import { customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { Provider } from "authentik-api";
import { AdminURLManager } from "../../api/legacy";

import "../../elements/buttons/ModalButton";
import "../../elements/Spinner";

@customElement("ak-provider-related-application")
export class RelatedApplicationButton extends LitElement {

    @property({attribute: false})
    provider?: Provider;

    render(): TemplateResult {
        if (this.provider?.assignedApplicationSlug) {
            return html`<a href="#/core/applications/${this.provider.assignedApplicationSlug}">
                ${this.provider.assignedApplicationName}
            </a>`;
        }
        return html`<ak-modal-button href=${AdminURLManager.applications(`create/?provider=${this.provider ? this.provider.pk : ""}`)}>
                <ak-spinner-button slot="trigger" class="pf-m-primary">
                    ${gettext("Create")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>`;
    }

}
