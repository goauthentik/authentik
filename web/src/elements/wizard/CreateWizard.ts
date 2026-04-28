import "#elements/LicenseNotice";
import "#admin/endpoints/connectors/agent/AgentConnectorForm";
import "#admin/endpoints/connectors/fleet/FleetConnectorForm";
import "#admin/endpoints/connectors/gdtc/GoogleChromeConnectorForm";
import "#elements/wizard/FormWizardPage";
import "#elements/wizard/TypeCreateWizardPage";
import "#elements/wizard/Wizard";

import { AKElement } from "#elements/Base";
import {
    DialogInit,
    isTransclusionParentElement,
    modalInvoker,
    ModalInvokerDirectiveResult,
    renderModal,
    TransclusionChildElement,
    TransclusionChildSymbol,
} from "#elements/dialogs";
import { LitPropertyRecord, SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";
import { StrictUnsafe } from "#elements/utils/unsafe";
import {
    TypeCreateWizardPage,
    TypeCreateWizardPageLayouts,
} from "#elements/wizard/TypeCreateWizardPage";
import { formatTypeCreateStepID } from "#elements/wizard/utils";
import { AKWizard } from "#elements/wizard/Wizard";

import { TypeCreate } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, PropertyValues } from "lit";
import { guard } from "lit-html/directives/guard.js";
import { createRef, ref } from "lit-html/directives/ref.js";
import { property } from "lit/decorators.js";
import { keyed } from "lit/directives/keyed.js";

export class CreateWizard extends AKElement implements TransclusionChildElement {
    /**
     * Optional singular label for the type of entity this form creates/edits.
     */
    public static verboseName: string | null = null;

    /**
     * Optional plural label for the type of entity this form creates/edits
     */
    public static verboseNamePlural: string | null = null;

    //#region Modal helpers

    /**
     * A helper method to create an invoker for a modal containing this form.
     *
     * @see {@linkcode modalInvoker} for the underlying implementation.
     */
    public static asModalInvoker<T extends CreateWizard = CreateWizard>(
        props?: LitPropertyRecord<T> | null,
        init?: DialogInit,
    ): ModalInvokerDirectiveResult {
        return modalInvoker(this, props, init);
    }

    /**
     * Show a modal containing this form.
     *
     * @see {@linkcode renderModal} for the underlying implementation.
     * @returns A promise that resolves when the modal is closed.
     */
    public static showModal(init?: DialogInit): Promise<void> {
        return renderModal(new (this as unknown as CustomElementConstructor)(), init);
    }

    //#endregion

    protected override createRenderRoot(): HTMLElement | DocumentFragment {
        return this;
    }

    //#region Public Properties

    public [TransclusionChildSymbol] = true;

    @property({ attribute: false })
    public creationTypes: TypeCreate[] | null = null;

    @property({ type: String, useDefault: true })
    public layout: TypeCreateWizardPageLayouts = TypeCreateWizardPageLayouts.list;

    @property({ type: String, attribute: "group-label", useDefault: true })
    public groupLabel: string | null = null;

    @property({ type: String, attribute: "group-description", useDefault: true })
    public groupDescription: string | null = null;

