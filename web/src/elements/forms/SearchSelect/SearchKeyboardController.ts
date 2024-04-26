import { bound } from "@goauthentik/elements/decorators/bound.js";
import { match } from "ts-pattern";

import { LitElement, ReactiveController, ReactiveControllerHost } from "lit";

type ReactiveElementHost = Partial<ReactiveControllerHost> & LitElement;
type ValuedHtmlElement = HTMLElement & { value: string };

export class KeyboardControllerSelectEvent extends Event {
    static EVENT_NAME = "ak-keyboard-controller-select";
    value: string | undefined;
    constructor(value: string | undefined) {
        super(KeyboardControllerSelectEvent.EVENT_NAME, { composed: true, bubbles: true });
        this.value = value;
    }
}

export class KeyboardControllerCloseEvent extends Event {
    static EVENT_NAME = "ak-keyboard-controller-close";
    constructor(value) {
        super(KeyboardControllerCloseEvent.EVENT_NAME, { composed: true, bubbles: true });
    }
}

export class AkKeyboardController implements ReactiveController {
    private host: ReactiveElementHost;

    private index: number = 0;

    private selector: string;

    private highlighter: string;

    private items: ValuedHtmlElement[];

    constructor(host, selector = ".ak-select-item", highlighter = ".ak-highlight-item") {
        this.host = host;
        host.addController(this);
        this.selector = selector[0] === "." ? selector : `.${selector}`;
        this.highlighter = highlighter.replace(/^\./, "");
    }

    hostUpdated() {
        this.items = Array.from(this.host.renderRoot.querySelectorAll(this.selector));
        // If the update changed the number of items such that our index is greater than the count,
        // bring the index in.
        this.index = Math.min(this.index, this.items.length - 1);
    }

    hostConnected() {
        this.host.addEventListener("keydown", this.onKeydown);
    }

    hostDisconnected() {
        this.host.removeEventListener("keydown", this.onKeydown);
    }

    get current() {
        return this.items[index];
    }

    get value() {
        return this.current?.value;
    }

    set value(v: string) {
        const index = this.items.findIndex((i) => i.value === v);
        if (index !== undefined) {
            this.index = index;
            this.performUpdate();
            this.host.dispatchEvent(new KeyboardControllerSelectEvent(v));
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

declare global {
    interface GlobalEventHandlersEventMap {
        "ak-keyboard-controller-select": KeyboardControllerSelectEvent;
        "ak-keyboard-controller-close": KeyboardControllerCloseEvent;
    }
}
