import { Flow, FlowsApi } from "@goauthentik/api";
import { t } from "@lingui/macro";
import { customElement } from "lit/decorators";
import { html, TemplateResult } from "lit";
import { DEFAULT_CONFIG } from "../../api/Config";
import { Form } from "../../elements/forms/Form";
import "../../elements/forms/HorizontalFormElement";

@customElement("ak-flow-import-form")
export class FlowImportForm extends Form<Flow> {
    getSuccessMessage(): string {
        return t`Successfully imported flow.`;
    }

    // eslint-disable-next-line
    send = (data: Flow): Promise<void> => {
        const file = this.getFormFile();
        if (!file) {
            throw new Error("No form data");
        }
        return new FlowsApi(DEFAULT_CONFIG).flowsInstancesImportFlowCreate({
            file: file,
        });
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`Flow`} name="flow">
                <input type="file" value="" class="pf-c-form-control" />
                <p class="pf-c-form__helper-text">${t`Background shown during execution.`}</p>
            </ak-form-element-horizontal>
        </form>`;
    }
}
