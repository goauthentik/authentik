import "#elements/Diagram/ak-diagram";

import { Diagram } from "#elements/Diagram/ak-diagram";

import { afterEach, describe, expect, it, vi } from "vitest";

const mounted = new Set<HTMLElement>();

function mount<T extends HTMLElement>(element: T): T {
    const container = document.body.appendChild(document.createElement("div"));

    mounted.add(container);
    container.appendChild(element);

    return element;
}

afterEach(() => {
    mounted.forEach((container) => container.remove());
    mounted.clear();
});

class TestDiagram extends Diagram {
    public observed: string[] = [];

    protected override diagramUpdated(): void {
        this.observed.push(this.renderRoot.querySelector("svg")?.tagName ?? "no-svg");
    }
}

class CallbackTestClass {
    public observed: string[] = [];

    invoke = (diagram: Diagram) => {
        this.observed.push(diagram.renderRoot.querySelector("svg")?.tagName ?? "no-svg");
    };
}

customElements.define("ak-test-diagram", TestDiagram);

describe("ak-diagram", () => {
    it("invokes diagramUpdated after the SVG is made visible", async () => {
        const element = mount(new TestDiagram());

        element.diagram = 'graph TD\nn0["Alpha"]\nn1["Beta"]\nn0 --> n1';

        await vi.waitFor(() => expect(element.observed).toStrictEqual(["svg"]));
    });

    it("invokes diagramUpdated again when the diagram changes", async () => {
        const element = mount(new TestDiagram());

        element.diagram = 'graph TD\nn0["Alpha"]';
        await vi.waitFor(() => expect(element.observed).toHaveLength(1));

        element.diagram = 'graph TD\nn0["Alpha"]\nn1["Beta"]\nn0 --> n1';
        await vi.waitFor(() => expect(element.observed).toStrictEqual(["svg", "svg"]));
    });

    it("invokes diagramUpdatedCallback on a function after the SVG is rendered", async () => {
        const element = mount(new Diagram());
        const observed: string[] = [];

        element.diagramUpdatedCallback = (diagram: Diagram) =>
            observed.push(diagram.renderRoot.querySelector("svg")?.tagName ?? "no-svg");

        element.diagram = 'graph TD\nn0["Alpha"]';
        await vi.waitFor(() => expect(observed).toHaveLength(1));

        element.diagram = 'graph TD\nn0["Alpha"]\nn1["Beta"]\nn0 --> n1';
        await vi.waitFor(() => expect(observed).toStrictEqual(["svg", "svg"]));
    });

    it("invokes diagramUpdatedCallback on a method after the SVG is rendered", async () => {
        const callback = new CallbackTestClass();
        const element = mount(new Diagram());
        element.diagramUpdatedCallback = callback.invoke;

        element.diagram = 'graph TD\nn0["Alpha"]';
        await vi.waitFor(() => expect(callback.observed).toHaveLength(1));

        element.diagram = 'graph TD\nn0["Alpha"]\nn1["Beta"]\nn0 --> n1';
        await vi.waitFor(() => expect(callback.observed).toStrictEqual(["svg", "svg"]));
    });
});
