import { PFSize } from "#common/enums";

import { AKElement } from "#elements/Base";
import Styles from "#elements/modals/styles.css";

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
    static styles: CSSResult[] = [
        PFButton,
        PFForm,
        PFTitle,
        PFFormControl,
        PFPage,
        PFCard,
        PFContent,
        Styles,
    ];

    #resizeObserver: ResizeObserver | null = null;

    #debug = console.debug.bind(console, this.tagName.toLowerCase());
    declare parentElement: HTMLDialogElement | null;

    //#region Properties

    #headline: string | null = null;

    public get headline(): string | null {
        return this.#headline;
    }

    public set headline(value: string | null) {
        this.#headline = value;
    }

    @property({ type: String, attribute: "close-label", useDefault: true })
    public closeLabel = msg("Close");

    @property({ type: Boolean, attribute: false, reflect: false })
    public set open(value: boolean) {
        if (value) {
            this.show();
        } else {
            this.close();
        }
    }

    public get open(): boolean {
        return this.parentElement?.open ?? false;
    }

    @property({ type: String })
    public size: PFSize = PFSize.Large;

    //#endregion

    //#region Public methods

    /**
     * Show the modal, rendering its contents.
     */
    public show() {
        if (!this.parentElement) {
            this.#debug("No parentElement, cannot show modal", this);
            return;
        }

        this.parentElement.addEventListener("transitionend", this.fadeInListener, {
            once: true,
        });

        this.parentElement.showModal();

        this.parentElement?.classList.add("fade-in");
    }

    /**
     * Close the modal, optionally with a return value.
     *
     * @param returnValue The return value for the dialog, if any.
     */
    public close() {
        if (!this.parentElement) {
            this.#debug("No parentElement, cannot close modal", this);
            return;
        }

        this.parentElement.addEventListener("transitionend", this.fadeOutListener, {
            once: true,
        });

        this.parentElement.classList.remove("fade-in");
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

    protected fadeInListener = (event: TransitionEvent) => {
        this.#debug("fade-in complete", event);

        this.removeEventListener("transitionend", this.fadeInListener);

        const { parentElement } = this;

        if (!parentElement) {
            return;
        }

        parentElement.style.height = parentElement.clientHeight + "px";

        const synchronizeHeight: ResizeObserverCallback = ([entry]) => {
            parentElement.style.height = entry.contentRect.height + "px";
        };

        this.#resizeObserver = new ResizeObserver(synchronizeHeight);

        this.#resizeObserver.observe(this);
    };

    protected fadeOutListener = (event: TransitionEvent) => {
        this.#debug("fade-out complete", event);

        this.parentElement?.requestClose();

        this.removeEventListener("transitionend", this.fadeOutListener);
    };

    /**
     * A stable reference to the dialog's close event listener.
     *
     * This is useful for simplifying adding and removing event listeners.
     */
    protected closeListener = () => {
        this.close();
    };

    //#endregion

    //#region Lifecycle

    protected renderContent: () => unknown;

    public constructor() {
        super();

        this.renderContent = this.render.bind(this);
        this.render = this.renderInternal;
    }

    public override connectedCallback(): void {
        super.connectedCallback();

        if (!this.parentElement) {
            this.#debug("Skipping connectedCallback, no parentElement", this);
            return;
        }

        if (!(this.parentElement instanceof HTMLDialogElement)) {
            throw new TypeError(
                `authentik/modal: ${this.tagName.toLowerCase()} must be placed inside a <dialog> element.`,
            );
        }

        // this.parentElement.addEventListener("toggle", this.#toggleListener);

        const tagName = this.tagName.toLowerCase();

        this.parentElement.dataset.akModal = tagName;
        this.parentElement.classList.add("ak-c-modal", this.size);

        this.show();
    }

    public override disconnectedCallback(): void {
        super.disconnectedCallback();

        this.#resizeObserver?.disconnect();
        this.#resizeObserver = null;
    }

    //#endregion

    //#region Render

    protected shouldRenderModalContent(): boolean {
        return this.open;
        // return true;
    }

    protected renderInternal() {
        if (!this.shouldRenderModalContent()) {
            return super.render();
        }

        return [this.renderCloseButton(), this.renderHeader(), this.renderContent()];
    }

    protected renderCloseButton() {
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
    protected renderHeader() {
        const heading = this.headline;

        return guard(
            [heading],
            () =>
                html`<header class="ak-modal__header">
                    <div class="ak-modal__title">
                        <h1 class="ak-modal__title-text" id="modal-title">
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
