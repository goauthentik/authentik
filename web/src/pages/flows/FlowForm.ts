import { Flow, FlowDesignationEnum, FlowsApi } from "authentik-api";
import { gettext } from "django";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { Form } from "../../elements/forms/Form";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/forms/HorizontalFormElement";

@customElement("ak-flow-form")
export class FlowForm extends Form<Flow> {

    @property({attribute: false})
    flow?: Flow;

    getSuccessMessage(): string {
        if (this.flow) {
            return gettext("Successfully updated flow.");
        } else {
            return gettext("Successfully created flow.");
        }
    }

    send = (data: Flow): Promise<void | Flow> => {
        let writeOp: Promise<Flow>;
        if (this.flow) {
            writeOp = new FlowsApi(DEFAULT_CONFIG).flowsInstancesUpdate({
                slug: this.flow.slug,
                data: data
            });
        } else {
            writeOp = new FlowsApi(DEFAULT_CONFIG).flowsInstancesCreate({
                data: data
            });
        }
        const background = this.getFormFile();
        if (background) {
            return writeOp.then(flow => {
                return new FlowsApi(DEFAULT_CONFIG).flowsInstancesSetBackground({
                    slug: flow.slug,
                    file: background
                });
            });
        }
        return writeOp;
    };

    renderDesignations(): TemplateResult {
        return html`
            <option value=${FlowDesignationEnum.Authentication} ?selected=${this.flow?.designation === FlowDesignationEnum.Authentication}>
                ${gettext("Authentication")}
            </option>
            <option value=${FlowDesignationEnum.Authorization} ?selected=${this.flow?.designation === FlowDesignationEnum.Authorization}>
                ${gettext("Authorization")}
            </option>
            <option value=${FlowDesignationEnum.Enrollment} ?selected=${this.flow?.designation === FlowDesignationEnum.Enrollment}>
                ${gettext("Enrollment")}
            </option>
            <option value=${FlowDesignationEnum.Invalidation} ?selected=${this.flow?.designation === FlowDesignationEnum.Invalidation}>
                ${gettext("Invalidation")}
            </option>
            <option value=${FlowDesignationEnum.Recovery} ?selected=${this.flow?.designation === FlowDesignationEnum.Recovery}>
                ${gettext("Recovery")}
            </option>
            <option value=${FlowDesignationEnum.StageConfiguration} ?selected=${this.flow?.designation === FlowDesignationEnum.StageConfiguration}>
                ${gettext("Stage Configuration")}
            </option>
            <option value=${FlowDesignationEnum.Unenrollment} ?selected=${this.flow?.designation === FlowDesignationEnum.Unenrollment}>
                ${gettext("Unenrollment")}
            </option>
        `;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${gettext("Name")}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.flow?.name)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Title")}
                ?required=${true}
                name="title">
                <input type="text" value="${ifDefined(this.flow?.title)}" class="pf-c-form-control" required>
                <p class="pf-c-form__helper-text">${gettext("Shown as the Title in Flow pages.")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Name")}
                ?required=${true}
                name="slug">
                <input type="text" value="${ifDefined(this.flow?.slug)}" class="pf-c-form-control" required>
                <p class="pf-c-form__helper-text">${gettext("Visible in the URL.")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Designation")}
                ?required=${true}
                name="designation">
                <select class="pf-c-form-control">
                    <option value="" ?selected=${this.flow?.designation === undefined}>---------</option>
                    ${this.renderDesignations()}
                </select>
                <p class="pf-c-form__helper-text">${gettext("Decides what this Flow is used for. For example, the Authentication flow is redirect to when an un-authenticated user visits authentik.")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Background")}
                name="background">
                <input type="file" value="${ifDefined(this.flow?.background)}" class="pf-c-form-control">
                <p class="pf-c-form__helper-text">${gettext("Background shown during execution.")}</p>
            </ak-form-element-horizontal>
        </form>`;
    }

}
