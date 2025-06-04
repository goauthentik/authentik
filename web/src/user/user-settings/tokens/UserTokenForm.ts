import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { dateTimeLocal } from "@goauthentik/common/temporal";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { CoreApi, IntentEnum, Token } from "@goauthentik/api";

@customElement("ak-user-token-form")
export class UserTokenForm extends ModelForm<Token, string> {
    @property()
    intent: IntentEnum = IntentEnum.Api;

    loadInstance(pk: string): Promise<Token> {
        return new CoreApi(DEFAULT_CONFIG).coreTokensRetrieve({
            identifier: pk,
        });
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated token.")
            : msg("Successfully created token.");
    }

    async send(data: Token): Promise<Token> {
        if (this.instance) {
            data.intent = this.instance.intent;
            return new CoreApi(DEFAULT_CONFIG).coreTokensUpdate({
                identifier: this.instance.identifier,
                tokenRequest: data,
            });
        }
        data.intent = this.intent;
        return new CoreApi(DEFAULT_CONFIG).coreTokensCreate({
            tokenRequest: data,
        });
    }

    renderForm(): TemplateResult {
        const now = new Date();
        const expiringDate = this.instance?.expires
            ? new Date(this.instance.expires.getTime())
            : new Date(now.getTime() + 30 * 60000);

        return html` <ak-form-element-horizontal
                label=${msg("Identifier")}
                ?required=${true}
                name="identifier"
            >
                <input
                    type="text"
                    value="${ifDefined(this.instance?.identifier)}"
                    class="pf-c-form-control pf-m-monospace"
                    autocomplete="off"
                    spellcheck="false"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Description")} name="description">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.description)}"
                    class="pf-c-form-control"
                />
            </ak-form-element-horizontal>
            ${this.intent === IntentEnum.AppPassword
                ? html`<ak-form-element-horizontal label=${msg("Expiring")} name="expires">
                      <input
                          type="datetime-local"
                          value="${dateTimeLocal(expiringDate)}"
                          min="${dateTimeLocal(now)}"
                          class="pf-c-form-control"
                      />
                  </ak-form-element-horizontal>`
                : html``}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-token-form": UserTokenForm;
    }
}
