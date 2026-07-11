import { expect, it } from "vitest";

it("runs in a real browser with a live custom element registry", () => {
    expect(typeof customElements.define).toBe("function");
    expect(typeof customElements.getName).toBe("function");
});
