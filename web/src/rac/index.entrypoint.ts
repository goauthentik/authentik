import "#elements/LoadingOverlay";
import "./FileSidebar";
import { type DriveState, emptyDriveState, FileBrowser } from "./file-browser";
import { FileTransfers, TransferStatus } from "./file-transfer";
import Styles from "./index.entrypoint.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";

import { writeToClipboard } from "#common/clipboard";

import { Interface } from "#elements/Interface";
import { WithBrandConfig } from "#elements/mixins/branding";

import Guacamole from "guacamole-common-js";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

enum GuacClientState {
    IDLE = 0,
    CONNECTING = 1,
    WAITING = 2,
    CONNECTED = 3,
    DISCONNECTING = 4,
    DISCONNECTED = 5,
}

export function GuacStateToString(state: GuacClientState): string {
    switch (state) {
        case GuacClientState.IDLE:
            return msg("Idle");
        case GuacClientState.CONNECTING:
            return msg("Connecting");
        case GuacClientState.WAITING:
            return msg("Waiting");
        case GuacClientState.CONNECTED:
            return msg("Connected");
        case GuacClientState.DISCONNECTING:
            return msg("Disconnecting");
        case GuacClientState.DISCONNECTED:
            return msg("Disconnected");
    }
}

const AUDIO_INPUT_MIMETYPE = "audio/L16;rate=44100,channels=2";
const RECONNECT_ATTEMPTS_INITIAL = 5;
const RECONNECT_ATTEMPTS = 5;

@customElement("ak-rac")
export class RacInterface extends WithBrandConfig(Interface) {
    static styles: CSSResult[] = [
        // ---

        PFPage,
        PFButton,
        PFContent,
        Styles,
    ];

    client?: Guacamole.Client;
    tunnel?: Guacamole.Tunnel;
    private fileTransfers?: FileTransfers;
    private fileBrowser?: FileBrowser;
    private keyboard?: Guacamole.Keyboard;
    private resizeObserver?: ResizeObserver;
    private lastSize = "";
    private readonly focusHandler = () => {
        this.checkClipboard();
    };

    @state() private filesOpen = false;
    @state() private drive: DriveState = emptyDriveState();
    private transferTimers = new Map<string, ReturnType<typeof setTimeout>>();
    private reconnectTimer?: ReturnType<typeof setTimeout>;
    private dragDepth = 0;

    @state()
    private draggingFiles = false;

    @state()
    private transfers: TransferStatus[] = [];

    @state()
    container?: HTMLElement;

    @state()
    clientState: GuacClientState = GuacClientState.WAITING;

    @state()
    clientStatus?: Guacamole.Status;

    @state()
    reconnectingMessage = "";

    @property()
    token?: string;

    @property({ attribute: "device-name" })
    deviceName?: string;

    @property()
    protocol?: string;

    @property()
    driveEnabled?: string;

    private get showFiles(): boolean {
        return this.protocol === "rdp" && this.driveEnabled === "true";
    }

    @state()
    clipboardWatcherTimer = 0;

    _previousClipboardValue: unknown;

    // Set to `true` if we've successfully connected once
    hasConnected = false;
    // Keep track of current connection attempt
    connectionAttempt = 0;

    private domSize(): { width: number; height: number } {
        const size = (
            this.renderRoot.querySelector(".desktop-viewport") || document.body
        ).getBoundingClientRect();

        return {
            width: size.width,
            height: size.height,
        };
    }

    constructor() {
        super();
        this.checkClipboard();

        this.clipboardWatcherTimer = setInterval(
            this.checkClipboard.bind(this),
            500,
        ) as unknown as number;
    }

    connectedCallback(): void {
        super.connectedCallback();
        window.addEventListener("focus", this.focusHandler);
    }

