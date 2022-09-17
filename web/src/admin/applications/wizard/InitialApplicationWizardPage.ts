import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { convertToSlug } from "@goauthentik/common/utils";
import { KeyUnknown } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { WizardFormPage } from "@goauthentik/elements/wizard/WizardFormPage";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { TemplateResult, html } from "lit";

import { ApplicationRequest, CoreApi, Provider } from "@goauthentik/api";

@customElement("ak-application-wizard-initial")
export class InitialApplicationWizardPage extends WizardFormPage {
    sidebarLabel = () => msg("Application details");

    nextDataCallback = async (data: KeyUnknown): Promise<boolean> => {
        const name = data.name as string;
        let slug = convertToSlug(name || "");
        // Check if an application with the generated slug already exists
        const apps = await new CoreApi(DEFAULT_CONFIG).coreApplicationsList({
            search: slug,
        });
        if (apps.results.filter((app) => app.slug == slug)) {
            slug += "-1";
        }
        this.host.state["slug"] = slug;
        this.host.state["name"] = name;
        this.host.addActionBefore(msg("Create application"), async (): Promise<boolean> => {
            const req: ApplicationRequest = {
                name: name || "",
                slug: slug,
                metaPublisher: data.metaPublisher as string,
                metaDescription: data.metaDescription as string,
            };
            if ("provider" in this.host.state) {
                req.provider = (this.host.state["provider"] as Provider).pk;
            }
            if ("link" in this.host.state) {
                req.metaLaunchUrl = this.host.state["link"] as string;
            }
            this.host.state["app"] = await new CoreApi(DEFAULT_CONFIG).coreApplicationsCreate({
                applicationRequest: req,
            });
            return true;
        });
        return true;
    };

    renderForm(): TemplateResult {
        return html`
            <form class="pf-c-form pf-m-horizontal">
                <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                    <input type="text" value="" class="pf-c-form-control" required />
                    <p class="pf-c-form__helper-text">${msg("Application's display Name.")}</p>
                </ak-form-element-horizontal>
                <ak-form-group ?expanded=${true}>
                    <span slot="header"> ${msg("Additional UI settings")} </span>
                    <div slot="body" class="pf-c-form">
                        <ak-form-element-horizontal
                            label=${msg("Description")}
                            name="metaDescription"
                        >
                            <textarea class="pf-c-form-control"></textarea>
                        </ak-form-element-horizontal>
                        <ak-form-element-horizontal label=${msg("Publisher")} name="metaPublisher">
                            <input type="text" value="" class="pf-c-form-control" />
                        </ak-form-element-horizontal>
                    </div>
                </ak-form-group>
            </form>
        `;
    }
}
