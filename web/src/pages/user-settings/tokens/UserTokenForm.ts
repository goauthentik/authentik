import { CoreApi, Token } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { Form } from "../../../elements/forms/Form";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";

@customElement("ak-user-token-form")
export class UserTokenForm extends Form<Token> {

    @property({attribute: false})
    token?: Token;

    getSuccessMessage(): string {
        if (this.token) {
            return t`Successfully updated token.`;
        } else {
            return t`Successfully created token.`;
        }
    }

    send = (data: Token): Promise<Token> => {
        if (this.token) {
            return new CoreApi(DEFAULT_CONFIG).coreTokensUpdate({
                identifier: this.token.identifier,
                data: data
            });
        } else {
            return new CoreApi(DEFAULT_CONFIG).coreTokensCreate({
                data: data
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${t`Identifier`}
                ?required=${true}
                name="identifier">
                <input type="text" value="${ifDefined(this.token?.identifier)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Description`}
                ?required=${true}
                name="description">
                <input type="text" value="${ifDefined(this.token?.description)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
        </form>`;
    }

}
