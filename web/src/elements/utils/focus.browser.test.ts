import { findEmptyFocusCandidate } from "#elements/utils/focus";

import { afterEach, beforeEach, describe, expect, it } from "vitest";

describe("findEmptyFocusCandidate", () => {
    let host: HTMLElement;
    let username: HTMLInputElement;
    let password: HTMLInputElement;

    beforeEach(() => {
        host = document.createElement("div");
        const root = host.attachShadow({ mode: "open", delegatesFocus: true });

        username = document.createElement("input");
        username.type = "text";
        username.required = true;

        password = document.createElement("input");
        password.type = "password";
        password.required = true;

        root.append(username, password);
        document.body.append(host);
    });

    afterEach(() => {
        host.remove();
    });

    it("returns the first blank required input when nothing is focused", () => {
        expect(findEmptyFocusCandidate(username, password)).toBe(username);
    });

    it("does not redirect focus away from a focused input inside a shadow root", () => {
        password.focus();

        // The document only sees the shadow host as the active element.
        expect(document.activeElement).toBe(host);
        expect(host.shadowRoot?.activeElement).toBe(password);

        expect(findEmptyFocusCandidate(username, password)).toBeNull();
    });

    it("still skips the focused input when the other field is the blank one", () => {
        username.value = "user";
        username.focus();

        expect(findEmptyFocusCandidate(username, password)).toBeNull();
    });
});