    disconnectedCallback(): void {
        super.disconnectedCallback();
        window.removeEventListener("focus", this.focusHandler);
        this.resizeObserver?.disconnect();
        this.keyboard?.reset();
        this.fileBrowser?.dispose();
        clearInterval(this.clipboardWatcherTimer);
        clearTimeout(this.reconnectTimer);
        this.fileTransfers?.dispose();

        if (this.client) {
            this.client.onerror = null;
            this.client.onstatechange = null;
        }

        if (this.tunnel) this.tunnel.onerror = null;
        this.client?.disconnect();

        for (const timer of this.transferTimers.values()) clearTimeout(timer);
        this.transferTimers.clear();
    }

    async firstUpdated(): Promise<void> {
        this.synchronizeTitle();
        this.fileBrowser?.dispose();
        this.fileTransfers?.dispose();
        this.drive = emptyDriveState();
        this.lastSize = "";
        this.initViewport();

        if (this.client) {
            this.client.onerror = null;
            this.client.onstatechange = null;
        }

        if (this.tunnel) this.tunnel.onerror = null;
        this.client?.disconnect();

        for (const timer of this.transferTimers.values()) clearTimeout(timer);
        this.transferTimers.clear();
        this.transfers = [];
        this.dragDepth = 0;
        this.draggingFiles = false;
        const connectionId = crypto.randomUUID();
        const wsUrl = `${window.location.protocol.replace("http", "ws")}//${window.location.host}/ws/rac/${this.token}/`;
        this.tunnel = new Guacamole.WebSocketTunnel(wsUrl);
        this.tunnel.receiveTimeout = 10 * 1000;

        // 10 seconds
        this.tunnel.onerror = (status) => {
            console.debug("authentik/rac: tunnel error: ", status);

            this.reconnect();
        };

        this.client = new Guacamole.Client(this.tunnel);

        this.fileTransfers = new FileTransfers(this.token!, connectionId, (status) =>
            this.updateTransfer(status),
        );

        const handleGuacamoleInstruction = this.tunnel.oninstruction;

        this.tunnel.oninstruction = (opcode, args) => {
            if (opcode === "authentik-bulk") {
                const [id, result] = args.map(String);
                this.fileTransfers?.settle(id, result === "ok");

                return;
            }

            handleGuacamoleInstruction?.(opcode, args);
        };

        this.fileBrowser = new FileBrowser(
            this.fileTransfers,
            this.token!,
            connectionId,
            (drive) => {
                this.drive = drive;
            },
        );

        this.client.onerror = (err) => {
            this.clientStatus = err;

            console.debug("authentik/rac: error: ", err);

            this.reconnect();
        };

        this.client.onstatechange = (state) => {
            this.clientState = state;

            if (state === GuacClientState.CONNECTED) {
                this.onConnected();
            }
        };

        this.client.onclipboard = (stream, mimetype) => {
            // If the received data is text, read it as a simple string
            if (/^text\//.exec(mimetype)) {
                const reader = new Guacamole.StringReader(stream);
                let data = "";

                reader.ontext = (text) => {
                    data += text;
                };

                reader.onend = () => {
                    const trimmed = data.trim();

                    // Some remote sessions (notably SSH) push empty clipboard
                    // payloads that would otherwise clobber the user's local
                    // clipboard, breaking subsequent paste attempts. Ignore
                    // them so the local clipboard remains intact.
                    if (!trimmed) {
                        console.debug("authentik/rac: ignored empty remote clipboard payload");

                        return;
                    }

                    this._previousClipboardValue = trimmed;
                    writeToClipboard(trimmed);
                };
            } else {
                const reader = new Guacamole.BlobReader(stream, mimetype);

                reader.onend = () => {
                    const blob = reader.getBlob();

                    const item = new ClipboardItem({
                        [blob.type]: blob,
                    });

                    writeToClipboard(item);
                };
            }

            console.debug("authentik/rac: updated clipboard from remote");
        };

        const params = new URLSearchParams();
        params.set("connection_id", connectionId);
        params.set("screen_width", Math.floor(this.domSize().width).toString());
        params.set("screen_height", Math.floor(this.domSize().height).toString());
        // https://github.com/goauthentik/authentik/pull/11757
        // there are DPI issues when using SSH on HiDPi screens
        // but if we're not setting DPI at all the resolution is not respected at all
        params.set("screen_dpi", "96");
        this.client.connect(params.toString());
    }

