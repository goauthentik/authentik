import { Flow, FlowDesignationEnum, PolicyEngineMode, FlowsApi, CapabilitiesEnum } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { config, DEFAULT_CONFIG } from "../../api/Config";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/forms/HorizontalFormElement";
import { ModelForm } from "../../elements/forms/ModelForm";
import { until } from "lit-html/directives/until";
import { first } from "../../utils";

@customElement("ak-flow-form")
export class FlowForm extends ModelForm<Flow, string> {

    loadInstance(pk: string): Promise<Flow> {
        return new FlowsApi(DEFAULT_CONFIG).flowsInstancesRetrieve({
            slug: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated flow.`;
        } else {
            return t`Successfully created flow.`;
        }
    }

    send = (data: Flow): Promise<void | Flow> => {
        let writeOp: Promise<Flow>;
        if (this.instance) {
            writeOp = new FlowsApi(DEFAULT_CONFIG).flowsInstancesUpdate({
                slug: this.instance.slug,
                flowRequest: data
            });
        } else {
            writeOp = new FlowsApi(DEFAULT_CONFIG).flowsInstancesCreate({
                flowRequest: data
            });
        }
        return config().then((c) => {
            if (c.capabilities.includes(CapabilitiesEnum.SaveMedia)) {
                const icon = this.getFormFile();
                if (icon) {
                    return writeOp.then(app => {
                        return new FlowsApi(DEFAULT_CONFIG).flowsInstancesSetBackgroundCreate({
                            slug: app.slug,
                            file: icon
                        });
                    });
                }
            } else {
                return writeOp.then(app => {
                    return new FlowsApi(DEFAULT_CONFIG).flowsInstancesSetBackgroundUrlCreate({
                        slug: app.slug,
                        setIconURLRequest: {
                            url: data.background || "",
                        }
                    });
                });
            }
        });
    };

    renderDesignations(): TemplateResult {
        return html`
            <option value=${FlowDesignationEnum.Authentication} ?selected=${this.instance?.designation === FlowDesignationEnum.Authentication}>
                ${t`Authentication`}
            </option>
            <option value=${FlowDesignationEnum.Authorization} ?selected=${this.instance?.designation === FlowDesignationEnum.Authorization}>
                ${t`Authorization`}
            </option>
            <option value=${FlowDesignationEnum.Enrollment} ?selected=${this.instance?.designation === FlowDesignationEnum.Enrollment}>
                ${t`Enrollment`}
            </option>
            <option value=${FlowDesignationEnum.Invalidation} ?selected=${this.instance?.designation === FlowDesignationEnum.Invalidation}>
                ${t`Invalidation`}
            </option>
            <option value=${FlowDesignationEnum.Recovery} ?selected=${this.instance?.designation === FlowDesignationEnum.Recovery}>
                ${t`Recovery`}
            </option>
            <option value=${FlowDesignationEnum.StageConfiguration} ?selected=${this.instance?.designation === FlowDesignationEnum.StageConfiguration}>
                ${t`Stage Configuration`}
            </option>
            <option value=${FlowDesignationEnum.Unenrollment} ?selected=${this.instance?.designation === FlowDesignationEnum.Unenrollment}>
                ${t`Unenrollment`}
            </option>
        `;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${t`Name`}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.instance?.name)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Title`}
                ?required=${true}
                name="title">
                <input type="text" value="${ifDefined(this.instance?.title)}" class="pf-c-form-control" required>
                <p class="pf-c-form__helper-text">${t`Shown as the Title in Flow pages.`}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Slug`}
                ?required=${true}
                name="slug">
                <input type="text" value="${ifDefined(this.instance?.slug)}" class="pf-c-form-control" required>
                <p class="pf-c-form__helper-text">${t`Visible in the URL.`}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Policy engine mode`}
                ?required=${true}
                name="policyEngineMode">
                <select class="pf-c-form-control">
                    <option value=${PolicyEngineMode.Any} ?selected=${this.instance?.policyEngineMode === PolicyEngineMode.Any}>
                        ${t`ANY, any policy must match to grant access.`}
                    </option>
                    <option value=${PolicyEngineMode.All} ?selected=${this.instance?.policyEngineMode === PolicyEngineMode.All}>
                        ${t`ALL, all policies must match to grant access.`}
                    </option>
                </select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Designation`}
                ?required=${true}
                name="designation">
                <select class="pf-c-form-control">
                    <option value="" ?selected=${this.instance?.designation === undefined}>---------</option>
                    ${this.renderDesignations()}
                </select>
                <p class="pf-c-form__helper-text">${t`Decides what this Flow is used for. For example, the Authentication flow is redirect to when an un-authenticated user visits authentik.`}</p>
            </ak-form-element-horizontal>
            ${until(config().then((c) => {
                let type = "text";
                if (c.capabilities.includes(CapabilitiesEnum.SaveMedia)) {
                    type = "file";
                }
                return html`<ak-form-element-horizontal
                    label=${t`Background`}
                    name="background">
                    <!-- @ts-ignore -->
                    <input type=${type} value="${first(this.instance?.background, "/static/dist/assets/images/flow_background.jpg")}" class="pf-c-form-control">
                    <p class="pf-c-form__helper-text">${t`Background shown during execution.`}</p>
                </ak-form-element-horizontal>`;
            }))}
        </form>`;
    }

}
