import { FileTransfers, type TransferStatus } from "./file-transfer";
import { UPLOAD_CHUNK_SIZE } from "./file-utils";

import { RacApi } from "@goauthentik/api";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

class HTTPRequest {
    static requests: HTTPRequest[] = [];
    method = "";
    url = "";
    status = 204;
    body?: Blob;
    headers = new Map<string, string>();
    upload = { onprogress: null as ((event: { loaded: number }) => void) | null };
    onload?: () => void;
    onloadend?: () => void;
    onerror?: () => void;
    ontimeout?: () => void;
    onabort?: () => void;
    open(method: string, url: string): void {
        this.method = method;
        this.url = url;
    }
    setRequestHeader(key: string, value: string): void {
        this.headers.set(key, value);
    }
    send(body?: Blob): void {
        this.body = body;
        HTTPRequest.requests.push(this);
    }
    finish(status = 204): void {
        this.status = status;
        this.onload?.();
        this.onloadend?.();
    }
    abort(): void {
        this.onabort?.();
        this.onloadend?.();
    }
}

describe("redirected-drive file transfers", () => {
    let transfers: FileTransfers;
    let statuses: TransferStatus[];
    let create: ReturnType<typeof vi.spyOn>;
    let finish: ReturnType<typeof vi.spyOn>;
    let destroy: ReturnType<typeof vi.spyOn>;

    beforeEach(() => {
        vi.stubGlobal("XMLHttpRequest", HTTPRequest);
        HTTPRequest.requests = [];
        statuses = [];

        create = vi.spyOn(RacApi.prototype, "racFileTransfersCreate").mockResolvedValue({
            id: "upload-id",
            filename: "file.txt",
            size: 4,
        });

        finish = vi
            .spyOn(RacApi.prototype, "racFileTransfersFinishCreate")
            .mockResolvedValue(undefined);

        destroy = vi
            .spyOn(RacApi.prototype, "racFileTransfersDestroy")
            .mockResolvedValue(undefined);

        transfers = new FileTransfers("token", "connection", (status) => statuses.push(status));
    });

    afterEach(() => {
        transfers.dispose();
        document.cookie = "authentik_csrf=; Max-Age=0; path=/";
        vi.unstubAllGlobals();
        vi.restoreAllMocks();
    });

    it("uploads queued files in order, reports progress, and finishes empty files", async () => {
        document.cookie = "authentik_csrf=merge%2Fcsrf; path=/";
        create
            .mockResolvedValueOnce({
                id: "first",
                filename: "large.bin",
                size: UPLOAD_CHUNK_SIZE + 1,
            })
            .mockResolvedValueOnce({ id: "second", filename: "empty.bin", size: 0 });

        transfers.enqueue(
            [
                new File([new Uint8Array(UPLOAD_CHUNK_SIZE + 1)], "large.bin"),
                new File([], "empty.bin"),
            ],
            { path: "/docs" },
        );

        await vi.waitFor(() => expect(HTTPRequest.requests).toHaveLength(1));
        expect(HTTPRequest.requests[0].url).toContain("/if/rac/bulk/first/");
        expect(HTTPRequest.requests[0].body?.size).toBe(UPLOAD_CHUNK_SIZE);
        expect(HTTPRequest.requests[0].headers.get("X-RAC-Offset")).toBe("0");
        expect(HTTPRequest.requests[0].headers.get("X-authentik-CSRF")).toBe("merge/csrf");
        HTTPRequest.requests[0].upload.onprogress?.({ loaded: 100 });
        expect(statuses.at(-1)?.transferred).toBe(100);
        HTTPRequest.requests[0].finish();
        await vi.waitFor(() => expect(HTTPRequest.requests).toHaveLength(2));
        expect(HTTPRequest.requests[1].body?.size).toBe(1);
        HTTPRequest.requests[1].finish();
        await vi.waitFor(() => expect(finish).toHaveBeenCalledTimes(2));
        expect(HTTPRequest.requests).toHaveLength(2);
        expect(create.mock.calls[0][0].transferCreateRequest.path).toBe("/docs/large.bin");

        expect(
            statuses.some((status) => status.name === "empty.bin" && status.phase === "complete"),
        ).toBe(true);
    });

    it("starts a native download without reading the response into JavaScript", async () => {
        create.mockResolvedValueOnce({ id: "download-id", filename: "report.txt", size: 10 });
        await transfers.download("/report.txt", 10);
        const frame = document.querySelector<HTMLIFrameElement>('iframe[title="report.txt"]');
        expect(frame?.src).toContain("/if/rac/bulk/download-id/");
        expect(HTTPRequest.requests).toHaveLength(0);
        expect(statuses.at(-1)?.direction).toBe("download");
        transfers.settle("download-id", true);
        expect(statuses.at(-1)?.phase).toBe("complete");
    });

    it("cancels the active upload and aborts its HTTP chunk", async () => {
        transfers.enqueue([new File(["data"], "file.txt")], { path: "/" });
        await vi.waitFor(() => expect(HTTPRequest.requests).toHaveLength(1));
        const abort = vi.spyOn(HTTPRequest.requests[0], "abort");
        await transfers.cancel("upload-id");
        expect(abort).toHaveBeenCalledOnce();
        expect(destroy).toHaveBeenCalledWith({ id: "upload-id" });
    });

    it("does not retry a failed binary chunk", async () => {
        transfers.enqueue([new File(["data"], "file.txt")], { path: "/" });
        await vi.waitFor(() => expect(HTTPRequest.requests).toHaveLength(1));
        HTTPRequest.requests[0].finish(502);
        await vi.waitFor(() => expect(destroy).toHaveBeenCalledOnce());
        expect(HTTPRequest.requests).toHaveLength(1);
        expect(statuses.some((status) => status.phase === "error")).toBe(true);
    });
});
