import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, TemplateResult, html } from "lit";
import { property } from "lit/decorators.js";

import AKGlobal from "../../../authentik.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { ApplicationRequest, CoreApi } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../../api/Config";
import "../../../elements/forms/FormGroup";
import "../../../elements/forms/HorizontalFormElement";
import { WizardPage } from "../../../elements/wizard/WizardPage";
import { convertToSlug } from "../../../utils";

@customElement("ak-application-wizard-initial")
export class InitialApplicationWizardPage extends WizardPage {
    static get styles(): CSSResult[] {
        return [PFBase, PFForm, PFFormControl, PFFormControl, AKGlobal, PFRadio];
    }

    @property()
    name?: string;

    sidebarLabel = () => t`Application details`;

    nextCallback = async (): Promise<boolean> => {
        let slug = convertToSlug(this.name || "");
        // Check if an application with the generated slug already exists
        const apps = await new CoreApi(DEFAULT_CONFIG).coreApplicationsList({
            search: slug,
        });
        if (apps.results.filter((app) => app.slug == slug)) {
            slug += "-1";
        }
        this.host.state["slug"] = slug;
        this.host.state["name"] = this.name;
        this.host.addActionBefore(t`Create application`, (): Promise<boolean> => {
            const req: ApplicationRequest = {
                name: this.name || "",
                slug: slug,
            };
            if ("provider" in this.host.state) {
                req.provider = this.host.state["provider"] as number;
            }
            if ("link" in this.host.state) {
                req.metaLaunchUrl = this.host.state["link"] as string;
            }
            return new CoreApi(DEFAULT_CONFIG)
                .coreApplicationsCreate({
                    applicationRequest: req,
                })
                .then(() => {
                    return true;
                });
        });
        return true;
    };

    render(): TemplateResult {
        return html`
            <form class="pf-c-form pf-m-horizontal">
                <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                    <input
                        type="text"
                        value=""
                        class="pf-c-form-control"
                        required
                        @input=${(ev: InputEvent) => {
                            const value = (ev.target as HTMLInputElement).value;
                            this._isValid = value !== "";
                            this.name = value;
                            this.host.requestUpdate();
                        }}
                    />
                    <p class="pf-c-form__helper-text">${t`Application's display Name.`}</p>
                </ak-form-element-horizontal>
                <ak-form-group>
                    <span slot="header"> ${t`Additional UI settings`} </span>
                    <div slot="body" class="pf-c-form">
                        <ak-form-element-horizontal label=${t`Publisher`} name="metaPublisher">
                            <input type="text" value="" class="pf-c-form-control" />
                        </ak-form-element-horizontal>
                        <ak-form-element-horizontal label=${t`Description`} name="metaDescription">
                            <textarea class="pf-c-form-control"></textarea>
                        </ak-form-element-horizontal>
                    </div>
                </ak-form-group>
            </form>
        `;
    }
}
