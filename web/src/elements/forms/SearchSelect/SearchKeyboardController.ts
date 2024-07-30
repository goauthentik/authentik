import { bound } from "@goauthentik/elements/decorators/bound.js";
import { match } from "ts-pattern";

import { LitElement, ReactiveController, ReactiveControllerHost } from "lit";

import { KeyboardControllerEscapeEvent, KeyboardControllerSelectEvent } from "./SearchKeyboardControllerEvents.js";

type ValuedHtmlElement = HTMLElement & { value: string };
type ReactiveElementHost = Partial<ReactiveControllerHost> &
    LitElement & { value?: string; items: ValuedHtmlElement[] };

/**
 * @class AkKeyboardController
 *
 * This reactive controller connects to the host and sets up listeners for keyboard events to manage
 * a list of elements.  Navigational controls (up, down, home, end) do what you'd expect.  Enter and Space
 * "select" the current item, which means:
 *
 * - All other items lose focus and tabIndex
 * - The selected item gains focus and tabIndex
 * - The value of the selected item is sent to the host as an event
 *
 * @fires ak-keyboard-controller-select - When an element is selected. Contains the `value` of the
 * selected item.
 *
 * @fires ak-keyboard-controller-close - When `Escape` is pressed. Clients can do with this as they
 * wish.
 *
 */
export class AkKeyboardController implements ReactiveController {
    private host: ReactiveElementHost;

    private index: number = 0;

    private highlighter: string;

    /**
     * @arg selector: The class identifier (it *must* be a class identifier) of the DOM objects
     * that this controller will be working with.
     *
     * NOTE: The objects identified by the selector *must* have a `value` associated with them, and
     * as in all things HTML, that value must be a string.
     *
     * @arg highlighter: The class identifier that clients *may* use to set an alternative focus
     * on the object.  Note that the object will always receive focus.
     *
     */
    constructor(host: ReactiveElementHost, highlighter = ".ak-highlight-item") {
        this.host = host;
        console.log(this.host);
        host.addController(this);
        this.highlighter = highlighter.replace(/^\./, "");
    }

    hostUpdated() {
        const current = this.host.items.findIndex((item) => item.value === this.host.value);
        if (current >= 0) {
            this.index = current;
        }
    }

    hostConnected() {
        this.host.addEventListener("keydown", this.onKeydown);
    }

    hostDisconnected() {
        this.host.removeEventListener("keydown", this.onKeydown);
    }

    hostVisible() {
        this.host.items[this.index]?.focus();
    }

    get current() {
        return this.host.items[this.index];
    }

    get value() {
        return this.current?.value;
    }

    set value(v: string) {
        const index = this.host.items.findIndex((i) => i.value === v);
        if (index !== undefined) {
            this.index = index;
            this.performUpdate();
        }
    }

    private performUpdate() {
        this.host.items.forEach((item) => {
            item.classList.remove(this.highlighter);
            item.tabIndex = 0;
        });
        this.host.items[this.index].classList.add(this.highlighter);
        this.host.items[this.index].tabIndex = 1;
        this.host.items[this.index].focus();
    }

    @bound
    onKeydown(event: KeyboardEvent) {
        const key = event.key;
        match({ key })
            .with({ key: "ArrowDown" }, () => {
                this.index = Math.min(this.index + 1, this.host.items.length - 1);
                this.performUpdate();
            })
            .with({ key: "ArrowUp" }, () => {
                this.index = Math.max(this.index - 1, 0);
                this.performUpdate();
            })
            .with({ key: "Home" }, () => {
                this.index = 0;
                this.performUpdate();
            })
            .with({ key: "End" }, () => {
                this.index = this.host.items.length - 1;
                this.performUpdate();
            })
            .with({ key: " " }, () => {
                this.host.dispatchEvent(new KeyboardControllerSelectEvent(this.value));
            })
            .with({ key: "Enter" }, () => {
                this.host.dispatchEvent(new KeyboardControllerSelectEvent(this.value));
            })
            .with({ key: "Escape" }, () => {
                this.host.dispatchEvent(new KeyboardControllerEscapeEvent());
            });
    }
}
