import "#components/ak-slug-input";
import "#components/ak-text-input";
import "#components/ak-radio-input";
import "#components/ak-switch-input";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import type { InvitationWizardState } from "./types";

import { aki } from "#common/api/client";
import { MessageLevel } from "#common/messages";

import { Form } from "#elements/forms/Form";
import { RadioOption } from "#elements/forms/Radio";
import { showAPIErrorMessage, showMessage } from "#elements/messages/MessageContainer";
import { SlottedTemplateResult } from "#elements/types";
import { WizardPage } from "#elements/wizard/WizardPage";

import {
    FlowDesignationEnum,
    type InvitationStage,
    StagesApi,
    UserTypeEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";

interface EnrollmentFlow {
    slug: string;
    pk: string;
    name: string;
}

/**
 * Serialized payload of {@linkcode InvitationWizardFlowStepNewEnrollmentForm}.
 */
interface NewEnrollmentFormData {
    flowName: string;
    slug: string;
    stageName: string;
    userType?: "external" | "internal";
    continueFlowWithoutInvitation: boolean;
}

/**
 * Serialized payload of {@linkcode InvitationWizardFlowStepExistingFlowForm}.
 */
interface ExistingFlowFormData {
    /**
     * The primary key of the selected enrollment flow.
     */
    flow?: string;
}

//#region New Enrollment Flow Form

@customElement("ak-invitation-wizard-flow-step-new-enrollment-form")
class InvitationWizardFlowStepNewEnrollmentForm extends Form<NewEnrollmentFormData> {
    public static override verboseName = msg("Enrollment Flow");
    public static override verboseNamePlural = msg("Enrollment Flows");

    public override renderHeader() {
        return null;
    }

    public override renderActions() {
        return null;
    }

    protected override renderForm(): SlottedTemplateResult {
        return html`<ak-text-input
                value="Enrollment with invitation"
                name="flowName"
                label=${msg("Flow Name")}
                required
                placeholder=${msg("Type a name for the new enrollment flow...")}
            ></ak-text-input>
            <ak-slug-input
                name="slug"
                label=${msg("Flow Slug")}
                value="enrollment-with-invitation"
                required
                help=${msg("Internal flow name used in URLs.")}
                placeholder=${msg("e.g. my-enrollment-flow")}
                input-hint="code"
            ></ak-slug-input>

            <ak-text-input
                name="stageName"
                label=${msg("Invitation Stage Name")}
                value="invitation-stage"
                required
                placeholder=${msg("Type a name for the stage...")}
            ></ak-text-input>

            <ak-radio-input
                label=${msg("User type")}
                name="userType"
                .options=${[
                    {
                        label: msg("External"),
                        default: true,
                        value: "external",
                        description: msg(
                            "Enrolled users are created as external (e.g. customers, guests). New users will be placed under users/external.",
                        ),
                    },
                    {
                        label: msg("Internal"),
                        value: "internal",
                        description: msg(
                            "Enrolled users are created as internal (e.g. employees). New users will be placed under users/internal.",
                        ),
                    },
                ] satisfies RadioOption<UserTypeEnum>[]}
            ></ak-radio-input>
            <ak-switch-input
                label=${msg("Continue flow without invitation")}
                checked
                name="continueFlowWithoutInvitation"
                help=${msg(
                    "If enabled, the stage will jump to the next stage when no invitation is given. If disabled, the flow will be cancelled without a valid invitation.",
                )}
            ></ak-switch-input>`;
    }
}

//#endregion

//#region Existing Flow Form

@customElement("ak-invitation-wizard-flow-step-existing-flow-form")
class InvitationWizardFlowStepExistingFlowForm extends Form<ExistingFlowFormData> {
    @property({ attribute: false })
    public enrollmentFlows: EnrollmentFlow[] = [];

    protected override renderForm(): SlottedTemplateResult {
        return html`<ak-form-element-horizontal
            label=${msg("Enrollment flow")}
            required
            name="flow"
        >
            <ak-search-select
                .fetchObjects=${async (query?: string): Promise<EnrollmentFlow[]> => {
                    if (!query) return this.enrollmentFlows;
                    const needle = query.toLowerCase();

                    return this.enrollmentFlows.filter(
                        (flow) =>
                            flow.name.toLowerCase().includes(needle) ||
                            flow.slug.toLowerCase().includes(needle),
                    );
                }}
                .renderElement=${(flow: EnrollmentFlow): string => flow.name}
                .renderDescription=${(flow: EnrollmentFlow): SlottedTemplateResult =>
                    html`${flow.slug}`}
                .value=${(flow: EnrollmentFlow | undefined): string | undefined => flow?.pk}
                style="display: block; width: 100%;"
            ></ak-search-select>
            <p class="pf-c-form__helper-text">
                ${msg(
                    "Only enrollment flows that have an invitation stage bound to them are listed here.",
                )}
            </p>
        </ak-form-element-horizontal>`;
    }
}

//#endregion

//#region Invitation Wizard Flow Step

const InvitationWizardFlowMode = {
    Existing: "existing",
    Create: "create",
} as const;

type InvitationWizardFlowMode =
    (typeof InvitationWizardFlowMode)[keyof typeof InvitationWizardFlowMode];

@customElement("ak-invitation-wizard-flow-step")
export class InvitationWizardFlowStep extends WizardPage<InvitationWizardState> {
    static styles: CSSResult[] = [
        PFForm,
        PFFormControl,
        PFButton,
        PFAlert,
        css`
            [part="no-enrollment-flows-alert"] {
                margin-block-end: var(--pf-global--spacer--md);
            }
        `,
    ];

    @property({ type: String })
    public mode: InvitationWizardFlowMode = InvitationWizardFlowMode.Existing;

    @state()
    protected enrollmentFlows: EnrollmentFlow[] = [];

    @state()
    protected loading = true;

    /**
     * Whether we fell back to "create" mode because no eligible enrollment flows exist.
     * Drives the informational alert, which should not appear when the user deliberately
     * chose to create a new flow.
     */
    @state()
    protected noEligibleFlows = false;

    protected formRef = createRef<Form>();

    protected async refreshEnrollmentFlows(): Promise<void> {
        this.loading = true;

        return aki(StagesApi)
            .stagesInvitationStagesList({
                noFlows: false,
            })
            .then((stages) => {
                const flowMap = new Map<string, EnrollmentFlow>();

                stages.results.forEach((stage: InvitationStage) => {
                    (stage.flowSet || [])
                        .filter((flow) => flow.designation === FlowDesignationEnum.Enrollment)
                        .forEach((flow) => {
                            if (!flowMap.has(flow.slug)) {
                                flowMap.set(flow.slug, {
                                    slug: flow.slug,
                                    pk: flow.pk,
                                    name: flow.name,
                                });
                            }
                        });
                });

                this.enrollmentFlows = Array.from(flowMap.values());
            })
            .catch((error) => {
                showAPIErrorMessage(error);
            })
            .finally(() => {
                this.loading = false;
            });
    }

    public override activeCallback = async (): Promise<void> => {
        // Forms own their own field-level validation; the Next button stays enabled and
        // `nextCallback` blocks progression via `reportValidity()` when something's missing.
        this.host.valid = true;

        if (this.mode !== InvitationWizardFlowMode.Existing) {
            // Nothing to fetch when creating a brand-new flow.
            this.loading = false;
            return;
        }

        await this.refreshEnrollmentFlows();

        // No eligible flows exist, so there's nothing to pick: fall back to creating one.
        if (!this.enrollmentFlows.length) {
            this.noEligibleFlows = true;
            this.mode = InvitationWizardFlowMode.Create;
            return;
        }

        // If there's exactly one eligible flow, skip this step so the user goes
        // straight to the invitation details. Drop ourselves from the step list
        // so the back button from the next step doesn't bounce back here.
        if (this.enrollmentFlows.length === 1) {
            const currentSlot = this.slot;
            const advanced = await this.host.navigateNext();

            if (advanced) {
                this.host.steps = this.host.steps.filter((s) => s !== currentSlot);
            }
        }
    };

    public override nextCallback = async (): Promise<boolean> => {
        const { state } = this.host;

        state.flowMode = this.mode;

        if (this.mode === InvitationWizardFlowMode.Existing) {
            const pk = this.resolveExistingFlowPk();

            if (!pk) return false;

            Object.assign(state, {
                selectedFlowPk: pk,
                selectedFlowSlug: this.enrollmentFlows.find((flow) => flow.pk === pk)?.slug,
                needsFlow: false,
                needsStage: false,
                needsBinding: false,
            } satisfies Partial<InvitationWizardState>);

            return true;
        }

        const form = this.formRef.value;

        if (!form) {
            showMessage({
                level: MessageLevel.error,
                message: msg("Form not found"),
            });

            return false;
        }

        if (!form.reportValidity()) return false;

        const data = form.toJSON() as unknown as NewEnrollmentFormData;

        Object.assign(state, {
            newFlowName: data.flowName,
            newFlowSlug: data.slug,
            newStageName: data.stageName,
            newUserType: data.userType ?? "external",
            continueFlowWithoutInvitation: data.continueFlowWithoutInvitation ?? true,
            needsFlow: true,
            needsStage: true,
            needsBinding: true,
        } satisfies Partial<InvitationWizardState>);

        return true;
    };

    /**
     * Resolve the selected enrollment flow's primary key for the "existing flow" mode.
     *
     * Returns `undefined` (blocking progression) when nothing valid is selected, except when
     * exactly one eligible flow exists — in which case it is used implicitly. The single-flow
     * fallback also covers the auto-advance in {@linkcode activeCallback}, which runs before the
     * form has rendered.
     */
    protected resolveExistingFlowPk(): string | undefined {
        const form = this.formRef.value;

        if (form?.reportValidity()) {
            const { flow } = form.toJSON() as ExistingFlowFormData;

            if (flow) return flow;
        }

        if (this.enrollmentFlows.length === 1) return this.enrollmentFlows[0].pk;

        return undefined;
    }

    public override reset(): void {
        this.enrollmentFlows = [];
        this.loading = true;
        this.noEligibleFlows = false;
    }

    //#region Rendering

    protected renderEnrollmentAlert(): SlottedTemplateResult {
        return html`<div
            class="pf-c-alert pf-m-warning pf-m-inline"
            part="no-enrollment-flows-alert"
        >
            <div class="pf-c-alert__icon">
                <i class="fas fa-exclamation-triangle" aria-hidden="true"></i>
            </div>
            <h4 class="pf-c-alert__title">
                ${msg("No enrollment flows with invitation stages found")}
            </h4>
            <div class="pf-c-alert__action"></div>
            <div class="pf-c-alert__description">
                <p>
                    ${msg(
                        "You can create a new enrollment flow and invitation stage right here, or cancel and bind an invitation stage to an existing flow manually.",
                    )}
                </p>
            </div>
        </div>`;
    }

    protected override render(): SlottedTemplateResult {
        if (this.loading) {
            return html`<div class="pf-c-form">
                <p>${msg("Loading...")}</p>
            </div>`;
        }

        if (this.mode === InvitationWizardFlowMode.Existing) {
            return html`<ak-invitation-wizard-flow-step-existing-flow-form
                .enrollmentFlows=${this.enrollmentFlows}
                ${ref(this.formRef)}
            ></ak-invitation-wizard-flow-step-existing-flow-form>`;
        }

        return html`<div class="pf-c-content">
            ${this.noEligibleFlows ? this.renderEnrollmentAlert() : null}
            <ak-invitation-wizard-flow-step-new-enrollment-form
                ${ref(this.formRef)}
            ></ak-invitation-wizard-flow-step-new-enrollment-form>
        </div>`;
    }

    //#endregion
}

//#endregion

declare global {
    interface HTMLElementTagNameMap {
        "ak-invitation-wizard-flow-step": InvitationWizardFlowStep;
        "ak-invitation-wizard-flow-step-new-enrollment-form": InvitationWizardFlowStepNewEnrollmentForm;
        "ak-invitation-wizard-flow-step-existing-flow-form": InvitationWizardFlowStepExistingFlowForm;
    }
}
