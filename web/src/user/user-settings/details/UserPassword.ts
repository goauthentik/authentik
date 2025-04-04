import { createNextSearchParams } from "@goauthentik/admin/flows/utils";
import { globalAK } from "@goauthentik/common/global";
import { AKElement } from "@goauthentik/elements/Base";
import { formatInterfaceRoute } from "@goauthentik/elements/router/utils";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { CSSResult } from "lit";
import { customElement } from "lit/decorators.js";
import { property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-user-settings-password")
export class UserSettingsPassword extends AKElement {
    @property()
    configureUrl?: string;

    static get styles(): CSSResult[] {
        return [PFBase, PFCard, PFButton, PFForm, PFFormControl];
    }

    render(): TemplateResult {
        // TODO: The use `ifDefined` below seems odd. Is it necessary?
        const searchParams = createNextSearchParams(
            globalAK().api.relBase +
                formatInterfaceRoute("user", "settings", {
                    page: "details",
                }),
        );

        // For this stage we don't need to check for a configureFlow,
        // as the stage won't return any UI Elements if no configureFlow is set.
        return html`<div class="pf-c-card">
            <div class="pf-c-card__title">${msg("Change your password")}</div>
            <div class="pf-c-card__body">
                <a
                    href="${ifDefined(this.configureUrl)}?${searchParams.toString()}"
                    class="pf-c-button pf-m-primary"
                >
                    ${msg("Change password")}
                </a>
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-settings-password": UserSettingsPassword;
    }
}
