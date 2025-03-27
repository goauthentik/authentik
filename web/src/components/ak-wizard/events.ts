export type NavigationUpdate = {
    disabled?: string[];
    enable?: string | string[];
    hidden?: string[];
};

export class WizardNavigationEvent<D extends string = string> extends Event {
    static readonly eventName = "ak-wizard-navigation";

    destination?: D;
    details?: NavigationUpdate;

    constructor(destination?: D, details?: NavigationUpdate) {
        super(WizardNavigationEvent.eventName, { bubbles: true, composed: true });
        this.destination = destination;
        this.details = details;
    }

    /**
     * Given an event target, bind the destination and details for dispatching.
     */
    static toListener<D extends string = string>(
        target: EventTarget,
        destination: D,
        details?: NavigationUpdate,
    ) {
        const wizardNavigationListener = (event?: Event) => {
            event?.preventDefault?.();

            return target.dispatchEvent(new WizardNavigationEvent(destination, details));
        };

        return wizardNavigationListener;
    }
}

export class WizardUpdateEvent<T> extends Event {
    static readonly eventName = "ak-wizard-update";

    content: T;

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
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        [WizardUpdateEvent.eventName]: WizardUpdateEvent<any>;
        [WizardCloseEvent.eventName]: WizardCloseEvent;
    }
}
