import { LitElement, ReactiveController, ReactiveControllerHost } from "lit";

type ReactiveElementHost = Partial<ReactiveControllerHost> & LitElement;

export interface ModalElement extends LitElement {
    closeModal(): void | boolean;
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

/**
 * Predicate to determine if a modal is connected and visible.
 */
function isModalLive(modal: ModalElement) {
    return modal.isConnected && modal.checkVisibility();
}

/**
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
    #host!: ReactiveElementHost;
    #modals: readonly ModalElement[] = [];

    constructor(host: ReactiveElementHost) {
        this.#host = host;

        this.#host.addController(this);
    }

    public hostConnected() {
        window.addEventListener("keyup", this.#keyupListener);
        window.addEventListener("ak-modal-show", this.#addModal);
        window.addEventListener("ak-modal-hide", this.#closeModal);
    }

    public hostDisconnected() {
        window.removeEventListener("keyup", this.#keyupListener);
        window.removeEventListener("ak-modal-show", this.#addModal);
        window.removeEventListener("ak-modal-hide", this.#closeModal);
    }

    #addModal = (e: ModalShowEvent) => {
        this.#modals = [...this.#modals, e.modal];
    };

    scheduleCleanup(modal: ModalElement) {
        requestAnimationFrame(() => {
            this.#modals = this.#modals.filter((m) => isModalLive(m) && modal !== m);
        });
    }

    #closeModal = ({ modal }: ModalHideEvent) => {
        if (!isModalLive(modal)) return;

        if (modal.closeModal() !== false) {
            this.scheduleCleanup(modal);
        }
    };

    #removeTopmostModal = () => {
        const knownModals = [...this.#modals];
        // Pop off modals until you find the first live one, schedule it to be closed, and make that
        // cleaned list the current state. Since this is our *only* state object, this has the
        // effect of crea
        // ting a new "knownModals" collection with some semantics.
        let modal: ModalElement | undefined;

        while ((modal = knownModals.pop())) {
            if (!isModalLive(modal)) continue;

            if (modal.closeModal() !== false) {
                this.scheduleCleanup(modal);
            }

            break;
        }

        this.#modals = knownModals;
    };

    #keyupListener = (e: KeyboardEvent) => {
        // The latter handles Firefox 37 and earlier.
        if (e.key === "Escape" || e.key === "Esc") {
            this.#removeTopmostModal();
        }
    };
}
