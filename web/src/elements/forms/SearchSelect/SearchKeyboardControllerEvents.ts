export class KeyboardControllerSelectEvent extends Event {
    static readonly eventName = "ak-keyboard-controller-select";
    value: string | undefined;
    constructor(value: string | undefined) {
        super(KeyboardControllerSelectEvent.eventName, { composed: true, bubbles: true });
        this.value = value;
    }
}

export class KeyboardControllerEscapeEvent extends Event {
    static readonly eventName = "ak-keyboard-controller-escape";
    constructor() {
        super("ak-keyboard-controller-escape", { composed: true, bubbles: true });
    }
}

declare global {
    interface GlobalEventHandlersEventMap {
        [KeyboardControllerSelectEvent.eventName]: KeyboardControllerSelectEvent;
        [KeyboardControllerEscapeEvent.eventName]: KeyboardControllerEscapeEvent;
    }
}
