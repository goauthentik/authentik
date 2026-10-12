import "#styles/interface.global.css";
import { RacInterface } from "./index.entrypoint";

import Guacamole from "guacamole-common-js";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { userEvent } from "vitest/browser";

describe("RacInterface clipboard", () => {
    let element: RacInterface;
    let viewport: HTMLElement;
    let tunnel: Guacamole.Tunnel;
    let messages: unknown[][];
    let readText: ReturnType<typeof vi.spyOn>;

    beforeEach(async () => {
        readText = vi.spyOn(navigator.clipboard, "readText").mockResolvedValue("");
        messages = [];
        tunnel = new Guacamole.Tunnel();
        tunnel.connect = vi.fn();
        tunnel.sendMessage = (...args: unknown[]) => messages.push(args);

        // Exercise the production connection lifecycle with an in-memory peer.
        vi.spyOn(Guacamole, "WebSocketTunnel").mockImplementation(function () {
            return tunnel as Guacamole.WebSocketTunnel;
        });

        element = new RacInterface();
        element.token = "clipboard-test";
        document.body.append(element);
        await element.updateComplete;
        tunnel.oninstruction?.("sync", ["1"]);
        await element.updateComplete;
        viewport = element.renderRoot.querySelector<HTMLElement>(".desktop-viewport")!;
        viewport.focus();
        await element.checkClipboard();
        messages.length = 0;
    });

    afterEach(async () => {
        element.remove();
        await userEvent.keyboard("{/Control}{/Shift}{/Meta}");
        vi.restoreAllMocks();
    });

    function clipboardText(): string {
        const bytes = messages
            .filter((message) => message[0] === "blob")
            .flatMap((message) => Array.from(atob(String(message[2])), (c) => c.charCodeAt(0)));

        return new TextDecoder().decode(new Uint8Array(bytes));
    }

    function paste(text: string): ClipboardEvent {
        const data = new DataTransfer();
        data.setData("text/plain", text);

        const event = new ClipboardEvent("paste", {
            clipboardData: data,
            bubbles: true,
            cancelable: true,
            composed: true,
        });

        viewport.dispatchEvent(event);

        return event;
    }

    async function copyInBrowser(text: string): Promise<void> {
        // Copy through a trusted shortcut without using the async Clipboard API.
        const source = document.createElement("textarea");
        source.value = text;
        document.body.append(source);
        source.focus();
        source.select();
        await userEvent.keyboard("{Control>}c{/Control}");
        source.remove();
        viewport.focus();
    }

    it("sends the first nonempty local text after an empty clipboard", async () => {
        readText.mockResolvedValue("Copied on the physical machine");

        await element.checkClipboard();

        expect(clipboardText()).toBe("Copied on the physical machine");
        expect(messages.some((message) => message[0] === "end")).toBe(true);
    });

    it("sends text that was already copied when the connection opened", async () => {
        element._previousClipboardValue = undefined;
        readText.mockResolvedValue("Copied before connecting");

        await element.checkClipboard();

        expect(clipboardText()).toBe("Copied before connecting");
    });

    it("allows the native paste shortcut through the Guacamole keyboard", () => {
        const event = new KeyboardEvent("keydown", {
            key: "v",
            code: "KeyV",
            keyCode: 86,
            ctrlKey: true,
            bubbles: true,
            cancelable: true,
        });

        viewport.dispatchEvent(event);

        expect(event.defaultPrevented).toBe(false);
        expect(messages).not.toContainEqual(["key", 118, 1]);
    });

    it("sends native clipboard text before one remote paste when reading is denied", () => {
        const text = "  中文 clipboard\r\nsecond line\t ";
        readText.mockRejectedValue(new DOMException("Clipboard reading denied", "NotAllowedError"));

        const event = paste(text);

        expect(event.defaultPrevented).toBe(true);
        expect(clipboardText()).toBe(text);
        expect(messages.filter((message) => message[0] === "clipboard")).toHaveLength(1);
        const end = messages.findIndex((message) => message[0] === "end");

        const key = messages.findIndex(
            (message) => message[0] === "key" && message[1] === 118 && message[2] === 1,
        );

        expect(end).toBeGreaterThanOrEqual(0);
        expect(key).toBeGreaterThan(end);
        expect(messages).toContainEqual(["key", 118, 0]);
        expect(messages).toContainEqual(["key", 0xffe3, 0]);
    });

    it("uses a real browser Ctrl+V paste when background reading is denied", async () => {
        await copyInBrowser("Native browser paste");
        readText.mockRejectedValue(new DOMException("Clipboard reading denied", "NotAllowedError"));

        await userEvent.keyboard("{Control>}v{/Control}");

        await vi.waitFor(() => expect(clipboardText()).toBe("Native browser paste"));

        expect(
            messages.filter(
                (message) => message[0] === "key" && message[1] === 118 && message[2] === 1,
            ),
        ).toHaveLength(1);
    });

    it("keeps native paste working after the file sidebar returns focus to the desktop", async () => {
        element.protocol = "rdp";
        element.driveEnabled = "true";
        await element.updateComplete;
        element.toggleFiles(true);
        await element.updateComplete;
        element.toggleFiles(false);
        await element.updateComplete;
        expect(element.shadowRoot!.activeElement).toBe(viewport);
        await copyInBrowser("Copied after closing the sidebar");
        readText.mockRejectedValue(new DOMException("Clipboard reading denied", "NotAllowedError"));

        await userEvent.keyboard("{Control>}v{/Control}");

        await vi.waitFor(() => expect(clipboardText()).toBe("Copied after closing the sidebar"));
    });

    it.each([
        { key: "v", code: "KeyV", ctrlKey: true },
        { key: "v", code: "KeyV", metaKey: true },
        { key: "Insert", code: "Insert", shiftKey: true },
    ])("allows the native paste shortcut $code with its platform modifier", (shortcut) => {
        const event = new KeyboardEvent("keydown", {
            ...shortcut,
            bubbles: true,
            cancelable: true,
        });

        viewport.dispatchEvent(event);
        paste("Platform shortcut text");

        viewport.dispatchEvent(
            new KeyboardEvent("keyup", {
                ...shortcut,
                bubbles: true,
                cancelable: true,
            }),
        );

        expect(event.defaultPrevented).toBe(false);
        expect(clipboardText()).toBe("Platform shortcut text");

        expect(
            messages.filter(
                (message) => message[0] === "key" && message[1] === 118 && message[2] === 1,
            ),
        ).toHaveLength(1);
    });

    it("preserves a large Unicode clipboard across multiple protocol blobs", () => {
        const text = "中文😀\r\n ".repeat(5000);

        paste(text);

        expect(clipboardText()).toBe(text);
        expect(messages.filter((message) => message[0] === "blob").length).toBeGreaterThan(1);
        expect(messages.filter((message) => message[0] === "end")).toHaveLength(1);
    });

    it("uses the Guacamole terminal paste shortcut for an SSH session", () => {
        element.protocol = "ssh";

        paste("Terminal paste");

        expect(clipboardText()).toBe("Terminal paste");

        expect(messages.filter((message) => message[0] === "key")).toEqual([
            ["key", 0xffe3, 1],
            ["key", 0xffe1, 1],
            ["key", 86, 1],
            ["key", 86, 0],
            ["key", 0xffe1, 0],
            ["key", 0xffe3, 0],
        ]);
    });

    it("sends the same local text again after reconnecting to a new remote clipboard", async () => {
        readText.mockResolvedValue("Copied before reconnecting");
        await element.checkClipboard();
        messages.length = 0;

        await element.firstUpdated();
        tunnel.oninstruction?.("sync", ["2"]);
        await element.updateComplete;
        await element.checkClipboard();

        expect(clipboardText()).toBe("Copied before reconnecting");
    });

    it("does not read or cache local text while disconnected", async () => {
        element.clientState = 5;
        readText.mockClear().mockResolvedValue("Copied while disconnected");

        await element.checkClipboard();

        expect(readText).not.toHaveBeenCalled();
        expect(messages.some((message) => message[0] === "clipboard")).toBe(false);
    });

    it("discards a pending read after a newer native paste", async () => {
        let resolveRead!: (value: string) => void;

        readText.mockImplementation(
            () =>
                new Promise<string>((resolve) => {
                    resolveRead = resolve;
                }),
        );

        const pending = element.checkClipboard();

        paste("New native paste");
        resolveRead("Stale clipboard text");
        await pending;

        expect(clipboardText()).toBe("New native paste");
        expect(messages.filter((message) => message[0] === "clipboard")).toHaveLength(1);
    });

    it("discards a pending read after the connection closes", async () => {
        let resolveRead!: (value: string) => void;

        readText.mockImplementation(
            () =>
                new Promise<string>((resolve) => {
                    resolveRead = resolve;
                }),
        );

        const pending = element.checkClipboard();

        element.remove();
        resolveRead("Copied before disconnecting");
        await pending;

        expect(messages.some((message) => message[0] === "clipboard")).toBe(false);
        expect(element._previousClipboardValue).toBeUndefined();
    });

    it("keeps a remote copy from being replaced by an older local read", async () => {
        const write = vi.spyOn(navigator.clipboard, "write").mockResolvedValue();
        let resolveRead!: (value: string) => void;

        readText.mockImplementation(
            () =>
                new Promise<string>((resolve) => {
                    resolveRead = resolve;
                }),
        );

        const pending = element.checkClipboard();

        tunnel.oninstruction?.("clipboard", ["8", "text/plain"]);
        tunnel.oninstruction?.("blob", ["8", btoa("Copied inside RDP")]);
        tunnel.oninstruction?.("end", ["8"]);
        resolveRead("Stale physical clipboard");
        await pending;

        await vi.waitFor(() => expect(write).toHaveBeenCalledOnce());
        const item = write.mock.calls[0][0][0];
        expect(await (await item.getType("text/plain")).text()).toBe("Copied inside RDP");
        expect(messages.some((message) => message[0] === "clipboard")).toBe(false);
        expect(element._previousClipboardValue).toBe("Copied inside RDP");
    });

    it("ignores empty remote clipboard updates without clearing the physical clipboard", () => {
        const write = vi.spyOn(navigator.clipboard, "write").mockResolvedValue();

        tunnel.oninstruction?.("clipboard", ["8", "text/plain"]);
        tunnel.oninstruction?.("end", ["8"]);

        expect(write).not.toHaveBeenCalled();
    });

    it("does not forward paste events from the local file sidebar", () => {
        const input = document.createElement("textarea");
        element.renderRoot.querySelector(".rac-toolbar")!.append(input);
        const data = new DataTransfer();
        data.setData("text/plain", "Local form text");

        input.dispatchEvent(
            new ClipboardEvent("paste", {
                clipboardData: data,
                bubbles: true,
                cancelable: true,
                composed: true,
            }),
        );

        expect(messages.some((message) => message[0] === "clipboard")).toBe(false);
    });
});