    reconnect(): void {
        if (this.reconnectTimer) return;
        this.fileBrowser?.dispose();
        this.fileTransfers?.dispose();
        this.clientState = GuacClientState.WAITING;
        this.connectionAttempt += 1;

        if (!this.hasConnected) {
            // Check connection attempts if we haven't had a successful connection
            if (this.connectionAttempt >= RECONNECT_ATTEMPTS_INITIAL) {
                this.hasConnected = true;

                this.reconnectingMessage = msg(
                    str`Connection failed after ${this.connectionAttempt} attempts.`,
                );

                return;
            }
        } else if (this.connectionAttempt >= RECONNECT_ATTEMPTS) {
            this.reconnectingMessage = msg(
                str`Connection failed after ${this.connectionAttempt} attempts.`,
            );

            return;
        }

        const delay = 500 * this.connectionAttempt;

        this.reconnectingMessage = msg(
            str`Re-connecting in ${Math.max(1, delay / 1000)} second(s).`,
        );

        this.reconnectTimer = setTimeout(() => {
            this.reconnectTimer = undefined;
            this.firstUpdated();
        }, delay);
    }

    protected synchronizeTitle(): void {
        this.setTitle(this.deviceName);
    }

    onConnected(): void {
        console.debug("authentik/rac: connected");

        if (!this.client) {
            return;
        }

        this.hasConnected = true;
        this.clientStatus = undefined;
        this.container = this.client.getDisplay().getElement();
        this.initMouse(this.container);
        this.resizeDesktop();
        this.focusDesktop();

        if (this.showFiles) this.fileBrowser?.start();
    }

    initMouse(container: HTMLElement): void {
        const mouse = new Guacamole.Mouse(container);

        const handler = (mouseState: Guacamole.Mouse.State, scaleMouse = false) => {
            if (!this.client) return;

            if (scaleMouse) {
                mouseState.y = mouseState.y / this.client.getDisplay().getScale();
                mouseState.x = mouseState.x / this.client.getDisplay().getScale();
            }

            this.client.sendMouseState(mouseState);
        };

        // @ts-expect-error Event type is not properly defined in guacamole-common-js
        mouse.onEach(["mouseup", "mousedown"], (ev: Guacamole.Mouse.Event) => {
            this.focusDesktop();
            handler(ev.state);
        });

        // @ts-expect-error Event type is not properly defined in guacamole-common-js
        mouse.on("mousemove", (ev: Guacamole.Mouse.Event) => {
            handler(ev.state, true);
        });
    }

    initAudioInput(): void {
        const stream = this.client?.createAudioStream(AUDIO_INPUT_MIMETYPE);

        if (!stream) return;
        // Guacamole.AudioPlayer
        const recorder = Guacamole.AudioRecorder.getInstance(stream, AUDIO_INPUT_MIMETYPE);

        // If creation of the AudioRecorder failed, simply end the stream
        if (!recorder) {
            stream.sendEnd();

            return;
        }

        // Otherwise, ensure that another audio stream is created after this
        // audio stream is closed
        recorder.onclose = this.initAudioInput.bind(this);
    }

    protected initViewport(): void {
        const viewport = this.renderRoot.querySelector<HTMLElement>(".desktop-viewport")!;

        if (!this.keyboard) this.initKeyboard(viewport);

        if (!this.resizeObserver) {
            this.resizeObserver = new ResizeObserver(() => this.resizeDesktop());
            this.resizeObserver.observe(viewport);
        }
    }

    initKeyboard(viewport: HTMLElement): void {
        const keyboard = (this.keyboard = new Guacamole.Keyboard(viewport));
        viewport.addEventListener("blur", () => keyboard.reset());

        keyboard.onkeydown = (keysym) => {
            this.client?.sendKeyEvent(1, keysym);
        };

        keyboard.onkeyup = (keysym) => {
            this.client?.sendKeyEvent(0, keysym);
        };
    }

