/** Browse the redirected RDP drive through bounded control requests. */
import type { FileTransfers, UploadDestination } from "./file-transfer";

import { aki } from "#common/api/client";

import { RacApi } from "@goauthentik/api";

import { msg } from "@lit/localize";

export interface DriveEntry {
    name: string;
    path: string;
    directory: boolean;
    size?: number;
}

export interface DriveState {
    ready: boolean;
    path: string;
    entries: DriveEntry[];
    loading: boolean;
    error?: string;
}

export const emptyDriveState = (): DriveState => ({
    ready: false,
    path: "/",
    entries: [],
    loading: false,
});

export function parentPath(path: string): string {
    return path.slice(0, path.lastIndexOf("/")) || "/";
}

export class FileBrowser {
    state = emptyDriveState();
    private generation = 0;
    private disposed = false;
    private request?: AbortController;

    constructor(
        private transfers: Pick<FileTransfers, "download">,
        private token: string,
        private connection: string,
        private update: (state: DriveState) => void,
    ) {}

    start(): void {
        this.state.ready = true;
        this.navigate("/");
    }

    get destination(): UploadDestination | undefined {
        return this.state.ready && !this.state.loading && !this.state.error
            ? { path: this.state.path }
            : undefined;
    }

    private emit(): void {
        if (!this.disposed) this.update({ ...this.state, entries: [...this.state.entries] });
    }

    async navigate(path: string): Promise<void> {
        if (this.disposed || !this.state.ready) return;
        const generation = ++this.generation;
        this.request?.abort();
        const controller = (this.request = new AbortController());
        this.state = { ...this.state, path, entries: [], loading: true, error: undefined };
        this.emit();

        try {
            let cursor = "";

            do {
                const page = await aki(RacApi).racFilesListCreate(
                    {
                        fileListQueryRequest: {
                            token: this.token,
                            connection: this.connection,
                            path,
                            ...(cursor ? { cursor } : {}),
                        },
                    },
                    { signal: controller.signal },
                );

                if (this.disposed || generation !== this.generation) return;

                this.state.entries.push(
                    ...page.entries.map((entry) => ({
                        name: entry.name,
                        path: entry.path,
                        directory: entry.kind === "directory",
                        size: entry.size ?? undefined,
                    })),
                );

                cursor = page.cursor;
                this.emit();
            } while (cursor);

            this.state.loading = false;
            this.emit();
        } catch {
            if (controller.signal.aborted || this.disposed || generation !== this.generation)
                return;

            this.state.loading = false;

            this.state.error = msg("Unable to read this directory. Refresh to try again.", {
                id: "rac.files.directory.error",
            });

            this.emit();
        }
    }

    download(entry: DriveEntry): void {
        if (this.disposed || entry.directory || !this.state.entries.includes(entry)) return;
        this.transfers.download(entry.path, entry.size);
    }

    dispose(): void {
        this.disposed = true;
        this.request?.abort();
    }
}
