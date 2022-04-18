import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, TemplateResult, html } from "lit";
import { state } from "lit/decorators.js";

import AKGlobal from "../../../authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    FlowDesignationEnum,
    FlowsApi,
    ProvidersApi,
    ProxyProviderRequest,
} from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../../api/Config";
import "../../../elements/forms/HorizontalFormElement";
import { WizardPage } from "../../../elements/wizard/WizardPage";

@customElement("ak-application-wizard-type-proxy")
export class TypeProxyApplicationWizardPage extends WizardPage {
    static get styles(): CSSResult[] {
        return [PFBase, PFForm, PFFormControl, PFFormControl, PFButton, AKGlobal, PFRadio];
    }

    sidebarLabel = () => t`Proxy details`;

    @state()
    externalHost?: string;

    nextCallback = async (): Promise<boolean> => {
        let name = this.host.state["name"] as string;
        // Check if a provider with the name already exists
        const providers = await new ProvidersApi(DEFAULT_CONFIG).providersAllList({
            search: name,
        });
        if (providers.results.filter((provider) => provider.name == name)) {
            name += "-1";
        }
        this.host.addActionBefore(t`Create provider`, async (): Promise<boolean> => {
            // Get all flows and default to the implicit authorization
            const flows = await new FlowsApi(DEFAULT_CONFIG).flowsInstancesList({
                designation: FlowDesignationEnum.Authorization,
                ordering: "slug",
            });
            const req: ProxyProviderRequest = {
                name: name,
                authorizationFlow: flows.results[0].pk,
                externalHost: this.externalHost || "",
            };
            return new ProvidersApi(DEFAULT_CONFIG)
                .providersProxyCreate({
                    proxyProviderRequest: req,
                })
                .then((prov) => {
                    this.host.state["provider"] = prov.pk;
                    return true;
                });
        });
        return true;
    };

    render(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`External domain`} ?required=${true}>
                <input
                    type="text"
                    value=""
                    class="pf-c-form-control"
                    required
                    @input=${(ev: InputEvent) => {
                        const value = (ev.target as HTMLInputElement).value;
                        this._isValid = value !== "";
                        this.externalHost = value;
                        this.host.requestUpdate();
                    }}
                />
                <p class="pf-c-form__helper-text">
                    ${t`External domain you will be accessing the domain from.`}
                </p>
            </ak-form-element-horizontal>
        </form> `;
    }
}
