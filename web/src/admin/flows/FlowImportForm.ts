import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { SentryIgnoredError } from "@goauthentik/common/errors";
import { Form } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import { Flow, FlowsApi } from "@goauthentik/api";

@customElement("ak-flow-import-form")
export class FlowImportForm extends Form<Flow> {
    getSuccessMessage(): string {
        return t`Successfully imported flow.`;
    }

    // eslint-disable-next-line
    send = (data: Flow): Promise<void> => {
        const file = this.getFormFiles()["flow"];
        if (!file) {
            throw new SentryIgnoredError("No form data");
        }
        return new FlowsApi(DEFAULT_CONFIG).flowsInstancesImportFlowCreate({
            file: file,
        });
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`Flow`} name="flow">
                <input type="file" value="" class="pf-c-form-control" />
                <p class="pf-c-form__helper-text">
                    ${t`.yaml files, which can be found on goauthentik.io and can be exported by authentik.`}
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }
}