    private resizeDesktop(): void {
        const { width, height } = this.domSize();
        const size = `${Math.floor(width)}:${Math.floor(height)}`;

        if (
            width > 0 &&
            height > 0 &&
            size !== this.lastSize &&
            this.clientState === GuacClientState.CONNECTED
        ) {
            this.lastSize = size;
            this.client?.sendSize(Math.floor(width), Math.floor(height));
        }
    }

    private focusDesktop(): void {
        this.renderRoot
            .querySelector<HTMLElement>(".desktop-viewport")
            ?.focus({ preventScroll: true });
    }

    toggleFiles(open = !this.filesOpen): void {
        this.keyboard?.reset();
        this.filesOpen = open;

        if (!open) this.focusDesktop();
        else
            this.updateComplete.then(() => {
                this.renderRoot
                    .querySelector("ak-rac-file-sidebar")
                    ?.shadowRoot?.querySelector<HTMLButtonElement>("header button")
                    ?.focus();
            });
    }

    async checkClipboard(): Promise<void> {
        try {
            if (!this._previousClipboardValue) {
                this._previousClipboardValue = await navigator.clipboard.readText();

                return;
            }

            const newValue = await navigator.clipboard.readText();

            if (newValue !== this._previousClipboardValue) {
                console.debug(`authentik/rac: new clipboard value: ${newValue}`);

                this._previousClipboardValue = newValue;
                this.writeClipboard(newValue);
            }
        } catch (ex) {
            // The error is most likely caused by the document not being in focus
            // in which case we can ignore it and just retry
            if (ex instanceof DOMException) {
                return;
            }

            console.warn("authentik/rac: error reading clipboard", ex);
        }
    }

    private writeClipboard(value: string) {
        if (!this.client) {
            return;
        }

        const stream = this.client.createClipboardStream("text/plain");
        const writer = new Guacamole.StringWriter(stream);
        writer.sendText(value);
        writer.sendEnd();

        console.debug("authentik/rac: Sent clipboard");
    }

    private updateTransfer(status: TransferStatus): void {
        this.transfers = [...this.transfers.filter((item) => item.id !== status.id), status].slice(
            -16,
        );

        clearTimeout(this.transferTimers.get(status.id));

        if (status.phase === "complete") {
            if (!this.drive.loading) {
                this.fileBrowser?.navigate(this.drive.path);
            }

            this.transferTimers.set(
                status.id,
                setTimeout(() => this.dismissTransfer(status.id), 5000),
            );
        }
    }

    private dismissTransfer(id: string): void {
        clearTimeout(this.transferTimers.get(id));
        this.transferTimers.delete(id);
        this.transfers = this.transfers.filter((status) => status.id !== id);
    }

    private dragEnter(event: DragEvent): void {
        if (!event.dataTransfer?.types.includes("Files")) return;
        event.preventDefault();
        this.dragDepth += 1;
        this.draggingFiles = true;
    }

    private dragOver(event: DragEvent): void {
        if (!event.dataTransfer?.types.includes("Files")) return;
        event.preventDefault();

        event.dataTransfer.dropEffect =
            this.clientState === GuacClientState.CONNECTED ? "copy" : "none";
    }

    private dragLeave(event: DragEvent): void {
        if (!event.dataTransfer?.types.includes("Files")) return;
        this.dragDepth = Math.max(0, this.dragDepth - 1);
        this.draggingFiles = this.dragDepth > 0;
    }

    private dropFiles(event: DragEvent): void {
        if (!event.dataTransfer?.types.includes("Files")) return;
        event.preventDefault();
        this.dragDepth = 0;
        this.draggingFiles = false;

        if (this.clientState === GuacClientState.CONNECTED) {
            const items = Array.from(event.dataTransfer.items);

            const files = items.length
                ? items
                      .filter(
                          (item) => item.kind === "file" && !item.webkitGetAsEntry?.()?.isDirectory,
                      )
                      .map((item) => item.getAsFile())
                      .filter((file): file is File => file !== null)
                : Array.from(event.dataTransfer.files);

            this.uploadFiles(files);
        }
    }

    private uploadFiles(files: File[]): void {
        if (
            !this.showFiles ||
            this.clientState !== GuacClientState.CONNECTED ||
            !this.fileBrowser?.destination
        )
            return;

        this.fileTransfers?.enqueue(files, this.fileBrowser.destination);
    }

