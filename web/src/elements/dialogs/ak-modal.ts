import Styles from "./ak-modal.css";
import DialogStyles from "./dialog.css";

import { PFSize } from "#common/enums";

import { AKElement } from "#elements/Base";
import { DialogInit, renderDialog } from "#elements/dialogs";
import {
    isTransclusionElement,
    TransclusionChildElement,
    TransclusionParentElement,
    TransclusionParentSymbol,
} from "#elements/dialogs/shared";
import { SlottedTemplateResult } from "#elements/types";

import { ConsoleLogger, Logger } from "#logger/browser";

import { msg } from "@lit/localize";
import { CSSResult, html, PropertyValues } from "lit";
import { createRef, ref } from "lit-html/directives/ref.js";
import { customElement, property, state } from "lit/decorators.js";
import { guard } from "lit/directives/guard.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

/**
 * A component used to display any content in a modal dialog with a consistent style and behavior.
 * This component may be used directly to wrap content, or extended for more specific modal implementations.
 *
 * @see {@link renderDialog} for a low-level API to render arbitrary content in a modal dialog.
 *
 * @remarks
 * The flexibility this component offers is made possible with a parent `<dialog>` element.
 * The browser-native `<dialog>` element provides the underlying functionality for modal behavior,
 * along with screen-reader friendly semantics and accessibility features.
 *
 * The content within the modal is typically slotted in, however this can be
 * customized by overriding the `render` method. If your slotted content includes
 * a header or actions, consider implementing {@linkcode TransclusionChildElement}
 * to allow this modal to automatically apply appropriate styles and structure.
 */
@customElement("ak-modal")
export class AKModal extends AKElement implements TransclusionParentElement {
    public static shadowRootOptions: ShadowRootInit = {
        ...AKElement.shadowRootOptions,
        delegatesFocus: true,
    };

    public [TransclusionParentSymbol] = true;

    /**
     * Whether the modal should open the parent dialog element when it is connected to the DOM.
     *
     * @default true
     */
    public static openOnConnect = true;

    /**
     * Show a modal containing this element.
     *
     * @see {@linkcode renderDialog} for the underlying implementation.
     *
     * @returns A promise that resolves when the modal is closed.
     */
    public static showModal(init?: DialogInit) {
        return renderDialog(new this(), init);
    }

    public static styles: CSSResult[] = [
        PFButton,
        PFForm,
        PFTitle,
        PFFormControl,
        PFPage,
        PFCard,
        PFContent,
        Styles,
    ];

    public static hostStyles: CSSResult[] = [DialogStyles];

    //#region Protected Properties

    protected logger: Logger;

    /**
     * An optional Lit ref which can automatically synchronize the modal's height with the element's height.
     */
    protected scrollContainerRef = createRef<HTMLElement>();

    protected get scrollContainer(): Element {
        return this.scrollContainerRef.value || this;
    }

    /**
     * A ref to the modal title element, used for accessibility purposes (e.g., setting `aria-labelledby` on the dialog).
     */
    protected modalTitleRef = createRef<HTMLElement>();

    /**
     * The parent element of the modal content.
     *
     * A runtime error will be thrown if this is not an {@linkcode HTMLDialogElement}.
     */
    declare parentElement: HTMLDialogElement | null;

    //#region Public Properties

    @property({ type: String, useDefault: true })
    public headline: string | null = null;

    /**
     * Whether the parent dialog element is currently open.
     */
    public get open(): boolean {
        return this.parentElement?.open ?? false;
    }

    @property({ type: Boolean, attribute: false, reflect: false })
    public set open(value: boolean) {
        if (value) {
            this.show();
        } else {
            this.close();
        }
    }

    @property({ type: String, useDefault: true })
    public size: PFSize | null = null;

    @property({ type: String, attribute: "cancel-button-label", useDefault: true })
    public cancelButtonLabel: string | null = null;

    /**
     * An optional aria-label formatter.
     */
    public formatARIALabel?(): string;

    //#endregion

    //#region Protected Properties

    protected defaultSlot: HTMLSlotElement;
    protected beforeBodySlot: HTMLSlotElement;
    protected dialogBody: HTMLDivElement;

    @state()
    protected slottedElement: TransclusionChildElement | null = null;

    @property({ attribute: false })
    public slottedElementUpdatedAt: Date | null = null;

    //#endregion

    //#region Public methods

    /**
     * Show the modal, rendering its contents.
     */
    public show() {
        const dialogElement = this.parentElement;

        if (!dialogElement) {
            this.logger.debug("No parentElement, cannot show modal", this);

            return;
        }

        dialogElement.showModal();

        dialogElement.classList.add("ak-c-dialog--m-fade-in");
    }

    /**
     * Close the modal, fading it out and then removing it from the DOM,
     * optionally with a return value.
     *
     * @param returnValue The return value for the dialog, if any.
     */
    public close(returnValue?: string) {
        const dialogElement = this.parentElement;

        if (!dialogElement) {
            this.logger.debug("No parentElement, cannot close modal", this);
            return;
        }

        dialogElement.addEventListener(
            "transitionend",
            this.delegateClose.bind(this, returnValue),
            {
                passive: true,
                once: true,
            },
        );

        dialogElement.classList.remove("ak-c-dialog--m-fade-in");
    }

