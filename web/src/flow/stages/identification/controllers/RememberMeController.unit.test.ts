import { MemoryStorage } from "#common/storage/shared";

import type { ReactiveElementHost } from "#elements/types";

import type { IdentificationStage } from "#flow/stages/identification/IdentificationStage";

import type { IdentificationChallenge } from "@goauthentik/api";

import { createRef } from "lit-html/directives/ref.js";
import { afterAll, beforeEach, describe, expect, it, vi } from "vitest";

const USER_KEY = "ak:remember_me:user";
const SESSION_KEY = "ak:remember_me:session";
const LEGACY_USER_KEY = "authentik-remember-me-user";
const LEGACY_SESSION_KEY = "authentik-remember-me-session";

const localStorage = new MemoryStorage();

vi.stubGlobal("self", { localStorage });
vi.stubGlobal("localStorage", localStorage);

// The session ID is derived from the CSRF cookie, which unit tests don't have.
vi.mock("#common/api/csrf", () => ({
    readCSRFToken: () => "CSRFTOKEN",
}));

// Imported lazily so that the storage stubs above are in place when the module's
// `StorageAccessor` instances are created.
const { RememberMeController, RememberMeStorage } =
    await import("#flow/stages/identification/controllers/RememberMeController");

function createController(challenge?: Partial<IdentificationChallenge>) {
    const host = {
        challenge,
    } as ReactiveElementHost<IdentificationStage>;

    const controller = new RememberMeController(host, {
        pendingUserIdentifier: null,
        identificationFieldRef: createRef<HTMLInputElement>(),
        passwordFieldRef: null,
        identificationFieldID: "identification",
    });

    return { controller };
}

describe("RememberMeController", () => {
    beforeEach(() => {
        localStorage.clear();
    });

    afterAll(() => {
        vi.unstubAllGlobals();
    });

    it("prefills the remembered username", () => {
        localStorage.setItem(USER_KEY, "user@example.com");

        const { controller } = createController();

        expect(controller.defaultUserIdentification).toBe("user@example.com");
        expect(controller.defaultChecked).toBe(true);
    });

    it("moves a username remembered by earlier versions to the current key", () => {
        localStorage.setItem(LEGACY_USER_KEY, "user@example.com");

        const { controller } = createController();

        expect(controller.defaultUserIdentification).toBe("user@example.com");
        expect(controller.defaultChecked).toBe(true);
        expect(localStorage.getItem(USER_KEY)).toBe("user@example.com");
        expect(localStorage.getItem(LEGACY_USER_KEY)).toBeNull();
    });

    it("prefers the current key over a leftover legacy username", () => {
        localStorage.setItem(USER_KEY, "current@example.com");
        localStorage.setItem(LEGACY_USER_KEY, "stale@example.com");

        const { controller } = createController();

        expect(controller.defaultUserIdentification).toBe("current@example.com");
        expect(localStorage.getItem(LEGACY_USER_KEY)).toBeNull();
    });

    it("moves the session ID written by earlier versions to the current key", () => {
        localStorage.setItem(LEGACY_SESSION_KEY, "CSRFTOKE");

        createController();

        expect(localStorage.getItem(SESSION_KEY)).toBe("CSRFTOKE");
        expect(localStorage.getItem(LEGACY_SESSION_KEY)).toBeNull();
    });

    it("falls back to the challenge's pending user identifier", () => {
        const { controller } = createController({ pendingUserIdentifier: "pending@example.com" });

        expect(controller.defaultUserIdentification).toBe("pending@example.com");
        expect(controller.defaultChecked).toBe(false);
    });

    it("clears the remembered username on an explicit reset", () => {
        localStorage.setItem(USER_KEY, "user@example.com");

        RememberMeStorage.reset();

        expect(createController().controller.defaultUserIdentification).toBeNull();
        expect(createController().controller.defaultChecked).toBe(false);
    });
});
