import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { t } from "@lingui/macro";

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
        if (this.instance) {
            return t`Successfully updated token.`;
        } else {
            return t`Successfully created token.`;
        }
    }

    send = (data: Token): Promise<Token> => {
        if (this.instance) {
            return new CoreApi(DEFAULT_CONFIG).coreTokensUpdate({
                identifier: this.instance.identifier,
                tokenRequest: data,
            });
        } else {
            data.intent = this.intent;
            return new CoreApi(DEFAULT_CONFIG).coreTokensCreate({
                tokenRequest: data,
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`Identifier`} ?required=${true} name="identifier">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.identifier)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Description`} name="description">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.description)}"
                    class="pf-c-form-control"
                />
            </ak-form-element-horizontal>
        </form>`;
    }
}
