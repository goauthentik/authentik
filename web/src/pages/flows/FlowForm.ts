import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import {
    CapabilitiesEnum,
    Flow,
    FlowDesignationEnum,
    FlowsApi,
    LayoutEnum,
    PolicyEngineMode,
} from "@goauthentik/api";

import { DEFAULT_CONFIG, config } from "../../api/Config";
import "../../elements/forms/HorizontalFormElement";
import { ModelForm } from "../../elements/forms/ModelForm";
import { first } from "../../utils";
import { DesignationToLabel, LayoutToLabel } from "./utils";

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

    @property({ type: Boolean })
    clearBackground = false;

    send = async (data: Flow): Promise<void | Flow> => {
        let flow: Flow;
        if (this.instance) {
            flow = await new FlowsApi(DEFAULT_CONFIG).flowsInstancesUpdate({
                slug: this.instance.slug,
                flowRequest: data,
            });
        } else {
            flow = await new FlowsApi(DEFAULT_CONFIG).flowsInstancesCreate({
                flowRequest: data,
            });
        }
        const c = await config();
        if (c.capabilities.includes(CapabilitiesEnum.SaveMedia)) {
            const icon = this.getFormFile();
            if (icon || this.clearBackground) {
                await new FlowsApi(DEFAULT_CONFIG).flowsInstancesSetBackgroundCreate({
                    slug: flow.slug,
                    file: icon,
                    clear: this.clearBackground,
                });
            }
        } else {
            await new FlowsApi(DEFAULT_CONFIG).flowsInstancesSetBackgroundUrlCreate({
                slug: flow.slug,
                filePathRequest: {
                    url: data.background || "",
                },
            });
        }
        return flow;
    };

    renderDesignations(): TemplateResult {
        return html`
            <option
                value=${FlowDesignationEnum.Authentication}
                ?selected=${this.instance?.designation === FlowDesignationEnum.Authentication}
            >
                ${DesignationToLabel(FlowDesignationEnum.Authentication)}
            </option>
            <option
                value=${FlowDesignationEnum.Authorization}
                ?selected=${this.instance?.designation === FlowDesignationEnum.Authorization}
            >
                ${DesignationToLabel(FlowDesignationEnum.Authorization)}
            </option>
            <option
                value=${FlowDesignationEnum.Enrollment}
                ?selected=${this.instance?.designation === FlowDesignationEnum.Enrollment}
            >
                ${DesignationToLabel(FlowDesignationEnum.Enrollment)}
            </option>
            <option
                value=${FlowDesignationEnum.Invalidation}
                ?selected=${this.instance?.designation === FlowDesignationEnum.Invalidation}
            >
                ${DesignationToLabel(FlowDesignationEnum.Invalidation)}
            </option>
            <option
                value=${FlowDesignationEnum.Recovery}
                ?selected=${this.instance?.designation === FlowDesignationEnum.Recovery}
            >
                ${DesignationToLabel(FlowDesignationEnum.Recovery)}
            </option>
            <option
                value=${FlowDesignationEnum.StageConfiguration}
                ?selected=${this.instance?.designation === FlowDesignationEnum.StageConfiguration}
            >
                ${DesignationToLabel(FlowDesignationEnum.StageConfiguration)}
            </option>
            <option
                value=${FlowDesignationEnum.Unenrollment}
                ?selected=${this.instance?.designation === FlowDesignationEnum.Unenrollment}
            >
                ${DesignationToLabel(FlowDesignationEnum.Unenrollment)}
            </option>
        `;
    }

    renderLayout(): TemplateResult {
        return html`
            <option
                value=${LayoutEnum.Stacked}
                ?selected=${this.instance?.layout === LayoutEnum.Stacked}
            >
                ${LayoutToLabel(LayoutEnum.Stacked)}
            </option>
            <option
                value=${LayoutEnum.ContentLeft}
                ?selected=${this.instance?.layout === LayoutEnum.ContentLeft}
            >
                ${LayoutToLabel(LayoutEnum.ContentLeft)}
            </option>
            <option
                value=${LayoutEnum.ContentRight}
                ?selected=${this.instance?.layout === LayoutEnum.ContentRight}
            >
                ${LayoutToLabel(LayoutEnum.ContentRight)}
            </option>
            <option
                value=${LayoutEnum.SidebarLeft}
                ?selected=${this.instance?.layout === LayoutEnum.SidebarLeft}
            >
                ${LayoutToLabel(LayoutEnum.SidebarLeft)}
            </option>
            <option
                value=${LayoutEnum.SidebarRight}
                ?selected=${this.instance?.layout === LayoutEnum.SidebarRight}
            >
                ${LayoutToLabel(LayoutEnum.SidebarRight)}
            </option>
        `;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Title`} ?required=${true} name="title">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.title)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">${t`Shown as the Title in Flow pages.`}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Slug`} ?required=${true} name="slug">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.slug)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">${t`Visible in the URL.`}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Policy engine mode`}
                ?required=${true}
                name="policyEngineMode"
            >
                <select class="pf-c-form-control">
                    <option
                        value=${PolicyEngineMode.Any}
                        ?selected=${this.instance?.policyEngineMode === PolicyEngineMode.Any}
                    >
                        ${t`ANY, any policy must match to grant access.`}
                    </option>
                    <option
                        value=${PolicyEngineMode.All}
                        ?selected=${this.instance?.policyEngineMode === PolicyEngineMode.All}
                    >
                        ${t`ALL, all policies must match to grant access.`}
                    </option>
                </select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Designation`}
                ?required=${true}
                name="designation"
            >
                <select class="pf-c-form-control">
                    <option value="" ?selected=${this.instance?.designation === undefined}>
                        ---------
                    </option>
                    ${this.renderDesignations()}
                </select>
                <p class="pf-c-form__helper-text">
                    ${t`Decides what this Flow is used for. For example, the Authentication flow is redirect to when an un-authenticated user visits authentik.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Layout`} ?required=${true} name="layout">
                <select class="pf-c-form-control">
                    ${this.renderLayout()}
                </select>
            </ak-form-element-horizontal>
            ${until(
                config().then((c) => {
                    if (c.capabilities.includes(CapabilitiesEnum.SaveMedia)) {
                        return html`<ak-form-element-horizontal
                                label=${t`Background`}
                                name="background"
                            >
                                <input type="file" value="" class="pf-c-form-control" />
                                ${this.instance?.background
                                    ? html`
                                          <p class="pf-c-form__helper-text">
                                              ${t`Currently set to:`} ${this.instance?.background}
                                          </p>
                                      `
                                    : html``}
                                <p class="pf-c-form__helper-text">
                                    ${t`Background shown during execution.`}
                                </p>
                            </ak-form-element-horizontal>
                            ${this.instance?.background
                                ? html`
                                      <ak-form-element-horizontal>
                                          <div class="pf-c-check">
                                              <input
                                                  type="checkbox"
                                                  class="pf-c-check__input"
                                                  @change=${(ev: Event) => {
                                                      const target = ev.target as HTMLInputElement;
                                                      this.clearBackground = target.checked;
                                                  }}
                                              />
                                              <label class="pf-c-check__label">
                                                  ${t`Clear background image`}
                                              </label>
                                          </div>
                                          <p class="pf-c-form__helper-text">
                                              ${t`Delete currently set background image.`}
                                          </p>
                                      </ak-form-element-horizontal>
                                  `
                                : html``}`;
                    }
                    return html`<ak-form-element-horizontal
                        label=${t`Background`}
                        name="background"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.background, "")}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Background shown during execution.`}
                        </p>
                    </ak-form-element-horizontal>`;
                }),
            )}
            <ak-form-element-horizontal name="compatibilityMode">
                <div class="pf-c-check">
                    <input
                        type="checkbox"
                        class="pf-c-check__input"
                        ?checked=${first(this.instance?.compatibilityMode, false)}
                    />
                    <label class="pf-c-check__label"> ${t`Compatibility mode`} </label>
                </div>
                <p class="pf-c-form__helper-text">
                    ${t`Enable compatibility mode, increases compatibility with password managers on mobile devices.`}
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }
}
