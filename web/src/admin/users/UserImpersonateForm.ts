import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { ServerContext } from "@goauthentik/common/server-context";
import "@goauthentik/components/ak-text-input";
import { Form } from "@goauthentik/elements/forms/Form";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { CoreApi, ImpersonationRequest } from "@goauthentik/api";

@customElement("ak-user-impersonate-form")
export class UserImpersonateForm extends Form<ImpersonationRequest> {
    @property({ type: Number })
    instancePk?: number;

    async send(data: ImpersonationRequest): Promise<void> {
        return new CoreApi(DEFAULT_CONFIG)
            .coreUsersImpersonateCreate({
                id: this.instancePk || 0,
                impersonationRequest: data,
            })
            .then(() => {
                window.location.href = ServerContext.baseURL;
            });
    }

    renderForm(): TemplateResult {
        return html`<ak-text-input
            name="reason"
            label=${msg("Reason")}
            help=${msg("Reason for impersonating the user")}
        ></ak-text-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-impersonate-form": UserImpersonateForm;
    }
}
