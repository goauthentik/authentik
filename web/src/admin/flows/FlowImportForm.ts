import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { SentryIgnoredError } from "@goauthentik/common/errors";
import { PFColor } from "@goauthentik/elements/Label";
import { Form } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

import { Flow, FlowImportResult, FlowsApi } from "@goauthentik/api";

@customElement("ak-flow-import-form")
export class FlowImportForm extends Form<Flow> {
    @state()
    result?: FlowImportResult;

    getSuccessMessage(): string {
        return t`Successfully imported flow.`;
    }

    static get styles(): CSSResult[] {
        return super.styles.concat(PFDescriptionList);
    }

    async send(): Promise<FlowImportResult> {
        const file = this.getFormFiles()["flow"];
        if (!file) {
            throw new SentryIgnoredError("No form data");
        }
        const result = await new FlowsApi(DEFAULT_CONFIG).flowsInstancesImportCreate({
            file: file,
        });
        if (!result.success) {
            this.result = result;
            throw new SentryIgnoredError("Failed to import flow");
        }
        return result;
    }

    renderResult(): TemplateResult {
        return html`
            <ak-form-element-horizontal label=${t`Successful`}>
                <div class="pf-c-form__group-label">
                    <div class="c-form__horizontal-group">
                        <span class="pf-c-form__label-text">
                            <ak-label color=${this.result?.success ? PFColor.Green : PFColor.Red}>
                                ${this.result?.success ? t`Yes` : t`No`}
                            </ak-label>
                        </span>
                    </div>
                </div>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Log messages`}>
                <div class="pf-c-form__group-label">
                    <div class="c-form__horizontal-group">
                        <dl class="pf-c-description-list pf-m-horizontal">
                            ${(this.result?.logs || []).length > 0
                                ? this.result?.logs?.map((m) => {
                                      return html`<div class="pf-c-description-list__group">
                                          <dt class="pf-c-description-list__term">
                                              <span class="pf-c-description-list__text"
                                                  >${m.log_level}</span
                                              >
                                          </dt>
                                          <dd class="pf-c-description-list__description">
                                              <div class="pf-c-description-list__text">
                                                  ${m.event}
                                              </div>
                                          </dd>
                                      </div>`;
                                  })
                                : html`<div class="pf-c-description-list__group">
                                      <dt class="pf-c-description-list__term">
                                          <span class="pf-c-description-list__text"
                                              >${t`No log messages.`}</span
                                          >
                                      </dt>
                                  </div>`}
                        </dl>
                    </div>
                </div>
            </ak-form-element-horizontal>
        `;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`Flow`} name="flow">
                <input type="file" value="" class="pf-c-form-control" />
                <p class="pf-c-form__helper-text">
                    ${t`.yaml files, which can be found on goauthentik.io and can be exported by authentik.`}
                </p>
            </ak-form-element-horizontal>
            ${this.result ? this.renderResult() : html``}
        </form>`;
    }
}
