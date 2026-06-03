import "#elements/forms/HorizontalFormElement";
import "#components/ak-text-input";

import { DEFAULT_CONFIG } from "#common/api/config";
import { dateTimeLocal } from "#common/temporal";

import { ModelForm } from "#elements/forms/ModelForm";

import { AKLabel } from "#components/ak-label";

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

    protected override renderForm(): TemplateResult {
        const now = new Date();
        const expiringDate = this.instance?.expires
            ? new Date(this.instance.expires.getTime())
            : new Date(now.getTime() + 30 * 60000);

        return html`<ak-text-input
                name="identifier"
                label=${msg("Identifier")}
                required
                value=${ifDefined(this.instance?.identifier)}
                autocomplete="off"
                spellcheck="false"
                input-hint="code"
                placeholder=${msg("Type a unique identifier for this token...")}
            ></ak-text-input>

            <ak-text-input
                name="description"
                label=${msg("Description")}
                value=${ifDefined(this.instance?.description)}
                placeholder=${msg("Type a description for this token...")}
            ></ak-text-input>

            ${this.intent === IntentEnum.AppPassword
                ? html`<ak-form-element-horizontal label=${msg("Expiring")} name="expires">
                      ${AKLabel(
                          {
                              slot: "label",
                              className: "pf-c-form__group-label",
                              htmlFor: "expiration-date-input",
                          },
                          msg("Expires on"),
                      )}

                      <input
                          id="expiration-date-input"
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
