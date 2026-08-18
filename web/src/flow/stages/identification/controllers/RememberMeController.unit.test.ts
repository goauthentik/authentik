import type { ReactiveElementHost } from "#elements/types";

import type { IdentificationStage } from "#flow/stages/identification/IdentificationStage";

import type { IdentificationChallenge } from "@goauthentik/api";

import { beforeEach, describe, expect, it, vi } from "vitest";

import { createRef } from "lit-html/directives/ref.js";

const USER_KEY = "authentik-remember-me-user";
const SESSION_KEY = "authentik-remember-me-session";

class MemoryStorage implements Storage {
    #items = new Map<string, string>();

    public get length() {
        return this.#items.size;
    }

    public key(index: number) {
        return [...this.#items.keys()][index] ?? null;
    }

    public getItem(key: string) {
        return this.#items.get(key) ?? null;
    }

    public setItem(key: string, value: string) {
        this.#items.set(key, value);
    }

    public removeItem(key: string) {
        this.#items.delete(key);
    }

    public clear() {
        this.#items.clear();
    }
}

const localStorage = new MemoryStorage();

vi.stubGlobal("self", { localStorage });
vi.stubGlobal("localStorage", localStorage);
vi.stubGlobal("document", { cookie: "authentik_csrf=NEWTOKEN0123456789" });

// Imported lazily so that the storage stubs above are in place when the module's
// `StorageAccessor` instances are created.
const { RememberMeController, RememberMeStorage } =
    await import("#flow/stages/identification/controllers/RememberMeController");

function createController(challenge?: Partial<IdentificationChallenge>) {
    const host = {
        challenge,
    } as ReactiveElementHost<IdentificationStage>;

    return new RememberMeController(host, {
        pendingUserIdentifier: null,
        identificationFieldRef: createRef<HTMLInputElement>(),
        passwordFieldRef: null,
        identificationFieldID: "identification",
    });
}

describe("RememberMeController", () => {
    beforeEach(() => {
        localStorage.clear();
    });

    it("prefills the remembered username", () => {
        localStorage.setItem(USER_KEY, "user@example.com");

        const controller = createController();

        expect(controller.defaultUserIdentification).toBe("user@example.com");
        expect(controller.defaultChecked).toBe(true);
    });

    it("keeps the remembered username after the CSRF token rotates", () => {
        // Django rotates the CSRF token on every successful login, so a session ID derived
        // from it never matches on the next visit. The remembered username must survive.
        localStorage.setItem(USER_KEY, "user@example.com");
        localStorage.setItem(SESSION_KEY, "OLDTOKEN");

        const controller = createController();

        expect(controller.defaultUserIdentification).toBe("user@example.com");
        expect(controller.defaultChecked).toBe(true);
        expect(localStorage.getItem(USER_KEY)).toBe("user@example.com");
    });

    it("discards the legacy session ID written by earlier versions", () => {
        localStorage.setItem(USER_KEY, "user@example.com");
        localStorage.setItem(SESSION_KEY, "OLDTOKEN");

        createController();

        expect(localStorage.getItem(SESSION_KEY)).toBeNull();
    });

    it("falls back to the challenge's pending user identifier", () => {
        const controller = createController({ pendingUserIdentifier: "pending@example.com" });

        expect(controller.defaultUserIdentification).toBe("pending@example.com");
        expect(controller.defaultChecked).toBe(false);
    });

    it("clears the remembered username on an explicit reset", () => {
        localStorage.setItem(USER_KEY, "user@example.com");

        RememberMeStorage.reset();

        expect(createController().defaultUserIdentification).toBeNull();
        expect(createController().defaultChecked).toBe(false);
    });
});
