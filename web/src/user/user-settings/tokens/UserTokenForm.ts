import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";
import { dateTimeLocal } from "#common/temporal";

import { ModelForm } from "#elements/forms/ModelForm";

import { CoreApi, IntentEnum, Token } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

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
                required
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
                : nothing}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-token-form": UserTokenForm;
    }
}
