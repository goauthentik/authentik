import { bound } from "@goauthentik/elements/decorators/bound.js";
import { match } from "ts-pattern";

import { LitElement, ReactiveController, ReactiveControllerHost } from "lit";

import {
    KeyboardControllerCloseEvent,
    KeyboardControllerSelectEvent,
} from "./SearchKeyboardControllerEvents.js";

type ReactiveElementHost = Partial<ReactiveControllerHost> & LitElement & { value?: string };
type ValuedHtmlElement = HTMLElement & { value: string };

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

    private selector: string;

    private highlighter: string;

    private items: ValuedHtmlElement[] = [];

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
    constructor(
        host: ReactiveElementHost,
        selector = ".ak-select-item",
        highlighter = ".ak-highlight-item",
    ) {
        this.host = host;
        host.addController(this);
        this.selector = selector[0] === "." ? selector : `.${selector}`;
        this.highlighter = highlighter.replace(/^\./, "");
    }

    hostUpdated() {
        this.items = Array.from(this.host.renderRoot.querySelectorAll(this.selector));
        const current = this.items.findIndex((item) => item.value === this.host.value);
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
        this.items[this.index].focus();
    }

    get current() {
        return this.items[this.index];
    }

    get value() {
        return this.current?.value;
    }

    set value(v: string) {
        const index = this.items.findIndex((i) => i.value === v);
        if (index !== undefined) {
            this.index = index;
            this.performUpdate();
        }
    }

    private performUpdate() {
        const items = this.items;
        items.forEach((item) => {
            item.classList.remove(this.highlighter);
            item.tabIndex = -1;
        });
        items[this.index].classList.add(this.highlighter);
        items[this.index].tabIndex = 0;
        items[this.index].focus();
    }

    @bound
    onKeydown(event: KeyboardEvent) {
        const key = event.key;
        match({ key })
            .with({ key: "ArrowDown" }, () => {
                this.index = Math.min(this.index + 1, this.items.length - 1);
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
                this.index = this.items.length - 1;
                this.performUpdate();
            })
            .with({ key: " " }, () => {
                this.host.dispatchEvent(new KeyboardControllerSelectEvent(this.value));
            })
            .with({ key: "Enter" }, () => {
                this.host.dispatchEvent(new KeyboardControllerSelectEvent(this.value));
            })
            .with({ key: "Escape" }, () => {
                this.host.dispatchEvent(new KeyboardControllerCloseEvent());
            });
    }
}
