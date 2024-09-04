import { WizardButton } from "./types";

export class WizardNavigationEvent extends Event {
    static readonly eventName = "authentik.wizard.navigation";
    command: WizardButton;
    constructor(button: WizardButton) {
        super(WizardNavigationEvent.eventName, { bubbles: true, composed: true });
        this.command = button;
    }
}

export class WizardUpdateEvent<T> extends Event {
    static readonly eventName = "authentik.wizard.update";
    content: T;
    constructor(content: T) {
        super(WizardUpdateEvent.eventName, { bubbles: true, composed: true });
        this.content = content;
    }
}

export class WizardCloseEvent extends Event {
    static readonly eventName = "authentik.wizard.closed";
    constructor() {
        super(WizardCloseEvent.eventName, { bubbles: true, composed: true });
    }
}

declare global {
    interface GlobalEventHandlersEventMap {
        [WizardNavigationEvent.eventName]: WizardNavigationEvent;
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        [WizardUpdateEvent.eventName]: WizardUpdateEvent<any>;
        [WizardCloseEvent.eventName]: WizardCloseEvent;
    }
}
