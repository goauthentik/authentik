/** RAC redirected-drive transfers. JSON control uses the generated API. */
import { sanitizeFilename, UPLOAD_CHUNK_SIZE } from "./file-utils";

import { aki } from "#common/api/client";
import { CSRFHeaderName, readCSRFToken } from "#common/api/csrf";
import { globalAK } from "#common/global";

import { RacApi } from "@goauthentik/api";

import { msg } from "@lit/localize";

export interface TransferStatus {
    id: string;
    name: string;
    direction: "upload" | "download";
    phase: "active" | "complete" | "error";
    transferred: number;
    total?: number;
    error?: string;
    position?: number;
    count?: number;
    queuedNames?: string[];
    path?: string;
}

export interface UploadDestination {
    path: string;
}

interface RemoteTransfer {
    id: string;
    name: string;
    direction: "upload" | "download";
    total: number;
    path: string;
}

export class FileTransfers {
    private active = new Map<string, RemoteTransfer>();
    private downloads = new Map<string, HTMLIFrameElement>();
    private requests = new Map<XMLHttpRequest, string>();
    private canceled = new Set<string>();
    private controller = new AbortController();
    private queue: { file: File; destination?: UploadDestination }[] = [];
    private uploading = false;
    private count = 0;
    private position = 0;

    constructor(
        private token: string,
        private connection: string,
        private update: (status: TransferStatus) => void,
    ) {}

    private url(id: string): string {
        const base = new URL(globalAK().api.relBase, window.location.origin);

        return new URL(`if/rac/bulk/${encodeURIComponent(id)}/`, base).href;
    }

    private publish(
        transfer: RemoteTransfer,
        phase: TransferStatus["phase"],
        transferred: number,
        error?: string,
    ): void {
        if (this.controller.signal.aborted) return;

        this.update({
            ...transfer,
            phase,
            transferred,
            error,
            position: transfer.direction === "upload" ? this.position : undefined,
            count: transfer.direction === "upload" ? this.count : undefined,
            queuedNames:
                transfer.direction === "upload"
                    ? this.queue.map(({ file }) => sanitizeFilename(file.name))
                    : undefined,
        });
    }

    async download(path: string, knownSize?: number): Promise<void> {
        if (this.controller.signal.aborted) return;
        const name = path.slice(path.lastIndexOf("/") + 1);

        try {
            const created = await aki(RacApi).racFileTransfersCreate({
                transferCreateRequest: {
                    token: this.token,
                    connection: this.connection,
                    direction: "download",
                    path,
                },
            });

            if (this.controller.signal.aborted) {
                await aki(RacApi).racFileTransfersDestroy({ id: created.id });

                return;
            }

            const transfer: RemoteTransfer = {
                id: created.id,
                name: created.filename || name,
                direction: "download",
                total: created.size ?? knownSize ?? 0,
                path,
            };

            this.active.set(transfer.id, transfer);
            this.publish(transfer, "active", 0);
            const frame = document.createElement("iframe");
            frame.hidden = true;
            frame.title = transfer.name;
            document.body.append(frame);
            this.downloads.set(transfer.id, frame);
            frame.src = this.url(transfer.id);
        } catch (error) {
            const transfer: RemoteTransfer = {
                id: crypto.randomUUID(),
                name,
                direction: "download",
                total: knownSize ?? 0,
                path,
            };

            this.publish(transfer, "error", 0, String(error));
        }
    }

    async cancel(id: string): Promise<void> {
        const transfer = this.active.get(id);

        if (!transfer) return;
        this.canceled.add(id);
        this.downloads.get(id)?.remove();
        this.downloads.delete(id);

        for (const [request, activeId] of this.requests) {
            if (activeId === id) request.abort();
        }

        try {
            await aki(RacApi).racFileTransfersDestroy({
                id,
            });

            this.publish(
                transfer,
                "error",
                0,
                msg("Transfer canceled", { id: "rac.transfer.canceled.error" }),
            );
        } catch {
            this.publish(
                transfer,
                "error",
                0,
                msg("Could not cancel file transfer", { id: "rac.transfer.cancel.error" }),
            );
        } finally {
            this.active.delete(id);
        }
    }

    /** The Outpost reports whether it finished handing a native download to the browser. */
    settle(id: string, ok: boolean): void {
        const transfer = this.active.get(id);

        if (!transfer || transfer.direction !== "download") return;

        this.publish(
            transfer,
            ok ? "complete" : "error",
            ok ? transfer.total : 0,
            ok
                ? undefined
                : msg("File transfer interrupted", { id: "rac.transfer.interrupted.error" }),
        );

        this.active.delete(id);

        if (!ok) {
            this.downloads.get(id)?.remove();
            this.downloads.delete(id);
        }
    }

