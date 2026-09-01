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

/**
 * Records what the render root actually contained at the moment the hook fired,
 * rather than what it contains once the test gets around to looking.
 */
class TestDiagram extends Diagram {
    public observed: string[] = [];

    protected override diagramRendered(): void {
        this.observed.push(this.renderRoot.querySelector("svg")?.tagName ?? "no-svg");
    }
}

customElements.define("ak-test-diagram", TestDiagram);

describe("ak-diagram", () => {
    it("invokes diagramRendered once the SVG is committed to the render root", async () => {
        const element = mount(new TestDiagram());

        element.diagram = 'graph TD\nn0["Alpha"]\nn1["Beta"]\nn0 --> n1';

        await vi.waitFor(() => expect(element.observed).toStrictEqual(["svg"]));
    });

    it("invokes diagramRendered again when the diagram changes", async () => {
        const element = mount(new TestDiagram());

        element.diagram = 'graph TD\nn0["Alpha"]';
        await vi.waitFor(() => expect(element.observed).toHaveLength(1));

        element.diagram = 'graph TD\nn0["Alpha"]\nn1["Beta"]\nn0 --> n1';
        await vi.waitFor(() => expect(element.observed).toStrictEqual(["svg", "svg"]));
    });
});
