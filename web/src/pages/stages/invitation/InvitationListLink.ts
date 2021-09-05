import { t } from "@lingui/macro";
import { CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { until } from "lit-html/directives/until";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import AKGlobal from "../../../authentik.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFFlex from "@patternfly/patternfly/layouts/Flex/flex.css";
import { FlowsApi, FlowsInstancesListDesignationEnum } from "@goauthentik/api";
import { DEFAULT_CONFIG } from "../../../api/Config";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

@customElement("ak-stage-invitation-list-link")
export class InvitationListLink extends LitElement {
    @property()
    invitation?: string;

    @property()
    selectedFlow?: string;

    static get styles(): CSSResult[] {
        return [PFBase, PFForm, PFFormControl, PFFlex, PFDescriptionList, AKGlobal];
    }

    renderLink(): string {
        return `${window.location.protocol}//${window.location.host}/if/flow/${this.selectedFlow}/?token=${this.invitation}`;
    }

    render(): TemplateResult {
        return html`<dl class="pf-c-description-list pf-m-horizontal">
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${t`Select an enrollment flow`}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">
                        <select
                            class="pf-c-form-control"
                            @change=${(ev: Event) => {
                                const current = (ev.target as HTMLInputElement).value;
                                this.selectedFlow = current;
                            }}
                        >
                            ${until(
                                new FlowsApi(DEFAULT_CONFIG)
                                    .flowsInstancesList({
                                        ordering: "pk",
                                        designation: FlowsInstancesListDesignationEnum.Enrollment,
                                    })
                                    .then((flows) => {
                                        if (!this.selectedFlow && flows.results.length > 0) {
                                            this.selectedFlow = flows.results[0].slug;
                                        }
                                        return flows.results.map((flow) => {
                                            return html`<option
                                                value=${flow.slug}
                                                ?selected=${flow.slug === this.selectedFlow}
                                            >
                                                ${flow.slug}
                                            </option>`;
                                        });
                                    }),
                                html`<option>${t`Loading...`}</option>`,
                            )}
                        </select>
                    </div>
                </dd>
            </div>
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text"
                        >${t`Link to use the invitation.`}</span
                    >
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">
                        <input
                            class="pf-c-form-control"
                            readonly
                            type="text"
                            value=${this.renderLink()}
                        />
                    </div>
                </dd>
            </div>
        </dl>`;
    }
}
