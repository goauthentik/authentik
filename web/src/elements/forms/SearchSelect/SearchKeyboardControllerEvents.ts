export class KeyboardControllerSelectEvent extends Event {
    value: string | undefined;
    constructor(value: string | undefined) {
        super("ak-keyboard-controller-select", { composed: true, bubbles: true });
        this.value = value;
    }
}

export class KeyboardControllerCloseEvent extends Event {
    constructor() {
        super("ak-keyboard-controller-close", { composed: true, bubbles: true });
    }
}

declare global {
    interface GlobalEventHandlersEventMap {
        "ak-keyboard-controller-select": KeyboardControllerSelectEvent;
        "ak-keyboard-controller-close": KeyboardControllerCloseEvent;
    }
}
