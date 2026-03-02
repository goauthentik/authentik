import { PFSize } from "#common/enums";

import { AKElement } from "#elements/Base";
import Styles from "#elements/modals/styles.css";
import { SlottedTemplateResult } from "#elements/types";

import { ConsoleLogger, Logger } from "#logger/browser";

import { msg } from "@lit/localize";
import { CSSResult, html } from "lit";
import { property } from "lit/decorators.js";
import { guard } from "lit/directives/guard.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

export abstract class AKModal extends AKElement {
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

    #hostResizeObserver: ResizeObserver | null = null;

    protected logger: Logger;

    declare parentElement: HTMLDialogElement | null;

    //#region Properties

    #headline: string | null = null;

    public get headline(): string | null {
        return this.#headline;
    }

    public set headline(value: string | null) {
        this.#headline = value;
    }

    @property({ type: String, useDefault: true })
    public cancelText = msg("Close");

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

    @property({ type: String })
    public size: PFSize = PFSize.Large;

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

        dialogElement.addEventListener("transitionend", this.fadeInListener, {
            once: true,
            passive: true,
        });

        dialogElement.showModal();

        dialogElement.classList.add("fade-in");
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
            (event) => this.delegateClose(event, returnValue),
            { once: true, passive: true },
        );

        dialogElement.classList.remove("fade-in");
    }

    //#endregion

    //#region Event listeners

    /**
     * A stable reference to the dialog's open event listener.
     *
     * This is useful for simplifying adding and removing event listeners.
     */
    protected showListener = () => {
        this.show();
    };

    #heightSyncFrameID = -1;
    /**
     * A map of observed elements to their expected sizes,
     * used to prevent unnecessary height synchronizations.
     */
    #expectedSizes = new WeakMap();

    protected fadeInListener = async (event: TransitionEvent) => {
        this.logger.debug("fade-in complete", event);

        this.removeEventListener("transitionend", this.fadeInListener);

        const dialogElement = this.parentElement;

        if (!dialogElement) {
            this.logger.debug("Skipping height synchronization, no dialog element", this);
            return;
        }

        dialogElement.classList.add("fade-in-complete");

        dialogElement.style.height = dialogElement.clientHeight + "px";

        const synchronizeHeight: ResizeObserverCallback = ([entry]) => {
            this.#heightSyncFrameID = requestAnimationFrame(() => {
                const expectedSize = this.#expectedSizes.get(entry.target);
                if (entry.contentRect.height === expectedSize) {
                    return;
                }

                dialogElement.style.height = entry.contentRect.height + "px";
                this.#expectedSizes.set(entry.target, entry.contentRect.height);
            });
        };

        this.#hostResizeObserver = new ResizeObserver(synchronizeHeight);

        this.#hostResizeObserver.observe(this);

        window.addEventListener("resize", this.#resetHeightListener, {
            passive: true,
        });
    };

    #heightResetAnimationFrameID = -1;

    #resetHeightListener = () => {
        cancelAnimationFrame(this.#heightResetAnimationFrameID);
        cancelAnimationFrame(this.#heightSyncFrameID);

        this.#heightResetAnimationFrameID = requestAnimationFrame(() => {
            if (this.parentElement) {
                this.parentElement.style.height = "";
            }
        });
    };

    #closing = false;

    /**
     * Delegate the close action to the parent dialog element,
     * ensuring that the correct event listeners are triggered and the modal is properly closed.
     */
    protected delegateClose(event: TransitionEvent, returnValue?: string) {
        if (this.#closing) {
            return;
        }

        this.logger.debug("Closing", event);

        this.#closing = true;

        window.removeEventListener("resize", this.#resetHeightListener);

        this.#hostResizeObserver?.disconnect();
        this.#hostResizeObserver = null;

        this.parentElement?.close(returnValue);
    }

    /**
     * A stable reference to the dialog's close event listener.
     *
     * This is useful for simplifying adding and removing event listeners.
     */
    protected closeListener = () => {
        this.close();
    };

    /**
     * A stable reference to the dialog's backdrop click event listener.
     *
     * @remarks
     * Note that if the browser supports {@linkcode HTMLDialogElement}'s `closeBy` property,
     * the backdrop click may trigger a "cancel" event instead of a "click" event.
     */
    protected backdropClickListener = (event: Event) => {
        if (event.target === this.parentElement) {
            this.close();
        }
    };

    /**
     * A stable reference to the dialog's cancel event listener.
     *
     * This is useful for simplifying adding and removing event listeners.
     */
    protected cancelListener = (event: Event) => {
        if (!this.parentElement) {
            return;
        }

        event.preventDefault();

        this.close();
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

        this.logger = ConsoleLogger.prefix(this.tagName.toLowerCase());

        this.renderContent = this.render.bind(this);
        this.render = this.renderInternal;
    }

    public override connectedCallback(): void {
        super.connectedCallback();

        if (!this.parentElement) {
            this.logger.debug("Skipping connectedCallback, no parentElement", this);
            return;
        }

        if (!(this.parentElement instanceof HTMLDialogElement)) {
            throw new TypeError(
                `authentik/modal: ${this.tagName.toLowerCase()} must be placed inside a <dialog> element.`,
            );
        }

        const tagName = this.tagName.toLowerCase();

        this.parentElement.dataset.akModal = tagName;
        this.parentElement.classList.add("ak-c-modal", this.size);
        this.classList.add("ak-c-modal__content");

        this.parentElement.addEventListener("cancel", this.cancelListener);
        this.parentElement.addEventListener("click", this.backdropClickListener, { passive: true });

        this.show();
    }

    public override disconnectedCallback(): void {
        super.disconnectedCallback();

        this.#hostResizeObserver?.disconnect();
        this.#hostResizeObserver = null;
    }

    //#endregion

    //#region Render

    protected shouldRenderModalContent(): boolean {
        return this.open;
    }

    protected renderInternal() {
        if (!this.shouldRenderModalContent()) {
            return super.render();
        }

        return [this.renderCloseButton(), this.renderHeader(), this.renderContent()];
    }

    protected renderCloseButton(): SlottedTemplateResult {
        return html`<button
            @click=${this.closeListener}
            class="pf-c-button pf-m-plain"
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
        const heading = this.headline;

        return guard(
            [heading],
            () =>
                html`<header class="pf-c-modal__header">
                    <div class="ak-c-modal__title">
                        <h1 class="ak-c-modal__title-text" id="modal-title">
                            ${this.headline}
                            <slot name="header"></slot>
                        </h1>
                    </div>
                </header>`,
        );
    }

    /**
     * Render the modal content.
     *
     * Note that this method is only called when the modal is open.
     *
     * @protected
     * @abstract
     */
    protected abstract render(): unknown;

    // protected render(): unknown {
    //     return html`<slot></slot>`;
    // }

    //#endregion
}