    @property({ attribute: false, useDefault: true })
    public finalHandler?: () => Promise<void>;

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
        return this.#verboseName || (this.constructor as typeof CreateWizard).verboseName;
    }

    #verboseNamePlural: string | null = null;

    /**
     * Optional plural label for the type of entity this form creates/edits.
     *
     * Overrides the static `verboseNamePlural` property for this instance.
     */
    @property({ type: String, attribute: "entity-plural" })
    public set verboseNamePlural(value: string | null) {
        this.#verboseNamePlural = value;

        if (isTransclusionParentElement(this.parentElement)) {
            this.parentElement.slottedElementUpdatedAt = new Date();
        }
    }

    public get verboseNamePlural(): string | null {
        return (
            this.#verboseNamePlural || (this.constructor as typeof CreateWizard).verboseNamePlural
        );
    }

    public get wizard(): AKWizard | null {
        return this.wizardRef.value || null;
    }

    /**
     * An optional description to show on the initial page of the wizard,
     * used to explain the different types or provide general information about the creation process.
     */
    @property({ type: String })
    public description: string | null = null;

    //#endregion

    //#region Protected Properties

    protected wizardRef = createRef<AKWizard>();
    protected pageTypeCreateRef = createRef<TypeCreateWizardPage>();

    protected initialSteps = ["initial"];

    @property({ attribute: false, useDefault: true })
    public selectedType: TypeCreate | null = null;

    //#endregion

    //#region Lifecycle

    protected stepObserver: MutationObserver;

    public constructor() {
        super();

        // Assigning a part to the host element to aid in selecting the wizard.
        this.part.add("wizard");

        this.stepObserver = new MutationObserver(() => {
            this.requestUpdate();
        });
    }

    public override firstUpdated(changedProperties: PropertyValues<this>): void {
        super.firstUpdated(changedProperties);

        this.refresh();

        const { wizard } = this;
        if (wizard) {
            this.stepObserver.observe(wizard, { attributeFilter: ["data-active-step"] });
        }
    }

    public override disconnectedCallback(): void {
        super.disconnectedCallback();
        this.stepObserver.disconnect();
    }

    /**
     * Fetches data from the API endpoint.
     *
     * @param requestInit Optional request initialization parameters.
     * @returns A promise that resolves to the fetched data.
     */
    protected apiEndpoint?(requestInit?: RequestInit): Promise<TypeCreate[]>;

    /**
     * Refreshes the wizard's creation types.
     */
    public refresh = (): Promise<void> => {
        const result = this.apiEndpoint?.() ?? Promise.resolve([]);

        return result.then((types) => {
            this.creationTypes = types;
        });
    };

    /**
     * Formats the ARIA label for the wizard, delegating to the wizard component if available,
     * or using a default label if not.
     */
    public formatARIALabel(verboseName = this.verboseName): string {
        return (
            this.wizard?.formatARIALabel(verboseName) ??
            AKWizard.prototype.formatARIALabel.call(this, verboseName)
        );
    }

    /**
     * An overridable method to filter the wizard's steps when a new type is selected.
     *
     * @param type The selected creation type.
     * @param currentSteps The current steps of the wizard.
     * @returns The filtered steps to use for the wizard.
     */
    protected selectSteps(type: TypeCreate, _currentSteps: string[]): string[] {
        const stepID = formatTypeCreateStepID(type);

        return [stepID];
    }

    /**
     * Listener invoked when a type is selected on the initial page,
     * responsible for updating the wizard's steps and validity.
     */
    protected typeSelectListener = ({
        detail: typeCreate,
    }: CustomEvent<TypeCreate>): boolean | Promise<boolean> => {
        this.selectedType = typeCreate;

        const { wizard } = this;

        if (!wizard) return false;

        const currentSteps = wizard.steps.slice();

        const selectedSteps = this.selectSteps(typeCreate, currentSteps);
        const nextSteps = [...this.initialSteps];

        const idx = nextSteps.indexOf("initial") + 1;

        nextSteps.splice(idx, 0, ...selectedSteps);

        wizard.steps = nextSteps;
        wizard.valid = true;

        return wizard.navigateNext();
    };

    //#endregion

    //#region Rendering

    /**
     * Optional method to render additional content on the initial page, for example to explain the different types.
     */
    protected renderInitialPageContent?(): SlottedTemplateResult;

    /**
     * Optional method to render content before the type selection on the initial page,
     * for example to offer a choice between creation and binding an existing entity.
     */
    protected renderCreateBefore(): SlottedTemplateResult {
        return null;
    }

    protected renderHeading(): SlottedTemplateResult {
        const { selectedType, wizard } = this;

        if (!selectedType || wizard?.activeStep === "initial") {
            return null;
        }

        return html`<header part="step-heading">
            <h3 class="pf-c-wizard__main-title">${selectedType.name}</h3>
            <h4 class="pf-c-wizard__main-description">${selectedType.description}</h4>
        </header>`;
    }

    protected render(): SlottedTemplateResult {
        const initialPageContent = this.renderInitialPageContent?.() ?? null;

        return html`<ak-wizard
            ${ref(this.wizardRef)}
            entity-singular=${ifPresent(this.verboseName)}
            entity-plural=${ifPresent(this.verboseNamePlural)}
            description=${ifPresent(this.description)}
            part="main"
            .initialSteps=${this.initialSteps}
            .finalHandler=${this.finalHandler}
        >
            ${this.renderHeading()}
            ${keyed(
                this.wizard?.activeStep,
                html`<ak-wizard-page-type-create
                    ${ref(this.pageTypeCreateRef)}
                    slot="initial"
                    .types=${this.creationTypes}
                    layout=${this.layout}
                    group-label=${ifPresent(this.groupLabel)}
                    group-description=${ifPresent(this.groupDescription)}
                    headline=${this.verboseName
                        ? msg(str`Choose ${this.verboseName} Type`)
                        : msg("Choose type")}
                    @ak-type-create-select=${this.typeSelectListener}
                >
                    ${this.renderCreateBefore()}
                    ${guard([initialPageContent], () => {
                        if (!initialPageContent) {
                            return null;
                        }

                        return html`<div>
                            <p>${initialPageContent}</p>
                        </div>`;
                    })}
                </ak-wizard-page-type-create>`,
            )}
            ${this.renderForms()}
        </ak-wizard>`;
    }

    /**
     * Optional method to assemble properties for the form pages based on the selected type,
     * which are then passed to the form components when rendering.
     */
    protected assembleFormProps?(type: TypeCreate): LitPropertyRecord<object>;

    protected renderWizardStep(type: TypeCreate): SlottedTemplateResult {
        const { selectedType } = this;
        const props = this.assembleFormProps?.(type) ?? {};

        const slotName = formatTypeCreateStepID(type);
        const entityLabel = selectedType?.name ?? this.verboseName ?? msg("Entity");

        const label = msg(str`${entityLabel} Details`);

        const content = StrictUnsafe(type.component, props);

        return html`<ak-wizard-page-form slot=${slotName} headline=${label}
            >${content}</ak-wizard-page-form
        >`;
    }

    /**
     * Renders the form pages for each creation type.
     *
     * Each form is slotted with a name corresponding to its type.
     *
     * @see {@linkcode formatTypeCreateStepID} for the expected slot naming convention.
     */
    protected renderForms(): SlottedTemplateResult {
        return guard([this.creationTypes, this.selectedType], () => {
            if (!this.creationTypes) {
                return null;
            }

            return this.creationTypes.map((type) => this.renderWizardStep(type));
        });
    }

    //#endregion
}
