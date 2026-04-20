import "#admin/stages/invitation/InvitationListLink";

import type { InvitationWizardState } from "./types";

import { AKRefreshEvent } from "#common/events";
import { MessageLevel } from "#common/messages";

import { showMessage } from "#elements/messages/MessageContainer";
import { WizardPage } from "#elements/wizard/WizardPage";

import { Invitation } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-invitation-wizard-success-step")
export class InvitationWizardSuccessStep extends WizardPage {
    static styles: CSSResult[] = [
        PFBase,
        PFForm,
        PFAlert,
        css`
            :host {
                display: block;
                width: 100%;
            }
            ak-stage-invitation-list-link {
                display: block;
                width: 100%;
            }
        `,
    ];

    @state()
    invitation?: Invitation;

    #notified = false;

    activeCallback = async (): Promise<void> => {
        const wizardState = this.host.state as unknown as InvitationWizardState;
        this.invitation = wizardState.createdInvitation;
        this.host.valid = true;

        if (this.invitation && !this.#notified) {
            showMessage({
                level: MessageLevel.success,
                message: msg("Successfully created invitation."),
            });
            this.#notified = true;
        }
    };

    nextCallback = async (): Promise<boolean> => {
        this.dispatchEvent(new AKRefreshEvent());
        return true;
    };

    override reset(): void {
        this.invitation = undefined;
        this.#notified = false;
    }

    render(): TemplateResult {
        const invitation = this.invitation;

        if (!invitation) {
            return html`<div class="pf-c-alert pf-m-warning pf-m-inline">
                <div class="pf-c-alert__icon">
                    <i class="fas fa-exclamation-triangle" aria-hidden="true"></i>
                </div>
                <h4 class="pf-c-alert__title">${msg("No invitation was created.")}</h4>
            </div>`;
        }

        return html`
            <ak-stage-invitation-list-link
                .invitation=${invitation}
            ></ak-stage-invitation-list-link>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-invitation-wizard-success-step": InvitationWizardSuccessStep;
    }
}
