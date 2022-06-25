import { DEFAULT_CONFIG } from "@goauthentik/web/api/Config";
import { SentryIgnoredError } from "@goauthentik/web/common/errors";
import { Form } from "@goauthentik/web/elements/forms/Form";
import "@goauthentik/web/elements/forms/HorizontalFormElement";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import {
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    ProvidersApi,
    SAMLProvider,
} from "@goauthentik/api";

@customElement("ak-provider-saml-import-form")
export class SAMLProviderImportForm extends Form<SAMLProvider> {
    getSuccessMessage(): string {
        return t`Successfully imported provider.`;
    }

    // eslint-disable-next-line
    send = (data: SAMLProvider): Promise<void> => {
        const file = this.getFormFiles()["metadata"];
        if (!file) {
            throw new SentryIgnoredError("No form data");
        }
        return new ProvidersApi(DEFAULT_CONFIG).providersSamlImportMetadataCreate({
            file: file,
            name: data.name,
            authorizationFlow: data.authorizationFlow,
        });
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input type="text" class="pf-c-form-control" required />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Authorization flow`}
                ?required=${true}
                name="authorizationFlow"
            >
                <select class="pf-c-form-control">
                    ${until(
                        new FlowsApi(DEFAULT_CONFIG)
                            .flowsInstancesList({
                                ordering: "slug",
                                designation: FlowsInstancesListDesignationEnum.Authorization,
                            })
                            .then((flows) => {
                                return flows.results.map((flow) => {
                                    return html`<option value=${flow.slug}>
                                        ${flow.name} (${flow.slug})
                                    </option>`;
                                });
                            }),
                        html`<option>${t`Loading...`}</option>`,
                    )}
                </select>
                <p class="pf-c-form__helper-text">
                    ${t`Flow used when authorizing this provider.`}
                </p>
            </ak-form-element-horizontal>

            <ak-form-element-horizontal label=${t`Metadata`} name="metadata">
                <input type="file" value="" class="pf-c-form-control" />
            </ak-form-element-horizontal>
        </form>`;
    }
}
