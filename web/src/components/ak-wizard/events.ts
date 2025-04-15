/**
 * Initialization options for a wizard navigation event.
 */
export interface NavigationEventInit {
    disabled?: string[];
    enable?: string | string[];
    hidden?: string[];
}

/**
 * Event dispatched when the wizard navigation is updated.
 */
export class WizardNavigationEvent<D extends string = string> extends Event {
    static readonly eventName = "ak-wizard-navigation";

    public readonly destination?: D;
    public readonly details?: NavigationEventInit;

    constructor(destination?: D, init?: NavigationEventInit) {
        super(WizardNavigationEvent.eventName, { bubbles: true, composed: true });
        this.destination = destination;
        this.details = init;
    }

    /**
     * Given an event target, bind the destination and details for dispatching.
     */
    static toListener<D extends string = string>(
        target: EventTarget,
        destination: D,
        init?: NavigationEventInit,
    ) {
        const wizardNavigationListener = (event?: Event) => {
            event?.preventDefault?.();

            return target.dispatchEvent(new this(destination, init));
        };

        return wizardNavigationListener;
    }
}

export class WizardUpdateEvent<T> extends Event {
    static readonly eventName = "ak-wizard-update";

    public readonly content: T;

    constructor(content: T) {
        super(WizardUpdateEvent.eventName, { bubbles: true, composed: true });
        this.content = content;
    }
}

export class WizardCloseEvent extends Event {
    static readonly eventName = "ak-wizard-close";

    constructor() {
        super(WizardCloseEvent.eventName, { bubbles: true, composed: true });
    }
}

declare global {
    interface GlobalEventHandlersEventMap {
        [WizardNavigationEvent.eventName]: WizardNavigationEvent;
        [WizardUpdateEvent.eventName]: WizardUpdateEvent<never>;
        [WizardCloseEvent.eventName]: WizardCloseEvent;
    }
}