    //#endregion

    //#region Event listeners

    /**
     * A stable reference to the dialog's open event listener.
     *
     * This is useful for simplifying adding and removing event listeners.
     */
    public showListener = () => {
        this.requestUpdate();
        this.show();
    };

    #closing = false;

    /**
     * Delegate the close action to the parent dialog element,
     * ensuring that the correct event listeners are triggered and the modal is properly closed.
     */
    protected delegateClose(returnValue?: string, event?: TransitionEvent) {
        if (this.#closing) {
            return;
        }

        this.#closing = true;

        if (!this.parentElement) {
            this.logger.debug("No parentElement, cannot delegate close", this);
            this.#closing = false;
            return;
        }

        this.logger.debug("Delegating close to parent dialog", { returnValue, event });

        this.parentElement.close(returnValue);
        this.#closing = false;
    }

    /**
     * A stable reference to the dialog's submit event listener, which
     * depending on the parent {@linkcode HTMLDialogElement.closedBy} property,
     * may close the dialog when a form inside the modal is submitted.
     */
    public submitListener = (_event: SubmitEvent) => {
        const { closedBy } = this.parentElement ?? {};

        if (closedBy === "node" || closedBy === "closerequest") {
            return;
        }

        return this.close("submitted");
    };

    /**
     * A stable reference to the dialog's close event listener.
     *
     * This is useful for simplifying adding and removing event listeners.
     */
    public closeListener = (_event?: Event) => {
        this.close("close");
    };

    /**
     * A stable reference to the dialog's backdrop click event listener.
     *
     * @remarks
     * Note that if the browser supports {@linkcode HTMLDialogElement}'s `closeBy` property,
     * the backdrop click may trigger a "cancel" event instead of a "click" event.
     */
    protected backdropClickListener = (event: Event) => {
        if (event.target !== this.parentElement) {
            return;
        }

        if (this.parentElement?.closedBy === "none") {
            return;
        }

        return this.close("backdrop");
    };

    //#endregion

    //#region Lifecycle

    /**
     * A bound render method that can be safely passed as a callback without losing the correct `this` context.
     *
     * @remarks
     * This allows the implementing class to use `render`, reducing the mental
     * overhead of which method should be used for rendering content.
     */
    protected renderContent: () => unknown;

    public constructor() {
        super();

        this.logger = ConsoleLogger.prefix(this.localName);

        this.renderContent = this.render.bind(this);
        this.render = this.renderInternal;

        this.defaultSlot = this.ownerDocument.createElement("slot");

        this.beforeBodySlot = this.ownerDocument.createElement("slot");
        this.beforeBodySlot.name = "before-body";

        this.dialogBody = this.ownerDocument.createElement("div");
        this.dialogBody.classList.add(
            "ak-c-dialog__body",
            "ak-m-thin-scrollbar",
            "ak-m-scroll-shadows",
        );
        this.dialogBody.setAttribute("part", "body");

        this.dialogBody.role = "region";
        this.dialogBody.ariaLabel = msg("Dialog content");

        this.dialogBody.appendChild(this.defaultSlot);

        this.addEventListener("command", (event) => {
            this.logger.debug("Command event received", { event });
        });
    }

    public override connectedCallback(): void {
        super.connectedCallback();

        const dialogElement = this.parentElement;

        if (!dialogElement) {
            this.logger.debug("Skipping connectedCallback, no parentElement", this);
            return;
        }

        const { localName } = this;

        if (!(dialogElement instanceof HTMLDialogElement)) {
            this.logger.error("Parent element is not a <dialog>, cannot initialize modal", {
                parentElement: dialogElement,
            });
            throw new TypeError(
                `authentik/modal: ${localName} must be placed inside a <dialog> element.`,
            );
        }

        dialogElement.dataset.akModal = localName;

        if (this.size) {
            dialogElement.classList.add("ak-c-dialog", this.size);
        }

        // eslint-disable-next-line wc/no-self-class
        this.classList.add("ak-c-dialog__content");

        dialogElement.addEventListener("click", this.backdropClickListener, { passive: true });

        this.addEventListener("submit", this.submitListener);

        const { openOnConnect } = this.constructor as typeof AKModal;

        if (openOnConnect) {
            this.show();
        }
    }

    public override updated(changedProperties: PropertyValues<this>): void {
        super.updated(changedProperties);

        const assignedElements = this.defaultSlot.assignedElements({ flatten: true });

        const nextSlottedElement = assignedElements.find(isTransclusionElement) ?? null;

        if (nextSlottedElement && nextSlottedElement !== this.slottedElement) {
            if (nextSlottedElement.displayBox) {
                nextSlottedElement.displayBox = "contents";
            }

            if ("visible" in nextSlottedElement) {
                nextSlottedElement.visible = true;
            }

            nextSlottedElement.classList.add("ak-c-dialog__slotted-content");

            this.slottedElement?.classList.remove("ak-c-dialog__slotted-content");
            this.slottedElement = nextSlottedElement;
        }

        requestAnimationFrame(this.synchronizeARIA);
    }

