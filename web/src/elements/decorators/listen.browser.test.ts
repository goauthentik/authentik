import { listen } from "#elements/decorators/listen";

import { afterEach, describe, expect, it } from "vitest";

import { html, LitElement } from "lit";

class ListeningElement extends LitElement {
    public ownClicks = 0;
    public windowResizes = 0;

    protected clickListener = () => {
        this.ownClicks += 1;
    };

    protected resizeListener = () => {
        this.windowResizes += 1;
    };

    render() {
        return html`<button>Child</button>`;
    }
}

listen("click")(ListeningElement.prototype, "clickListener");
listen("resize", { target: window })(ListeningElement.prototype, "resizeListener");

customElements.define("ak-test-listening-element", ListeningElement);

class ExtendedListeningElement extends ListeningElement {
    public keydowns = 0;

    protected keydownListener = () => {
        this.keydowns += 1;
    };
}

listen("keydown")(ExtendedListeningElement.prototype, "keydownListener");

customElements.define("ak-test-extended-listening-element", ExtendedListeningElement);

class MethodListeningElement extends LitElement {
    public receivedBy: unknown = null;

    protected resizeListener(): void {
        this.receivedBy = this;
    }
}

listen("resize", { target: window })(MethodListeningElement.prototype, "resizeListener");

customElements.define("ak-test-method-listening-element", MethodListeningElement);

const mounted = new Set<HTMLElement>();

async function mount<T extends LitElement>(element: T): Promise<T> {
    document.body.appendChild(element);
    mounted.add(element);
    await element.updateComplete;

    return element;
}

afterEach(() => {
    for (const element of mounted) element.remove();
    mounted.clear();
});

describe("@listen", () => {
    it("listens on the element itself by default, including events from its descendants", async () => {
        const element = await mount(new ListeningElement());

        element.dispatchEvent(new Event("click"));

        element.renderRoot
            .querySelector("button")!
            .dispatchEvent(new Event("click", { bubbles: true, composed: true }));

        window.dispatchEvent(new Event("click"));

        expect(element.ownClicks, "Own and bubbled clicks count, window clicks don't").toBe(2);
    });

    it("listens on the given target and stops when the element disconnects", async () => {
        const element = await mount(new ListeningElement());

        window.dispatchEvent(new Event("resize"));
        element.remove();
        window.dispatchEvent(new Event("resize"));

        expect(element.windowResizes, "Only the resize while connected counts").toBe(1);
    });

    it("does not stack listeners when the element reconnects", async () => {
        const element = await mount(new ListeningElement());

        element.remove();
        document.body.appendChild(element);
        window.dispatchEvent(new Event("resize"));

        expect(element.windowResizes, "One listener after reconnecting").toBe(1);
    });

    it("registers a parent's listeners once when a subclass adds its own", async () => {
        const element = await mount(new ExtendedListeningElement());

        element.dispatchEvent(new Event("click"));
        element.dispatchEvent(new Event("keydown"));
        window.dispatchEvent(new Event("resize"));

        expect(element.ownClicks, "Inherited element listener fires once").toBe(1);
        expect(element.windowResizes, "Inherited window listener fires once").toBe(1);
        expect(element.keydowns, "Subclass listener fires").toBe(1);

        element.remove();
        window.dispatchEvent(new Event("resize"));

        expect(element.windowResizes, "Inherited window listener is removed on disconnect").toBe(1);
    });

    it("calls plain methods with the element as `this`", async () => {
        const element = await mount(new MethodListeningElement());

        window.dispatchEvent(new Event("resize"));

        expect(element.receivedBy, "`this` is the element, not the window").toBe(element);
    });
});
