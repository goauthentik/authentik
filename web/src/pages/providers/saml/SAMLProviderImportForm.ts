import { FlowDesignationEnum, FlowsApi, ProvidersApi, SAMLProvider } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { ifDefined } from "lit-html/directives/if-defined";
import { until } from "lit-html/directives/until";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { Form } from "../../../elements/forms/Form";
import "../../../elements/forms/HorizontalFormElement";

@customElement("ak-provider-saml-import-form")
export class SAMLProviderImportForm extends Form<SAMLProvider> {

    getSuccessMessage(): string {
        return t`Successfully imported provider.`;
    }

    // eslint-disable-next-line
    send = (data: SAMLProvider): Promise<void> => {
        const file = this.getFormFile();
        if (!file) {
            throw new Error("No form data");
        }
        return new ProvidersApi(DEFAULT_CONFIG).providersSamlImportMetadata({
            file: file,
            name: data.name,
            authorizationFlow: data.authorizationFlow,
        });
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${t`Name`}
                ?required=${true}
                name="name">
                <input type="text" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Authorization flow`}
                ?required=${true}
                name="authorizationFlow">
                <select class="pf-c-form-control">
                    ${until(new FlowsApi(DEFAULT_CONFIG).flowsInstancesList({
                        ordering: "pk",
                        designation: FlowDesignationEnum.Authorization,
                    }).then(flows => {
                        return flows.results.map(flow => {
                            return html`<option value=${ifDefined(flow.pk)}>${flow.name} (${flow.slug})</option>`;
                        });
                    }), html`<option>${t`Loading...`}</option>`)}
                </select>
                <p class="pf-c-form__helper-text">${t`Flow used when authorizing this provider.`}</p>
            </ak-form-element-horizontal>

            <ak-form-element-horizontal
                label=${t`Metadata`}
                name="flow">
                <input type="file" value="" class="pf-c-form-control">
            </ak-form-element-horizontal>
        </form>`;
    }

}
