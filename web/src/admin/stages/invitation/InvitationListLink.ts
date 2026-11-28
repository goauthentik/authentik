import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import "#components/ak-text-input";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";

import { aki } from "#common/api/client";
import { writeToClipboard } from "#common/clipboard";
import { globalAK } from "#common/global";

import { AKElement } from "#elements/Base";
import { modalInvoker } from "#elements/dialogs";
import { SlottedTemplateResult } from "#elements/types";

import { AKLabel } from "#components/ak-label";

import { InvitationSendEmailForm } from "#admin/stages/invitation/InvitationSendEmailForm";

import { FlowSet, Invitation, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

@customElement("ak-stage-invitation-list-link")
export class InvitationListLink extends AKElement {
    static styles: CSSResult[] = [
        PFForm,
        PFFormControl,
        PFButton,
        css`
            :host {
                display: block;
                width: 100%;
            }

            fieldset[name="invitation-actions"] button {
                flex: 1 1 auto;
            }
        `,
    ];

    @property({ attribute: false })
    public invitation: Invitation | null = null;

    @property({ type: String, attribute: "selected-flow" })
    public selectedFlow: string | null = null;

    @state()
    protected flows: FlowSet[] | null = null;

    public override connectedCallback(): void {
        super.connectedCallback();

        aki(StagesApi)
            .stagesInvitationStagesList({
                ordering: "name",
                noFlows: false,
            })
            .then((stages) => {
                const flows = new Map<string, FlowSet>();

                for (const stage of stages.results) {
                    for (const flow of stage.flowSet ?? []) {
                        if (!flows.has(flow.slug)) flows.set(flow.slug, flow);
                    }
                }

                this.flows = Array.from(flows.values());
                this.selectedFlow ??= this.flows[0]?.slug ?? null;
            });
    }

    protected get flowSlug(): string | null {
        return this.invitation?.flowObj?.slug ?? this.selectedFlow;
    }

    protected formatInvitationLink(): string {
        return `${globalAK().api.base}if/flow/${this.flowSlug}/?itoken=${this.invitation?.pk}`;
    }

    protected changeListener = (ev: Event) => {
        this.selectedFlow = (ev.target as HTMLSelectElement).value;
    };

    protected doCopy = () => {
        writeToClipboard(this.formatInvitationLink());
    };

    protected renderFlowSelector(): SlottedTemplateResult {
        if (this.invitation?.flow) {
            return null;
        }

        return html`<ak-form-element-horizontal>
            ${AKLabel(
                {
                    slot: "label",
                    className: "pf-c-form__group-label",
                    htmlFor: "flow",
                },
                msg("Enrollment Flow"),
            )}
            <select class="pf-c-form-control" @change=${this.changeListener} id="flow">
                ${
                    this.flows
                        ? this.flows.map(
                              (flow) =>
                                  html`<option
                                      value=${flow.slug}
                                      ?selected=${flow.slug === this.selectedFlow}
                                  >
                                      ${flow.title} (${flow.slug})
                                  </option>`,
                          )
                        : html`<option>${msg("Loading...")}</option>`
                }
            </select>
        </ak-form-element-horizontal>`;
    }

    protected renderActions(): SlottedTemplateResult {
        return html`<fieldset
            name="invitation-actions"
            class="ak-c-fieldset pf-c-form__group pf-m-action"
        >
            <legend class="sr-only">${msg("Invitation Actions")}</legend>

            <button class="pf-c-button pf-m-secondary" type="button" @click=${this.doCopy}>
                <span class="pf-c-button__icon pf-m-start">
                    <i class="fas fa-copy" aria-hidden="true"></i>
                </span>
                ${msg("Copy Link")}
            </button>
            <button
                class="pf-c-button pf-m-secondary"
                type="button"
                ${modalInvoker(InvitationSendEmailForm, {
                    invitation: this.invitation,
                })}
            >
                ${msg("Send via Email")}
                <span class="pf-c-button__icon pf-m-end">
                    <i class="fas fa-paper-plane" aria-hidden="true"></i>
                </span>
            </button>
        </fieldset>`;
    }

    protected override render(): SlottedTemplateResult {
        const invitationLink = this.formatInvitationLink();

        return html`<div class="pf-c-form pf-m-horizontal">
            <ak-text-input
                label=${msg("Invitation Link")}
                value=${invitationLink}
                type="url"
                readonly
            ></ak-text-input>
            ${this.renderFlowSelector()} ${this.renderActions()}
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-invitation-list-link": InvitationListLink;
    }
}
