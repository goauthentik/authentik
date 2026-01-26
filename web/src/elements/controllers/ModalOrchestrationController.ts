import { LitElement, ReactiveController } from "lit";

interface ModalElement extends LitElement {
    close(): void | boolean;
}

export class ModalShowEvent extends Event {
    modal: ModalElement;
    constructor(modal: ModalElement) {
        super("ak-modal-show", { bubbles: true, composed: true });
        this.modal = modal;
    }
}

export class ModalHideEvent extends Event {
    modal: ModalElement;
    constructor(modal: ModalElement) {
        super("ak-modal-hide", { bubbles: true, composed: true });
        this.modal = modal;
    }
}

declare global {
    interface GlobalEventHandlersEventMap {
        "ak-modal-show": ModalShowEvent;
        "ak-modal-hide": ModalHideEvent;
    }
}

const modalIsLive = (modal: ModalElement) => modal.isConnected && modal.checkVisibility();

/**
 * class ModalOrchetrationController
 *
 * A top-level controller that listens for requests from modals to be added to
 * the management list, such that the *topmost* modal will be closed (and all
 * references to it eliminated) whenever the user presses the Escape key.
 * Can also take ModalHideEvent requests and automatically close the modal
 * sending the event.
 *
 * Both events that this responds to expect a reference to the modal to be part
 * of the event payload.
 *
 * If the `.closeModal()` method on the target modal returns `false`
 * *explicitly*, it will abort cleanup and the stack will keep the record that
 * the modal is still open. This allows `.closeModal()` to return `undefined`
 * and still behave correctly.
 */

export class ModalOrchestrationController implements ReactiveController {
    #knownModals: ModalElement[] = [];

    public hostConnected() {
        window.addEventListener("keyup", this.#keyupListener);
        window.addEventListener("ak-modal-show", this.#addModal);
        window.addEventListener("ak-modal-hide", this.closeModal);
    }

    public hostDisconnected() {
        window.removeEventListener("keyup", this.#keyupListener);
        window.removeEventListener("ak-modal-show", this.#addModal);
        window.removeEventListener("ak-modal-hide", this.closeModal);
    }

    #addModal = (e: ModalShowEvent) => {
        this.#knownModals = [...this.#knownModals, e.modal];
    };

    #cleanupFrameID = -1;

    #scheduleCleanup = (modal: ModalElement) => {
        cancelAnimationFrame(this.#cleanupFrameID);

        this.#cleanupFrameID = requestAnimationFrame(() => {
            this.#knownModals = this.#knownModals.filter((m) => modalIsLive(m) && modal !== m);
        });
    };

    closeModal = (e: ModalHideEvent) => {
        const modal = e.modal;

        if (!modalIsLive(modal)) return;

        if (modal.close() !== false) {
            this.#scheduleCleanup(modal);
        }
    };

    #removeTopmostModal = () => {
        const knownModals = [...this.#knownModals];

        // Pop off modals until you find the first live one, schedule it to be closed, and make that
        // cleaned list the current state. Since this is our *only* state object, this has the
        // effect of creating a new "knownModals" collection with some semantics.
        while (true) {
            const modal = knownModals.pop();

            if (!modal) break;

            if (!modalIsLive(modal)) continue;

            if (modal.close() !== false) {
                this.#scheduleCleanup(modal);
            }

            break;
        }
        this.#knownModals = knownModals;
    };

    #keyupListener = ({ key, defaultPrevented }: KeyboardEvent) => {
        // The latter handles Firefox 37 and earlier.
        if (key !== "Escape" && key !== "Esc") {
            return;
        }

        // Allow an event listener within the modal to prevent
        // our default behavior of closing the modal.
        if (defaultPrevented) return;

        if (key === "Escape" || key === "Esc") {
            this.#removeTopmostModal();
        }
    };
}
