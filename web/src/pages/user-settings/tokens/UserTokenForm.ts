import { CoreApi, Token } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";
import { ModelForm } from "../../../elements/forms/ModelForm";

@customElement("ak-user-token-form")
export class UserTokenForm extends ModelForm<Token, string> {

    loadInstance(pk: string): Promise<Token> {
        return new CoreApi(DEFAULT_CONFIG).coreTokensRetrieve({
            identifier: pk
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
                tokenRequest: data
            });
        } else {
            return new CoreApi(DEFAULT_CONFIG).coreTokensCreate({
                tokenRequest: data
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${t`Identifier`}
                ?required=${true}
                name="identifier">
                <input type="text" value="${ifDefined(this.instance?.identifier)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Description`}
                name="description">
                <input type="text" value="${ifDefined(this.instance?.description)}" class="pf-c-form-control">
            </ak-form-element-horizontal>
        </form>`;
    }

}
