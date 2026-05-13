import "#elements/wizard/ActionWizardPage";
import "#elements/LoadingOverlay";

import { AKRefreshEvent } from "#common/events";

import { AKElement } from "#elements/Base";
import { listen } from "#elements/decorators/listen";
import { isTransclusionParentElement } from "#elements/dialogs";
import { SlottedTemplateResult } from "#elements/types";
import { findNearestDialog } from "#elements/utils/render-roots";
import { WizardPage } from "#elements/wizard/WizardPage";

import { ButtonKindLabelRecord } from "#components/ak-wizard/shared";

import { ConsoleLogger } from "#logger/browser";

import { msg, str } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { property } from "@lit/reactive-element/decorators/property.js";
import { css, CSSResult, html, PropertyValues } from "lit";
import { guard } from "lit-html/directives/guard.js";
import { state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFWizard from "@patternfly/patternfly/components/Wizard/wizard.css";

export interface WizardAction {
    displayName: string;
    subText?: string;
    run: () => Promise<boolean>;
}

export interface StepProgress {
    activeStepElement: WizardPage | null;
    activeStepIndex: number;
    lastPage: boolean;
}

export const ApplyActionsSlot = "apply-actions";

/**
 * A base class for creation wizards, providing common functionality such as step management,
 * loading state, and action handling.
 *
 * @typeparam S The shape of the state object that can be used to share data between steps and the final handler.
 */
@customElement("ak-wizard")
export class AKWizard<S = Record<string, unknown>> extends AKElement {
    /**
     * Optional singular label for the type of entity this wizard creates.
     */
    public static verboseName: string | null = null;

    public static styles: CSSResult[] = [
        PFButton,
        PFTitle,
        PFWizard,
        css`
            :host {
                display: block;
                height: min(var(--ak-c-dialog--AspectRatioHeight), var(--ak-c-dialog--MaxHeight));
            }
        `,
    ];

    protected logger = ConsoleLogger.prefix(this.localName);

    protected defaultSlot = this.ownerDocument.createElement("slot");

    //#region Public Properties

    /**
     * Formats the ARIA label for the wizard, using the {@linkcode verboseName} property if available.
     */
    public formatARIALabel(verboseName = this.verboseName): string {
        return verboseName
            ? msg(str`New ${verboseName} Wizard`, {
                  id: "wizard.ariaLabel.entity-singular",
                  desc: "ARIA label for the creation wizard, where the entity singular is interpolated.",
              })
            : msg("Wizard", {
                  id: "wizard.ariaLabel.default",
                  desc: "ARIA label for the creation wizard when no entity singular is provided.",
              });
    }

    /**
     * Formats the header text for the wizard, using the {@linkcode verboseName} property if available.
     */
    public formatHeader(verboseName = this.verboseName): string {
        if (verboseName) {
            return msg(str`Create New ${verboseName}`, {
                id: "wizard.header.entity-singular",
                desc: "Header for the creation wizard, where the entity singular is interpolated.",
            });
        }

        return msg("Create New Entity", {
            id: "wizard.header.default",
            desc: "Header for the creation wizard when no entity singular is provided.",
        });
    }

    //#region Public Properties

    /**
     * Whether the wizard can be cancelled.
     */
    @property({ type: Boolean })
    public cancelable = true;

    /**
     * Whether the wizard can go back to the previous step.
     */
    @property({ type: Boolean })
    public canBack = true;

    /**
     * Header title of the wizard.
     */
    @property()
    public header?: string;

    #verboseName: string | null = null;

    /**
     * Optional singular label for the type of entity this form creates/edits.
     *
     * Overrides the static `verboseName` property for this instance.
     */
    @property({ type: String, attribute: "entity-singular" })
    public set verboseName(value: string | null) {
        this.#verboseName = value;

        if (isTransclusionParentElement(this.parentElement)) {
            this.parentElement.slottedElementUpdatedAt = new Date();
        }
    }

    public get verboseName(): string | null {
        return this.#verboseName || (this.constructor as typeof AKWizard).verboseName;
    }

    /**
     * Optional plural label for the type of entity this wizard creates, used in messages and the like.
     */
    @property({ type: String, attribute: "entity-plural" })
    public verboseNamePlural: string | null = null;

    /**
     * An optional description to show on the initial page of the wizard,
     * used to explain the different types or provide general information about the creation process.
     */
    @property({ type: String })
    public description: string | null = null;

    /**
     * Whether the wizard is valid and can proceed to the next step.
     */
    @property({ type: Boolean })
    public valid = false;

    /**
     * Actions to display at the end of the wizard.
     */
    private _actions: WizardAction[] = [];

    @property({ attribute: false })
    public get actions(): WizardAction[] {
        return this._actions;
    }

    public set actions(value: WizardAction[]) {
        const oldValue = this._actions;
        this._actions = value;

        if (this._actions.length > 0) {
            if (!this.querySelector(`[slot="ak-wizard-page-action"]`)) {
                const actionPage = document.createElement("ak-wizard-page-action");
                actionPage.slot = "ak-wizard-page-action";
                actionPage.dataset.wizardmanaged = "true";
                this.appendChild(actionPage);
            }
            if (!this.steps.includes("ak-wizard-page-action")) {
                this.steps = [...this.steps, "ak-wizard-page-action"];
            }
        }

        this.requestUpdate("actions", oldValue);
    }

    @property({ attribute: false })
    public finalHandler?: () => Promise<void>;

    @property({ attribute: false })
    public state: S = {} as S;

    @property({ attribute: false })
    public dialog: HTMLDialogElement | null = null;

    //#endregion

    @state()
    protected loading = false;

    protected loadingOverlay = this.ownerDocument.createElement("ak-loading-overlay");

    //#region State

    /**
     * Initial steps to reset to.
     */
    @property({ attribute: false })
    public initialSteps: string[] = [];

    #steps: string[] | null = null;

    /**
     * Step tag names present in the wizard.
     */
    public get steps(): readonly string[] {
        return this.#steps || this.initialSteps;
    }

    @property({ attribute: false })
    public set steps(nextSteps: string[]) {
        const applyStepPresent = this.#steps?.includes(ApplyActionsSlot);

        if (applyStepPresent) {
            nextSteps.push(ApplyActionsSlot);
        }
        this.#steps = nextSteps;
    }

    /**
     * The active step element being displayed.
     */
    @property({ attribute: false })
    public activeStepElement: WizardPage | null = null;

    public get activeStep(): string | null {
        return this.activeStepElement?.slot || null;
    }

    protected get activeStepIndex(): number {
        const { activeStepElement, steps } = this;

        const activeStepIndex = activeStepElement ? steps.indexOf(activeStepElement.slot) : 0;

        return activeStepIndex;
    }

    protected getStepElementByIndex(stepIndex: number): WizardPage | null {
        const stepName = this.steps[stepIndex];

        return this.getStepElementByName(stepName);
    }

    protected getStepElementByName(stepName: string): WizardPage | null {
        return this.querySelector<WizardPage>(`[slot=${stepName}]`);
    }

    /**
     * Determines the current step progress, the active step element, its index,
     * and whether it's the last page.
     *
     * @remarks
     * TODO: This causes a synchronous update of the active step element.
     * It'd be nice if this could be decoupled. Leaving as is for now since,
     * x`but something to keep in mind if we run into weird update issues.
     */
    protected takeStepProgress(): StepProgress {
        if (!this.activeStepElement) {
            const firstStepElement = this.getStepElementByIndex(0);

            this.activeStepElement = firstStepElement;
        }

        const { steps, activeStepElement } = this;

        const activeStepIndex = activeStepElement ? steps.indexOf(activeStepElement.slot) : 0;

        let lastPage = activeStepIndex === steps.length - 1;

        if (lastPage && !steps.includes("ak-wizard-page-action") && this.actions.length > 0) {
            this.steps = steps.concat("ak-wizard-page-action");

            lastPage = activeStepIndex === steps.length - 1;
        }

        return {
            activeStepElement,
            activeStepIndex,
            lastPage,
        };
    }

    /**
     * Navigates to the previous step, if possible.
     */
    public navigatePrevious = (): Promise<boolean> => {
        const prevPage = this.getStepElementByIndex(this.activeStepIndex - 1);

        if (prevPage) {
            this.activeStepElement = prevPage;
            return Promise.resolve(true);
        }

        return Promise.resolve(false);
    };

    /**
     * Navigates to the next step, if possible.
     * If the current step has a `nextCallback`, it will be invoked first.
     */
    public navigateNext = async (event?: Event): Promise<boolean> => {
        const { activeStepElement, activeStepIndex, lastPage } = this.takeStepProgress();

        if (!activeStepElement) return false;

        if (activeStepElement.nextCallback) {
            this.loading = true;

            const completedStep = await activeStepElement.nextCallback(event);

            this.loading = false;

            if (!completedStep) return false;

            if (lastPage) {
                const promise = this.finalHandler?.() || Promise.resolve();

                return promise
                    .then(() => {
                        this.requestClose("submitted");
                        return true;
                    })
                    .finally(() => {
                        this.loading = false;
                    });
            }
        }

        const nextPage = this.getStepElementByIndex(activeStepIndex + 1);

        if (!nextPage) {
            this.logger.warn("No next page found for step", {
                stepIndex: activeStepIndex + 1,
                steps: this.steps,
            });

            return false;
        }

        this.activeStepElement = nextPage;

        return true;
    };

    //#endregion

    //#region Lifecycle

    public override connectedCallback() {
        super.connectedCallback();

        this.dialog ??= findNearestDialog(this);
    }

    public override updated(changedProperties: PropertyValues<this>): void {
        super.updated(changedProperties);

        if (changedProperties.has("activeStepElement") && this.activeStepElement) {
            const activated = this.activeStepElement.activeCallback?.() || Promise.resolve();

            activated
                .then(() => {
                    this.dataset.activeStep = this.activeStep || "";
                })
                .catch((error: unknown) => {
                    this.logger.error("Error in active callback of step", {
                        step: this.activeStepElement,
                        error,
                    });
                });
        }
    }

    //#endregion

    //#region Event Listeners

    public requestClose = (returnValue?: string) => {
        if (!this.dialog) {
            this.logger.warn("Skipping close request: No dialog found for wizard.");
            return;
        }

        this.dialog.requestClose(returnValue);
    };

    @listen(AKRefreshEvent, { target: window })
    protected refreshListener = (event: AKRefreshEvent) => {
        const { lastPage } = this.takeStepProgress();

        if (!lastPage) {
            event.stopImmediatePropagation();
        }
    };

    //#endregion

    //#region Rendering

    public renderHeader(): SlottedTemplateResult {
        const { cancelable, description } = this;

        return guard([cancelable, description], () => {
            const header = this.formatHeader();

            const children: SlottedTemplateResult = [
                html`<button
                    data-test-id="wizard-close"
                    class="pf-c-button pf-m-plain pf-c-wizard__close"
                    type="button"
                    aria-label="${msg("Cancel wizard")}"
                    @click=${() => this.requestClose("cancel")}
                >
                    <i class="fas fa-times" aria-hidden="true"></i>
                </button>`,
                header
                    ? html`<h1
                          id="modal-title"
                          role="heading"
                          aria-level="1"
                          class="pf-c-title pf-m-3xl pf-c-wizard__title"
                          data-test-id="wizard-heading"
                      >
                          ${header}
                      </h1>`
                    : null,
                description
                    ? html`<p
                          role="heading"
                          aria-level="2"
                          id="modal-description"
                          class="pf-c-wizard__description"
                      >
                          ${description}
                      </p>`
                    : null,
            ];

            return html`<header class="pf-c-wizard__header">${children}</header>`;
        });
    }

    protected override render(): SlottedTemplateResult {
        const stepProgress = this.takeStepProgress();

        return html`<div class="pf-c-wizard" role="presentation">
            ${this.renderHeader()}

            <div role="presentation" class="pf-c-wizard__outer-wrap">
                ${this.loading ? this.loadingOverlay : null}
                <div class="pf-c-wizard__inner-wrap">
                    <nav aria-label="${msg("Wizard steps")}" class="pf-c-wizard__nav">
                        <ol role="presentation" class="pf-c-wizard__nav-list">
                            ${this.renderStepList(stepProgress)}
                        </ol>
                    </nav>
                    <main
                        part="wizard-main"
                        class="pf-c-wizard__main ak-m-thin-scrollbar"
                        aria-label=${msg("Wizard content")}
                    >
                        ${this.defaultSlot}
                        <div role="presentation" class="pf-c-wizard__main-body">
                            ${this.renderBody()}
                        </div>
                    </main>
                </div>
                <nav class="pf-c-wizard__footer" aria-label="${msg("Wizard navigation")}">
                    ${this.renderNavigationButtons(stepProgress)}
                </nav>
            </div>
        </div>`;
    }
    protected renderStepList({ activeStepIndex }: StepProgress): SlottedTemplateResult {
        const { steps, renderRoot } = this;

        return guard([steps, activeStepIndex, renderRoot.childElementCount], () => {
            return this.steps.map((step, idx) => {
                const stepEl = this.getStepElementByName(step);

                if (!stepEl) {
                    console.warn(`Expected step element with slot="${step}" not found in wizard.`, {
                        step,
                        slotSelector: `[slot=${step}]`,
                        renderRootChildren: renderRoot.children,
                    });
                    return html`<p>Unexpected missing step: ${step}</p>`;
                }

                // By default, disable steps ahead of the current step
                let disabled = activeStepIndex < idx;
                // If this wizard is at the end, disable navigation back
                if (activeStepIndex === this.steps.length - 1 && idx !== activeStepIndex) {
                    disabled = true;
                }
                return html`<li role="presentation" class="pf-c-wizard__nav-item">
                    <button
                        class=${classMap({
                            "pf-c-wizard__nav-link": true,
                            "pf-m-current": idx === activeStepIndex,
                        })}
                        type="button"
                        ?disabled=${disabled}
                        @click=${() => {
                            this.activeStepElement = stepEl;
                        }}
                    >
                        ${stepEl.formatSidebarLabel()}
                    </button>
                </li>`;
            });
        });
    }

    protected renderBody(): SlottedTemplateResult {
        return html`<slot name=${this.activeStepElement?.slot || this.steps[0]}></slot>`;
    }

    protected renderNavigationButtons({
        activeStepIndex,
        lastPage,
    }: StepProgress): SlottedTemplateResult {
        const { canBack, cancelable, valid, childElementCount } = this;

        return guard(
            [activeStepIndex, lastPage, canBack, cancelable, valid, childElementCount],
            () => {
                const customLabel = this.activeStepElement?.formatNextLabel();
                const nextLabel =
                    customLabel ??
                    (lastPage && activeStepIndex > 0
                        ? this.cancelable
                            ? ButtonKindLabelRecord.create()
                            : ButtonKindLabelRecord.finish()
                        : ButtonKindLabelRecord.next());

                return [
                    cancelable
                        ? html`<div class="pf-c-wizard__footer-cancel">
                              <button
                                  data-test-id="wizard-navigation-cancel"
                                  class="pf-c-button pf-m-link"
                                  type="button"
                                  @click=${() => this.requestClose("cancel")}
                              >
                                  ${msg("Cancel")}
                              </button>
                          </div>`
                        : null,
                    activeStepIndex > 0 && canBack
                        ? html`<button
                              data-test-id="wizard-navigation-previous"
                              class="pf-c-button pf-m-secondary"
                              type="button"
                              @click=${this.navigatePrevious}
                          >
                              ${ButtonKindLabelRecord.back()}
                          </button>`
                        : null,
                    html`<button
                        data-test-id="wizard-navigation-next"
                        class="pf-c-button pf-m-primary"
                        ?disabled=${!this.valid}
                        type="button"
                        @click=${this.navigateNext}
                    >
                        ${nextLabel}
                    </button>`,
                ];
            },
        );
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-wizard": AKWizard;
    }

    interface WizardNavigationTestIDMap {
        next: HTMLButtonElement;
        previous: HTMLButtonElement;
        cancel: HTMLButtonElement;
    }

    interface WizardTestIDMap {
        navigation: WizardNavigationTestIDMap;
    }

    interface TestIDSelectorMap {
        wizard: WizardTestIDMap;
    }
}
