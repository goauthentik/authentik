import { CoreApi, Application, ProvidersApi, Provider } from "authentik-api";
import { gettext } from "django";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { Form } from "../../elements/forms/Form";
import { until } from "lit-html/directives/until";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/forms/HorizontalFormElement";
import "../../elements/CodeMirror";

@customElement("ak-application-form")
export class ApplicationForm extends Form<Application> {

    @property({ attribute: false })
    application?: Application;

    @property({ attribute: false })
    provider?: number;

    getSuccessMessage(): string {
        if (this.application) {
            return gettext("Successfully updated application.");
        } else {
            return gettext("Successfully created application.");
        }
    }

    send = (data: Application): Promise<Application> => {
        let writeOp: Promise<Application>;
        if (this.application) {
            writeOp = new CoreApi(DEFAULT_CONFIG).coreApplicationsUpdate({
                slug: this.application.slug,
                data: data
            });
        } else {
            writeOp = new CoreApi(DEFAULT_CONFIG).coreApplicationsCreate({
                data: data
            });
        }
        const icon = this.getFormFile();
        if (icon) {
            return writeOp.then(app => {
                return new CoreApi(DEFAULT_CONFIG).coreApplicationsSetIcon({
                    slug: app.slug,
                    file: icon
                });
            });
        }
        return writeOp;
    };

    groupProviders(providers: Provider[]): TemplateResult {
        const m = new Map<string, Provider[]>();
        providers.forEach(p => {
            if (!m.has(p.verboseName || "")) {
                m.set(p.verboseName || "", []);
            }
            const tProviders = m.get(p.verboseName || "") || [];
            tProviders.push(p);
        });
        return html`
            ${Array.from(m).map(([group, providers]) => {
                return html`<optgroup label=${group}>
                    ${providers.map(p => {
                        const selected = (this.application?.provider?.pk === p.pk) || (this.provider === p.pk)
                        return html`<option ?selected=${selected} value=${ifDefined(p.pk)}>${p.name}</option>`;
                    })}
                </optgroup>`;
            })}
        `;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${gettext("Name")}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.application?.name)}" class="pf-c-form-control" required>
                <p class="pf-c-form__helper-text">${gettext("Application's display Name.")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Slug")}
                ?required=${true}
                name="slug">
                <input type="text" value="${ifDefined(this.application?.slug)}" class="pf-c-form-control" required>
                <p class="pf-c-form__helper-text">${gettext("Internal application name, used in URLs.")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Provider")}
                name="parent">
                <select class="pf-c-form-control">
                    <option value="" ?selected=${this.application?.provider === undefined}>---------</option>
                    ${until(new ProvidersApi(DEFAULT_CONFIG).providersAllList({}).then(providers => {
                        return this.groupProviders(providers.results);
                    }), html``)}
                </select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Launch URL")}
                name="launchUrl">
                <input type="text" value="${ifDefined(this.application?.launchUrl)}" class="pf-c-form-control">
                <p class="pf-c-form__helper-text">${gettext("If left empty, authentik will try to extract the launch URL based on the selected provider.")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Icon")}
                name="metaIcon">
                <input type="file" value="${ifDefined(this.application?.metaIcon)}" class="pf-c-form-control">
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Description")}
                name="metaDescription">
                <textarea class="pf-c-form-control">${ifDefined(this.application?.metaDescription)}</textarea>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Publisher")}
                name="metaPublisher">
                <input type="text" value="${ifDefined(this.application?.metaPublisher)}" class="pf-c-form-control">
            </ak-form-element-horizontal>
        </form>`;
    }

}