    /**
     * Synchronize the modal's ARIA attributes with its content for accessibility purposes.
     *
     * @remarks
     * The preferred order for determining the modal's accessible name is:
     * 1. The text content of the element referenced by {@linkcode modalTitleRef}, if it exists and has non-empty text.
     * 2. The static {@linkcode AKModal.formatARIALabel} property of the modal class, if it is defined.
     * 3. Otherwise, no accessible name is set on the dialog.
     */
    protected synchronizeARIA = (): void => {
        const dialogElement = this.parentElement;

        if (!dialogElement) return;

        const ariaLabel = this.formatARIALabel?.();

        const modalTitleElement = this.modalTitleRef.value;

        let label = modalTitleElement?.textContent?.trim() ?? ariaLabel ?? null;

        if (this.slottedElement) {
            label ||= this.slottedElement.formatARIALabel?.() ?? null;
        }

        dialogElement.ariaLabel = label;
    };

    //#endregion

    //#region Render

    /**
     * An overridable method that determines whether the modal content should be rendered.
     *
     * By default, the modal content is only rendered when the modal is open,
     * to avoid unnecessary rendering and potential issues with elements that
     * require being in the DOM to function properly (e.g., autofocus).
     */
    protected shouldRenderModalContent(): boolean {
        return this.open;
    }

    /**
     * The internal render method, including the close button and header, which are common to all modals.
     */
    protected renderInternal() {
        if (!this.shouldRenderModalContent()) {
            return super.render();
        }

        return [
            this.renderCloseButton(),
            this.renderHeader(),
            this.renderContent(),
            this.renderActions(),
        ];
    }

    protected renderCloseButton(): SlottedTemplateResult {
        return html`<button
            @click=${this.closeListener}
            class="pf-c-button pf-m-plain ak-c-dialog__close-button"
            type="button"
            aria-label=${msg("Close dialog")}
        >
            <i class="fas fa-times" aria-hidden="true"></i>
        </button>`;
    }

    /**
     * Render the modal header.
     *
     * This method may be overridden to customize the modal header.
     *
     * @protected
     * @abstract
     */
    protected renderHeader(): SlottedTemplateResult {
        const { headline, slottedElement, slottedElementUpdatedAt } = this;
        const hasHeaderSlot = this.findSlotted("header");

        return guard([headline, hasHeaderSlot, slottedElement, slottedElementUpdatedAt], () => {
            if (!headline && !hasHeaderSlot && !slottedElement) {
                return null;
            }

            if (slottedElement && !slottedElement.renderHeader) {
                // Slotted element is possibly nested, but does not implement a header render method,
                // so we cannot render a header for it.
                return null;
            }

            const slottedHeader = slottedElement ? slottedElement.renderHeader?.(true) : null;

            const content =
                slottedHeader ??
                html`<div class="ak-c-dialog__title">
                    <h1 class="ak-c-dialog__title-text" id="modal-title">
                        ${this.headline}
                        <slot name="header"></slot>
                    </h1>
                </div>`;

            return html`<div class="ak-c-dialog__header" part="header" ${ref(this.modalTitleRef)}>
                ${content}
            </div>`;
        });
    }

    /**
     * Render the modal actions.
     *
     * This method may be overridden to customize the modal actions.
     *
     * @protected
     * @abstract
     */
    protected renderActions(): SlottedTemplateResult {
        const { slottedElement, slottedElementUpdatedAt } = this;
        const hasActionsSlot = this.findSlotted("actions");

        return guard([hasActionsSlot, slottedElement, slottedElementUpdatedAt], () => {
            if (!hasActionsSlot && !slottedElement) {
                return null;
            }
            if (slottedElement && !slottedElement.renderActions) {
                // Slotted element is possibly nested, but does not implement an actions render method,
                // so we cannot render actions for it.
                return null;
            }

            const cancelButton = slottedElement?.cancelable
                ? html`<button
                      @click=${this.closeListener}
                      class="pf-c-button pf-m-link"
                      type="button"
                  >
                      ${this.cancelButtonLabel ??
                      slottedElement?.cancelButtonLabel ??
                      msg("Cancel")}
                  </button>`
                : null;

            return html`<footer
                aria-label=${msg("Form actions")}
                class="ak-c-dialog__footer"
                part="actions"
            >
                <slot name="actions"></slot>
                ${cancelButton} ${slottedElement ? slottedElement.renderActions?.(true) : null}
            </footer>`;
        });
    }

    /**
     * Render the modal content.
     *
     * Note that this method is only called when the modal is open.
     *
     * @protected
     * @abstract
     */
    protected render(): unknown {
        if (this.beforeBodySlot.assignedElements().length) {
            return [this.beforeBodySlot, this.dialogBody];
        }

        return this.dialogBody;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-modal": AKModal;
    }
}
