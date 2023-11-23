import { TITLE_DEFAULT } from "@goauthentik/app/common/constants";
import { Interface } from "@goauthentik/elements/Base";
import "@goauthentik/elements/LoadingOverlay";
import Guacamole from "guacamole-common-js";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import AKGlobal from "@goauthentik/common/styles/authentik.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

enum GuacClientState {
    IDLE = 0,
    CONNECTING = 1,
    WAITING = 2,
    CONNECTED = 3,
    DISCONNECTING = 4,
    DISCONNECTED = 5,
}

const AUDIO_INPUT_MIMETYPE = "audio/L16;rate=44100,channels=2";

@customElement("ak-rac")
export class RacInterface extends Interface {
    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFPage,
            PFContent,
            AKGlobal,
            css`
                :host {
                    cursor: none;
                }
                canvas {
                    z-index: unset !important;
                }
                .container {
                    overflow: hidden;
                }
                ak-loading-overlay {
                    z-index: 5;
                }
            `,
        ];
    }

    client?: Guacamole.Client;
    tunnel?: Guacamole.Tunnel;

    @state()
    container?: HTMLElement;

    @state()
    clientState?: GuacClientState;

    @state()
    reconnecting = false;

    @property()
    app?: string;

    @state()
    clipboardWatcherTimer = 0;

    _previousClipboardValue: unknown;

    static domSize(): DOMRect {
        return document.body.getBoundingClientRect();
    }

    constructor() {
        super();
        this.initKeyboard();
        this.checkClipboard();
        this.clipboardWatcherTimer = setInterval(
            this.checkClipboard.bind(this),
            500,
        ) as unknown as number;
    }

    connectedCallback(): void {
        super.connectedCallback();
        window.addEventListener(
            "focus",
            () => {
                this.checkClipboard();
            },
            {
                capture: false,
            },
        );
    }

    disconnectedCallback(): void {
        super.disconnectedCallback();
        clearInterval(this.clipboardWatcherTimer);
    }

    async firstUpdated(): Promise<void> {
        this.updateTitle();
        const wsUrl = `${window.location.protocol.replace("http", "ws")}//${
            window.location.host
        }/ws/rac/${this.app}/`;
        this.tunnel = new Guacamole.WebSocketTunnel(wsUrl);
        this.tunnel.onerror = (status) => {
            this.reconnecting = true;
            this.clientState = undefined;
            console.debug("authentik/rac: tunnel error: ", status);
            setTimeout(() => {
                this.firstUpdated();
            }, 150);
        };
        this.client = new Guacamole.Client(this.tunnel);
        this.client.onerror = (err) => {
            this.reconnecting = true;
            this.clientState = undefined;
            console.debug("authentik/rac: error: ", err);
            setTimeout(() => {
                this.firstUpdated();
            }, 150);
        };
        this.client.onstatechange = (state) => {
            this.clientState = state;
            if (state === GuacClientState.CONNECTED) {
                this.reconnecting = false;
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
                    this._previousClipboardValue = data;
                    navigator.clipboard.writeText(data);
                };
            } else {
                const reader = new Guacamole.BlobReader(stream, mimetype);
                reader.onend = () => {
                    const blob = reader.getBlob();
                    navigator.clipboard.write([
                        new ClipboardItem({
                            [blob.type]: blob,
                        }),
                    ]);
                };
            }
            console.debug("authentik/rac: updated clipboard from remote");
        };
        const params = new URLSearchParams();
        params.set("screen_width", Math.floor(RacInterface.domSize().width).toString());
        params.set("screen_height", Math.floor(RacInterface.domSize().height).toString());
        params.set("screen_dpi", (window.devicePixelRatio * 96).toString());
        this.client.connect(params.toString());
    }

    updateTitle(): void {
        const title = this.tenant?.brandingTitle || TITLE_DEFAULT;
        document.title = `${this.app} - ${title}`;
    }

    onConnected(): void {
        console.debug("authentik/rac: connected");
        if (!this.client) {
            return;
        }
        this.container = this.client.getDisplay().getElement();
        this.initMouse(this.container);
        this.client?.sendSize(
            Math.floor(RacInterface.domSize().width),
            Math.floor(RacInterface.domSize().height),
        );
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
        mouse.onmouseup = mouse.onmousedown = (mouseState) => {
            this.container?.focus();
            handler(mouseState);
        };
        mouse.onmousemove = (mouseState) => {
            handler(mouseState, true);
        };
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

    initKeyboard(): void {
        const keyboard = new Guacamole.Keyboard(document);
        keyboard.onkeydown = (keysym) => {
            this.client?.sendKeyEvent(1, keysym);
        };
        keyboard.onkeyup = (keysym) => {
            this.client?.sendKeyEvent(0, keysym);
        };
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
        const stream = this.client.createClipboardStream("text/plain", "clipboard");
        const writer = new Guacamole.StringWriter(stream);
        writer.sendText(value);
        writer.sendEnd();
        console.debug("authentik/rac: Sent clipboard");
    }

    render(): TemplateResult {
        return html`
            ${this.clientState !== GuacClientState.CONNECTED
                ? html`
                      <ak-loading-overlay>
                          <span slot="body">
                              ${this.reconnecting
                                  ? html`${msg("Re-connecting...")}`
                                  : html`${msg("Connecting...")}`}
                          </span>
                      </ak-loading-overlay>
                  `
                : html``}
            <div class="container">${this.container}</div>
        `;
    }
}
