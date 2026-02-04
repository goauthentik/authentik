import "#admin/stages/invitation/InvitationSendEmailForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { MessageLevel } from "#common/messages";

import { AKElement } from "#elements/Base";
import { showMessage } from "#elements/messages/MessageContainer";

import { Invitation, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";

@customElement("ak-stage-invitation-list-link")
export class InvitationListLink extends AKElement {
    @property({ attribute: false })
    invitation?: Invitation;

    @property()
    selectedFlow?: string;

    static styles: CSSResult[] = [PFForm, PFFormControl, PFDescriptionList, PFButton];

    renderLink(): string {
        if (this.invitation?.flowObj) {
            this.selectedFlow = this.invitation.flowObj?.slug;
        }
        return `${window.location.protocol}//${window.location.host}/if/flow/${this.selectedFlow}/?itoken=${this.invitation?.pk}`;
    }

    renderFlowSelector(): TemplateResult {
        return html`<div class="pf-c-description-list__group">
            <dt class="pf-c-description-list__term">
                <span class="pf-c-description-list__text">${msg("Select an enrollment flow")}</span>
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
                            new StagesApi(DEFAULT_CONFIG)
                                .stagesInvitationStagesList({
                                    ordering: "name",
                                    noFlows: false,
                                })
                                .then((stages) => {
                                    if (
                                        !this.selectedFlow &&
                                        stages.results.length > 0 &&
                                        stages.results[0].flowSet
                                    ) {
                                        this.selectedFlow = stages.results[0].flowSet[0].slug;
                                    }
                                    const seenFlowSlugs: string[] = [];
                                    return stages.results.map((stage) => {
                                        return stage.flowSet?.map((flow) => {
                                            if (seenFlowSlugs.includes(flow.slug)) {
                                                return nothing;
                                            }
                                            seenFlowSlugs.push(flow.slug);
                                            return html`<option
                                                value=${flow.slug}
                                                ?selected=${flow.slug === this.selectedFlow}
                                            >
                                                ${flow.slug}
                                            </option>`;
                                        });
                                    });
                                }),
                            html`<option>${msg("Loading...")}</option>`,
                        )}
                    </select>
                </div>
            </dd>
        </div>`;
    }

    render(): TemplateResult {
        return html`<dl class="pf-c-description-list pf-m-horizontal">
            ${this.invitation?.flow === undefined ? this.renderFlowSelector() : nothing}
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text"
                        >${msg("Link to use the invitation.")}</span
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
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${msg("Actions")}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">
                        <button
                            class="pf-c-button pf-m-secondary"
                            @click=${() => {
                                navigator.clipboard.writeText(this.renderLink()).then(() => {
                                    showMessage({
                                        level: MessageLevel.info,
                                        message: msg("Copied link to clipboard."),
                                    });
                                });
                            }}
                        >
                            ${msg("Copy Link")}
                        </button>
                        <ak-forms-modal>
                            <span slot="submit">${msg("Send")}</span>
                            <span slot="header">${msg("Send Invitation via Email")}</span>
                            <ak-invitation-send-email-form
                                slot="form"
                                .invitation=${this.invitation}
                            >
                            </ak-invitation-send-email-form>
                            <button slot="trigger" class="pf-c-button pf-m-secondary">
                                ${msg("Send via Email")}
                            </button>
                        </ak-forms-modal>
                    </div>
                </dd>
            </div>
        </dl>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-invitation-list-link": InvitationListLink;
    }
}
