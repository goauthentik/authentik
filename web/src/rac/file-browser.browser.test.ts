import { FileBrowser, parentPath } from "./file-browser";

import { RacApi } from "@goauthentik/api";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

describe("redirected-drive file browser", () => {
    let browser: FileBrowser;
    const download = vi.fn();
    let list: ReturnType<typeof vi.spyOn>;

    beforeEach(() => {
        download.mockReset();
        list = vi.spyOn(RacApi.prototype, "racFilesListCreate");

        list.mockResolvedValue({
            entries: [
                { name: "docs", path: "/docs", kind: "directory", size: null },
                { name: "empty.txt", path: "/empty.txt", kind: "file", size: 0 },
            ],
            cursor: "",
        });

        browser = new FileBrowser({ download }, "token", "connection", () => {});
    });

    afterEach(() => {
        browser.dispose();
        vi.restoreAllMocks();
    });

    it("lists shared-drive entries with sizes and downloads only on request", async () => {
        browser.start();
        await vi.waitFor(() => expect(browser.state.loading).toBe(false));
        expect(browser.state.ready).toBe(true);
        expect(browser.state.entries[1].size).toBe(0);

        expect(list).toHaveBeenCalledWith(
            { fileListQueryRequest: { token: "token", connection: "connection", path: "/" } },
            expect.anything(),
        );

        expect(download).not.toHaveBeenCalled();
        browser.download(browser.state.entries[0]);
        expect(download).not.toHaveBeenCalled();
        browser.download(browser.state.entries[1]);
        expect(download).toHaveBeenCalledWith("/empty.txt", 0);
    });

    it("requests pages by cursor and navigates folders", async () => {
        list.mockResolvedValueOnce({
            entries: [{ name: "a", path: "/a", kind: "file", size: 1 }],
            cursor: "a",
        }).mockResolvedValueOnce({
            entries: [{ name: "b", path: "/b", kind: "file", size: 2 }],
            cursor: "",
        });

        browser.start();
        await vi.waitFor(() => expect(browser.state.loading).toBe(false));
        expect(browser.state.entries.map((entry) => entry.name)).toEqual(["a", "b"]);
        expect(list.mock.calls[1][0].fileListQueryRequest.cursor).toBe("a");
        browser.navigate("/docs");
        await vi.waitFor(() => expect(browser.destination?.path).toBe("/docs"));
        expect(parentPath(browser.state.path)).toBe("/");
    });
});
