import "#styles/interface.global.css";
import { FileSidebar } from "./FileSidebar";
import { RacInterface } from "./index.entrypoint";

import Guacamole from "guacamole-common-js";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { page, userEvent } from "vitest/browser";

// Exercise the real layout and keyboard handlers without connecting to a remote host.
class RacLayoutFixture extends RacInterface {
    async firstUpdated(): Promise<void> {
        this.initViewport();
    }
    async checkClipboard(): Promise<void> {
        // Clipboard polling is unrelated to this disconnected layout fixture.
    }
}

customElements.define("ak-rac-layout-fixture", RacLayoutFixture);

async function settleLayout(): Promise<void> {
    // Allow ResizeObserver to observe both opening and closing layout changes.
    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
}

describe("RAC file sidebar", () => {
    let element: RacLayoutFixture;
    let sidebar: FileSidebar;
    let tunnel: Guacamole.Tunnel;
    let messages: unknown[][];

    beforeEach(async () => {
        await page.viewport(1280, 800);
        element = new RacLayoutFixture();
        element.deviceName = "RDP test session";
        element.protocol = "rdp";
        element.driveEnabled = "true";
        messages = [];
        tunnel = new Guacamole.Tunnel();
        tunnel.sendMessage = (...args: unknown[]) => messages.push(args);
        element.client = new Guacamole.Client(tunnel);
        element.client.connect("");
        tunnel.oninstruction?.("sync", ["1"]);
        element.clientState = 3;
        document.body.append(element);
        await element.updateComplete;
        sidebar = element.renderRoot.querySelector<FileSidebar>("ak-rac-file-sidebar")!;

        const drive = {
            ready: true,
            path: "/",
            loading: false,
            entries: [
                { name: "Documents", path: "/Documents", directory: true },
                { name: "report.pdf", path: "/report.pdf", directory: false, size: 123456 },
                { name: "empty.txt", path: "/empty.txt", directory: false, size: 0 },
            ],
        };

        Object.assign(element, { drive });
        await element.updateComplete;
        await sidebar.updateComplete;

        await vi.waitFor(() =>
            expect(messages.some((message) => message[0] === "size")).toBe(true),
        );

        messages.length = 0;
    });

    afterEach(() => element.remove());

    it("shows the device name supplied by the connection page", async () => {
        element.setAttribute("device-name", "Device inventory desktop");
        await element.updateComplete;

        expect(element.renderRoot.querySelector(".endpoint-name")?.textContent).toBe(
            "Device inventory desktop",
        );
    });

    it("releases transfers once and waits before reconnecting", async () => {
        const disposeBrowser = vi.fn();
        const disposeTransfers = vi.fn();

        Object.assign(element, {
            fileBrowser: { dispose: disposeBrowser },
            fileTransfers: { dispose: disposeTransfers },
        });

        const reconnect = vi.spyOn(element, "firstUpdated").mockResolvedValue();

        vi.useFakeTimers();

        try {
            element.reconnect();
            element.reconnect();
            expect(element.clientState).toBe(2);
            expect(disposeBrowser).toHaveBeenCalledOnce();
            expect(disposeTransfers).toHaveBeenCalledOnce();
            expect(reconnect).not.toHaveBeenCalled();
            await vi.advanceTimersByTimeAsync(500);
            expect(reconnect).toHaveBeenCalledOnce();
        } finally {
            vi.useRealTimers();
            reconnect.mockRestore();
        }
    });

    it("floats without changing desktop size or sending resize instructions", async () => {
        const panel = element.renderRoot.querySelector<HTMLElement>(".files-panel")!;
        const desktop = element.renderRoot.querySelector<HTMLElement>(".desktop-viewport")!;
        const original = desktop.getBoundingClientRect();
        expect(panel.hidden).toBe(true);
        element.renderRoot.querySelector<HTMLButtonElement>(".files-toggle")!.click();
        await element.updateComplete;
        expect(panel.hidden).toBe(false);
        await settleLayout();
        expect(desktop.getBoundingClientRect().width).toBe(original.width);
        expect(desktop.getBoundingClientRect().height).toBe(original.height);
        expect(panel.getBoundingClientRect().left).toBeLessThan(original.right);
        expect(getComputedStyle(panel).position).toBe("absolute");
        expect(messages.some((message) => message[0] === "size")).toBe(false);

        expect(
            sidebar.renderRoot
                .querySelector<HTMLInputElement>("input[type=file]")!
                .getBoundingClientRect().width,
        ).toBe(0);

        expect(sidebar.renderRoot.querySelector("[webkitdirectory], [directory]")).toBeNull();

        expect(
            sidebar.renderRoot.querySelectorAll("tbody button[aria-label^='Download']"),
        ).toHaveLength(2);

        element.toggleFiles(false);
        await element.updateComplete;
        await settleLayout();
        expect(panel.hidden).toBe(true);
        expect(desktop.getBoundingClientRect().width).toBe(original.width);
        expect(desktop.getBoundingClientRect().height).toBe(original.height);
        expect(messages.some((message) => message[0] === "size")).toBe(false);
    });

    it("keeps sidebar keys local and restores desktop keyboard input after closing", async () => {
        element.toggleFiles(true);
        await element.updateComplete;
        const close = sidebar.renderRoot.querySelector<HTMLButtonElement>("header button")!;

        close.dispatchEvent(
            new KeyboardEvent("keydown", {
                key: "a",
                code: "KeyA",
                keyCode: 65,
                bubbles: true,
                composed: true,
            }),
        );

        expect(messages.some((message) => message[0] === "key")).toBe(false);

        close.dispatchEvent(
            new KeyboardEvent("keydown", { key: "Escape", bubbles: true, composed: true }),
        );

        await element.updateComplete;
        const desktop = element.renderRoot.querySelector<HTMLElement>(".desktop-viewport")!;
        expect(element.shadowRoot!.activeElement).toBe(desktop);
        await userEvent.keyboard("{a>}");
        await vi.waitFor(() => expect(messages).toContainEqual(["key", 97, 1]));
        desktop.blur();
        expect(messages).toContainEqual(["key", 97, 0]);
        await userEvent.keyboard("{/a}");
    });

    it("fits narrow screens without resizing the desktop when opened", async () => {
        await page.viewport(600, 800);

        // Browser resizing should still update the remote resolution.
        await vi.waitFor(() =>
            expect(messages.some((message) => message[0] === "size")).toBe(true),
        );

        messages.length = 0;
        const desktop = element.renderRoot.querySelector<HTMLElement>(".desktop-viewport")!;
        const original = desktop.getBoundingClientRect();
        element.toggleFiles(true);
        await element.updateComplete;
        await settleLayout();

        const panel = element.renderRoot
            .querySelector<HTMLElement>(".files-panel")!
            .getBoundingClientRect();

        expect(panel.left).toBeGreaterThanOrEqual(original.left);
        expect(panel.right).toBeLessThanOrEqual(original.right);
        expect(panel.top).toBeGreaterThanOrEqual(original.top);
        expect(panel.bottom).toBeLessThanOrEqual(original.bottom);
        expect(desktop.getBoundingClientRect().width).toBe(original.width);
        expect(desktop.getBoundingClientRect().height).toBe(original.height);
        expect(messages.some((message) => message[0] === "size")).toBe(false);
    });
});
