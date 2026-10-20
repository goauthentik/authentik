import { MemoryStorage } from "#common/storage/shared";

import type { ReactiveElementHost } from "#elements/types";

import type { IdentificationStage } from "#flow/stages/identification/IdentificationStage";

import type { IdentificationChallenge } from "@goauthentik/api";

import { createRef } from "lit-html/directives/ref.js";
import { afterAll, beforeEach, describe, expect, it, vi } from "vitest";

const USER_KEY = "ak:remember_me:user";

const localStorage = new MemoryStorage();

vi.stubGlobal("self", { localStorage });
vi.stubGlobal("localStorage", localStorage);

// The keystroke listener defers its write to the next frame. Queue frames so tests can observe
// writes that are still pending, then run them with `flushFrames`.
const pendingFrames = new Map<number, FrameRequestCallback>();
let nextFrameID = 1;

vi.stubGlobal("requestAnimationFrame", (callback: FrameRequestCallback) => {
    const frameID = nextFrameID++;
    pendingFrames.set(frameID, callback);

    return frameID;
});

vi.stubGlobal("cancelAnimationFrame", (frameID: number) => {
    pendingFrames.delete(frameID);
});

function flushFrames() {
    const callbacks = [...pendingFrames.values()];
    pendingFrames.clear();

    for (const callback of callbacks) callback(0);
}

// Toggling on picks a field to focus by inspecting the document, which unit tests don't have.
vi.mock("#elements/utils/focus", () => ({
    findEmptyFocusCandidate: () => null,
}));

// Imported lazily so that the storage stubs above are in place when the module's
// `StorageAccessor` instances are created.
const { RememberMeController, RememberMeStorage } =
    await import("#flow/stages/identification/controllers/RememberMeController");

/**
 * A stand-in for the username `input`, since unit tests run without a DOM. Only the surface the
 * controller actually touches is implemented.
 */
function createUsernameField(value = "") {
    const inputListeners = new Set<(event: InputEvent) => void>();

    return {
        value,
        addEventListener(_type: string, listener: (event: InputEvent) => void) {
            inputListeners.add(listener);
        },
        removeEventListener(_type: string, listener: (event: InputEvent) => void) {
            inputListeners.delete(listener);
        },
        focus: vi.fn(),
        select: vi.fn(),

        /**
         * Simulate the user typing, dispatching an `input` event to whatever the controller bound.
         */
        type(nextValue: string) {
            this.value = nextValue;

            for (const listener of inputListeners) {
                listener({ target: this } as unknown as InputEvent);
            }
        },
    };
}

function createController(challenge?: Partial<IdentificationChallenge>) {
    const host = {
        challenge,
    } as ReactiveElementHost<IdentificationStage>;

    const identificationFieldRef = createRef<HTMLInputElement>();
    const usernameField = createUsernameField();

    identificationFieldRef.value = usernameField as unknown as HTMLInputElement;

    const controller = new RememberMeController(host, {
        pendingUserIdentifier: null,
        identificationFieldRef,
        passwordFieldRef: null,
        identificationFieldID: "identification",
    });

    return { controller, usernameField };
}

describe("RememberMeController", () => {
    beforeEach(() => {
        localStorage.clear();
        pendingFrames.clear();
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

    it("records keystrokes for a returning user who never re-toggles the switch", () => {
        localStorage.setItem(USER_KEY, "alice@example.com");

        const { controller, usernameField } = createController();

        expect(controller.defaultChecked).toBe(true);

        // Lit populates the field ref during render, so the controller binds on the first update.
        controller.hostUpdated();

        usernameField.type("bob@example.com");
        flushFrames();

        expect(localStorage.getItem(USER_KEY)).toBe("bob@example.com");
    });

    it("records keystrokes as soon as it is connected, without waiting for an update", () => {
        // The host adds the controller after it has rendered, so `hostUpdated` may never follow.
        localStorage.setItem(USER_KEY, "alice@example.com");

        const { controller, usernameField } = createController();

        controller.hostConnected();

        usernameField.type("bob@example.com");
        flushFrames();

        expect(localStorage.getItem(USER_KEY)).toBe("bob@example.com");
    });

    it("drops a pending keystroke write when the switch is toggled off", () => {
        localStorage.setItem(USER_KEY, "alice@example.com");

        const { controller, usernameField } = createController();

        controller.hostConnected();
        usernameField.type("bob@example.com");

        controller.toggleChangeListener({
            target: { checked: false },
        } as unknown as Event);

        flushFrames();

        expect(localStorage.getItem(USER_KEY)).toBeNull();
    });

    it("stops recording keystrokes once disconnected", () => {
        localStorage.setItem(USER_KEY, "alice@example.com");

        const { controller, usernameField } = createController();

        controller.hostConnected();
        usernameField.type("bob@example.com");

        controller.hostDisconnected();

        usernameField.type("carol@example.com");
        flushFrames();

        expect(localStorage.getItem(USER_KEY)).toBe("alice@example.com");
    });

    it("stops recording keystrokes once the switch is toggled off", () => {
        localStorage.setItem(USER_KEY, "alice@example.com");

        const { controller, usernameField } = createController();

        controller.hostUpdated();

        controller.toggleChangeListener({
            target: { checked: false },
        } as unknown as Event);

        usernameField.type("bob@example.com");
        flushFrames();

        expect(localStorage.getItem(USER_KEY)).toBeNull();
    });

    it("does not auto-submit once a returning user switches the toggle off", () => {
        localStorage.setItem(USER_KEY, "alice@example.com");

        const { controller, usernameField } = createController({ enableRememberMe: true });

        usernameField.value = "alice@example.com";

        expect(controller.canAutoSubmit()).toBe(true);

        controller.toggleChangeListener({
            target: { checked: false },
        } as unknown as Event);

        expect(controller.canAutoSubmit()).toBe(false);
    });

    it("does not auto-submit a first-time visitor who switches the toggle on", () => {
        const { controller, usernameField } = createController({ enableRememberMe: true });

        usernameField.value = "bob@example.com";

        controller.toggleChangeListener({
            target: { checked: true },
        } as unknown as Event);

        expect(controller.canAutoSubmit()).toBe(false);
    });

    it("does not record keystrokes for a first-time visitor", () => {
        const { controller, usernameField } = createController();

        expect(controller.defaultChecked).toBe(false);

        controller.hostUpdated();

        usernameField.type("bob@example.com");
        flushFrames();

        expect(localStorage.getItem(USER_KEY)).toBeNull();
    });
});
