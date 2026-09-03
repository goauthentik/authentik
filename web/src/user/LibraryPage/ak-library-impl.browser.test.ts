import "#user/LibraryPage/ak-library-impl";

import { type Application } from "@goauthentik/api";

import { describe, expect, it } from "vitest";

function app(name: string, pk: string): Application {
    return {
        pk,
        name,
        slug: name.toLowerCase(),
        launchUrl: `https://example.com/${name}`,
    } as Application;
}

/**
 * Mount the library with a fixed set of applications and return the search input.
 */
async function mount(apps: Application[]) {
    document.body.replaceChildren();

    const element = document.createElement("ak-library-impl");
    element.apps = apps;
    document.body.append(element);

    await element.updateComplete;

    const input = element.renderRoot.querySelector<HTMLInputElement>("#application-search-input");

    if (!input) throw new Error("Search input never rendered");

    return { element, input };
}

describe("ak-library-impl single-match auto-launch", () => {
    it("launches the single match when a search is committed from empty", async () => {
        // Two apps so the query has to narrow to one. The search starts empty,
        // which is what makes this the regression case: no row carries
        // `targetRef` until a query exists.
        const { element, input } = await mount([app("alpha", "pk-alpha"), app("zulu", "pk-zulu")]);

        // Patch the prototype rather than listening on the shadow root: a stale
        // `targetRef` can point at an element Lit has already detached, and a
        // click on a detached node reaches no ancestor listener.
        const clicked: string[] = [];
        const originalClick = HTMLElement.prototype.click;

        HTMLElement.prototype.click = function patched(this: HTMLElement) {
            const href = this.getAttribute("href") || this.tagName;

            clicked.push(`${href}${this.isConnected ? "" : " (detached)"}`);
        };

        input.value = "zulu";

        // `input` then `change` within a single task, which is what a real
        // keystroke-then-commit produces. Lit's re-render is scheduled on a
        // microtask, so it has not run when `change` is handled.
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.dispatchEvent(new Event("change", { bubbles: true }));

        // The launch is deferred to the render that binds the ref, so settle both.
        await element.updateComplete;
        await new Promise((resolve) => requestAnimationFrame(resolve));

        HTMLElement.prototype.click = originalClick;

        expect(clicked, "Auto-launch fires for the single visible match").toHaveLength(1);
        expect(clicked[0], "Auto-launch targets the filtered application").toContain("zulu");
    });
});