    renderOverlay() {
        if (!this.clientState || this.clientState === GuacClientState.CONNECTED) {
            return nothing;
        }

        let message = html`${GuacStateToString(this.clientState)}`;

        if (this.clientState === GuacClientState.WAITING) {
            message = html`${msg("Connecting...")}`;
        }

        if (this.hasConnected) {
            message = html`${this.reconnectingMessage}`;
        }

        if (this.clientStatus?.message) {
            message = html`${message}<br />${this.clientStatus.message}`;
        }

        const isLoading = [
            GuacClientState.CONNECTING,
            GuacClientState.DISCONNECTING,
            GuacClientState.WAITING,
        ].includes(this.clientState);

        return html`
            <ak-loading-overlay ?no-spinner=${!isLoading} icon="fa fa-times">
                <span>${message}</span>
            </ak-loading-overlay>
        `;
    }

    render(): TemplateResult {
        const active = this.transfers.filter((status) => status.phase === "active").length;
        const errors = this.transfers.some((status) => status.phase === "error");

        return html`
            <div
                class="rac-shell"
                @dragenter=${this.dragEnter}
                @dragover=${this.dragOver}
                @dragleave=${this.dragLeave}
                @drop=${this.dropFiles}
            >
                <header class="rac-toolbar">
                    <span class="endpoint-name">${this.deviceName}</span>
                    ${
                        this.showFiles
                            ? html`<button
                                  class="pf-c-button pf-m-plain files-toggle"
                                  aria-controls="rac-files"
                                  aria-expanded=${this.filesOpen}
                                  @click=${() => this.toggleFiles()}
                              >
                                  <i class="fas fa-folder-open" aria-hidden="true"></i>
                                  ${msg("Files", { id: "rac.files.title.label" })}
                                  ${active ? html`<span class="transfer-count">${active}</span>` : nothing}
                                  ${
                                      errors
                                          ? html`<i
                                                class="fas fa-exclamation-circle error-indicator"
                                                role="img"
                                                aria-label=${msg("File transfer failed", {
                                                    id: "rac.transfer.status.error",
                                                })}
                                            ></i>`
                                          : nothing
                                  }
                              </button>`
                            : nothing
                    }
                </header>
                <div class="rac-layout">
                    <div
                        class="desktop-viewport"
                        tabindex="0"
                        aria-label=${msg("Remote desktop", { id: "rac.desktop.aria-label" })}
                    >
                        ${this.container} ${this.renderOverlay()}
                    </div>
                    ${
                        this.showFiles
                            ? html`<aside
                                  id="rac-files"
                                  class="files-panel"
                                  ?hidden=${!this.filesOpen}
                              >
                                  <ak-rac-file-sidebar
                                      .drive=${this.drive}
                                      .transfers=${this.transfers}
                                      ?disabled=${this.clientState !== GuacClientState.CONNECTED}
                                      @rac-files-close=${() => this.toggleFiles(false)}
                                      @rac-files-navigate=${(event: CustomEvent) =>
                                          this.fileBrowser?.navigate(event.detail.path)}
                                      @rac-files-download=${(event: CustomEvent) =>
                                          this.fileBrowser?.download(event.detail.entry)}
                                      @rac-files-upload=${(event: CustomEvent) =>
                                          this.uploadFiles(event.detail.files)}
                                      @rac-files-cancel=${(event: CustomEvent) =>
                                          this.fileTransfers?.cancel(event.detail.id)}
                                      @rac-files-dismiss=${(event: CustomEvent) =>
                                          this.dismissTransfer(event.detail.id)}
                                  >
                                  </ak-rac-file-sidebar>
                              </aside>`
                            : nothing
                    }
                </div>
                ${
                    this.draggingFiles
                        ? html`<div class="file-drop-overlay">
                              ${msg(str`Upload files to ${this.drive.path}`, {
                                  id: "rac.files.drop.description",
                              })}
                          </div>`
                        : nothing
                }
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-rac": RacInterface;
    }
}