    enqueue(files: File[], destination?: UploadDestination): void {
        if (this.controller.signal.aborted) return;
        this.queue.push(...files.map((file) => ({ file, destination })));
        this.count += files.length;

        if (!this.uploading) void this.drain();
    }

    private async drain(): Promise<void> {
        this.uploading = true;

        try {
            while (this.queue.length && !this.controller.signal.aborted) {
                const { file, destination } = this.queue.shift()!;
                this.position += 1;
                await this.upload(file, destination);
            }
        } finally {
            this.uploading = false;
            this.count = 0;
            this.position = 0;
        }
    }

    private async upload(file: File, destination?: UploadDestination): Promise<void> {
        const name = sanitizeFilename(file.name);
        const parent = destination?.path || "/";
        const path = `${parent.replace(/\/$/, "")}/${name}`;
        let transfer: RemoteTransfer | undefined;

        try {
            const created = await aki(RacApi).racFileTransfersCreate({
                transferCreateRequest: {
                    token: this.token,
                    connection: this.connection,
                    direction: "upload",
                    path,
                    size: file.size,
                },
            });

            if (this.controller.signal.aborted) {
                await aki(RacApi).racFileTransfersDestroy({ id: created.id });

                return;
            }

            transfer = {
                id: created.id,
                name: created.filename,
                direction: "upload",
                total: file.size,
                path,
            };

            this.active.set(transfer.id, transfer);
            this.publish(transfer, "active", 0);

            for (let offset = 0; offset < file.size; offset += UPLOAD_CHUNK_SIZE) {
                if (this.controller.signal.aborted || this.canceled.has(transfer.id)) {
                    throw new Error("Transfer canceled");
                }

                const current = offset;

                await this.sendChunk(
                    transfer,
                    file.slice(offset, offset + UPLOAD_CHUNK_SIZE),
                    offset,
                    (loaded) => this.publish(transfer!, "active", current + loaded),
                );

                this.publish(transfer, "active", Math.min(offset + UPLOAD_CHUNK_SIZE, file.size));
            }

            await aki(RacApi).racFileTransfersFinishCreate({
                id: transfer.id,
                transferActionRequest: { token: this.token, connection: this.connection },
            });

            this.publish(transfer, "complete", file.size);
        } catch (error) {
            const failed = transfer ?? {
                id: crypto.randomUUID(),
                name,
                direction: "upload" as const,
                total: file.size,
                path,
            };

            this.publish(
                failed,
                "error",
                0,
                error instanceof Error ? error.message : String(error),
            );

            if (transfer && !this.canceled.has(transfer.id)) await this.cancel(transfer.id);
        } finally {
            if (transfer) {
                this.active.delete(transfer.id);
                this.canceled.delete(transfer.id);
            }
        }
    }

    private sendChunk(
        transfer: RemoteTransfer,
        body: Blob,
        offset: number,
        progress: (loaded: number) => void,
    ): Promise<void> {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            this.requests.set(xhr, transfer.id);
            const abort = () => xhr.abort();
            this.controller.signal.addEventListener("abort", abort, { once: true });
            xhr.open("PUT", this.url(transfer.id));
            xhr.timeout = 300000;
            xhr.setRequestHeader(CSRFHeaderName, readCSRFToken());
            xhr.setRequestHeader("Content-Type", "application/octet-stream");
            xhr.setRequestHeader("X-RAC-Offset", String(offset));
            xhr.upload.onprogress = (event) => progress(event.loaded);

            xhr.onload = () =>
                xhr.status >= 200 && xhr.status < 300
                    ? resolve()
                    : reject(new Error(`HTTP ${xhr.status}`));

            xhr.onerror =
                xhr.ontimeout =
                xhr.onabort =
                    () =>
                        reject(
                            new Error(
                                msg("File transfer interrupted", {
                                    id: "rac.transfer.interrupted.error",
                                }),
                            ),
                        );

            xhr.onloadend = () => {
                this.requests.delete(xhr);
                this.controller.signal.removeEventListener("abort", abort);
            };

            xhr.send(body);
        });
    }

    dispose(): void {
        this.controller.abort();
        this.queue = [];

        for (const request of this.requests.keys()) request.abort();

        for (const frame of this.downloads.values()) frame.remove();
        this.requests.clear();
        this.downloads.clear();
        this.active.clear();
        this.canceled.clear();
    }
}
