import "#components/ak-text-input";

import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";
import { SlottedTemplateResult } from "#elements/types";

import { RequestRule, RequestsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { ifDefined } from "lit-html/directives/if-defined.js";
import { customElement } from "lit/decorators.js";

@customElement("ak-request-rule-form")
export class RequestRuleForm extends ModelForm<RequestRule, string> {
    public static override verboseName = msg("Request Rule");
    public static override verboseNamePlural = msg("Request Rules");

    protected async loadInstance(pk: string): Promise<RequestRule> {
        return aki(RequestsApi).requestsRulesRetrieve({ uuid: pk });
    }

    protected override async send(data: RequestRule): Promise<RequestRule> {
        if (this.instance?.uuid) {
            return aki(RequestsApi).requestsRulesUpdate({
                uuid: this.instance.uuid,
                requestRuleRequest: data,
            });
        }

        return aki(RequestsApi).requestsRulesCreate({
            requestRuleRequest: data,
        });
    }

    protected renderForm(): SlottedTemplateResult {
        return html`<ak-text-input
            label=${msg("Rule Name")}
            name="name"
            required
            value="${ifDefined(this.instance?.name)}"
            placeholder=${msg("Type a name for this request rule...")}
        ></ak-text-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-request-rule-form": RequestRuleForm;
    }
}
