import "#flow/FormStatic";
import "#flow/components/ak-flow-card";

import { pluckErrorDetail } from "#common/errors/network";

import { akEmptyState } from "#elements/EmptyState";
import { ListenerController } from "#elements/utils/listenerController";
import { randomId } from "#elements/utils/randomId";

import { AKFormErrors, ErrorProp } from "#components/ak-field-errors";

import { FlowUserDetails } from "#flow/FormStatic";
import { BaseStage } from "#flow/stages/base";
import Styles from "#flow/stages/captcha/CaptchaStage.css";
import {
    CaptchaController,
    CaptchaControllerConstructor,
    CaptchaHandlerHost,
} from "#flow/stages/captcha/controllers/CaptchaController";
import { GReCaptchaController } from "#flow/stages/captcha/controllers/grecaptcha";
import { HCaptchaController } from "#flow/stages/captcha/controllers/hcaptcha";
import { TurnstileController } from "#flow/stages/captcha/controllers/turnstile";
import { iframeTemplate } from "#flow/stages/captcha/shared";

import { ConsoleLogger } from "#logger/browser";

import { CaptchaChallenge, CaptchaChallengeResponseRequest } from "@goauthentik/api";

import { match } from "ts-pattern";

import { LOCALE_STATUS_EVENT, LocaleStatusEventDetail, msg } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { createRef, ref, type Ref } from "lit/directives/ref.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

export type TokenListener = (token: string) => void;

interface CaptchaMessage {
    source?: string;
    context?: string;
    message: "captcha";
    token: string;
}

interface LoadMessage {
    source?: string;
    context?: string;
    message: "load";
}

type IframeMessageEvent = MessageEvent<CaptchaMessage | LoadMessage>;

@customElement("ak-stage-captcha")
export class CaptchaStage
    extends BaseStage<CaptchaChallenge, CaptchaChallengeResponseRequest>
    implements CaptchaHandlerHost
{
    public static readonly styles: CSSResult[] = [
        // ---
        PFLogin,
        PFForm,
        PFFormControl,
        PFTitle,
        Styles,
    ];

    /**
     * Set of Captcha provider controllers.
     *
     * Note that this `Set` is in the preferred order of discovery.
     */
    public static readonly controllers = new Set<CaptchaControllerConstructor>([
        // ---
        HCaptchaController,
        GReCaptchaController,
        TurnstileController,
    ]);

    #logger = ConsoleLogger.prefix("flow:captcha");

    //#region Properties

    @property({ type: Boolean })
    public embedded = false;

    @property()
    public onTokenChange: TokenListener = (token: string) => {
        this.host.submit({ component: "ak-stage-captcha", token });
    };

    @property()
    public onLoad?: () => void;

    @property({ attribute: false })
    public refreshedAt = new Date();

    //#endregion

    //#region State

    @property({ attribute: false })
    public error: ErrorProp | null = null;

    @state()
    protected iframeHeight = 65;

    /**
     * The currently active Captcha controller, if any.
     */
    @state()
    protected activeController: CaptchaController | null = null;

    /**
     * The desired source URL of the iframe. Note that this may differ from the actual
     * `src` attribute of the iframe element for certain captcha providers.
     */
    #iframeSource = "about:blank";
    /**
     * A Lit {@linkcode Ref} to the iframe element.
     */
    public iframeRef: Ref<HTMLIFrameElement> = createRef();

    #iframeLoaded = false;

    #captchaDocumentContainer?: HTMLDivElement;
    #listenController = new ListenerController();

    //#endregion

    //#region Getters/Setters

    public get captchaDocumentContainer(): HTMLDivElement {
        if (this.#captchaDocumentContainer) {
            return this.#captchaDocumentContainer;
        }

        this.#captchaDocumentContainer = document.createElement("div");
        this.#captchaDocumentContainer.id = `ak-captcha-${randomId()}`;

        return this.#captchaDocumentContainer;
    }

    //#endregion

    //#region Listeners

    // ADR: Did not to put anything into `otherwise` or `exhaustive` here because iframe messages
    // that were not of interest to us also weren't necessarily corrupt or suspicious. For example,
    // during testing Storybook throws a lot of cross-iframe messages that we don't care about.

    #messageListener = ({ data }: IframeMessageEvent) => {
        if (!data) return;

        if (data.source !== "goauthentik.io" || data.context !== "flow-executor") {
            return;
        }

        this.#logger.debug("Received message:", data);

        return match(data)
            .with({ message: "captcha" }, ({ token }) => this.onTokenChange(token))
            .with({ message: "load" }, this.#loadListener)
            .otherwise(({ message }) => {
                this.#logger.debug(`Unknown message: ${message}`);
            });
    };

    //#endregion

    //#region Render

    protected renderBody() {
        if (this.error) {
            return html`<ak-empty-state icon="fa-times" .defaultLabel=${false}>
                <div>${msg("The CAPTCHA challenge failed to load.")}</div>
                <div slot="body">${AKFormErrors({ errors: [this.error] })}</div></ak-empty-state
            >`;
        }

        if (this.challenge?.interactive) {
            return html`
                <iframe
                    aria-label=${msg("CAPTCHA challenge")}
                    ${ref(this.iframeRef)}
                    style="height: ${this.iframeHeight}px;"
                    data-ready=${this.#iframeLoaded ? "ready" : "loading"}
                    class="ak-interactive-challenge"
                    id="ak-captcha"
                ></iframe>
            `;
        }

        return akEmptyState({ loading: true }, { heading: msg("Verifying...") });
    }

    protected renderMain() {
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form">
                ${FlowUserDetails({ challenge: this.challenge })} ${this.renderBody()}
            </form>
        </ak-flow-card>`;
    }

    protected render() {
        if (!this.challenge) {
            return this.embedded ? nothing : akEmptyState({ loading: true });
        }

        if (!this.embedded) {
            return this.renderMain();
        }

        return this.challenge.interactive ? this.renderBody() : nothing;
    }

    //#endregion

    //#region Lifecycle

    public connectedCallback(): void {
        super.connectedCallback();
        window.addEventListener("message", this.#messageListener, {
            signal: this.#listenController.signal,
        });
    }

    public disconnectedCallback(): void {
        this.#listenController.abort();

        if (!this.challenge?.interactive) {
            if (document.body.contains(this.captchaDocumentContainer)) {
                document.body.removeChild(this.captchaDocumentContainer);
            }
        }

        super.disconnectedCallback();
    }

    public override firstUpdated(changedProperties: PropertyValues<this>) {
        super.firstUpdated(changedProperties);

        if (changedProperties.has("challenge") && this.challenge) {
            this.#refreshControllers();
        }
    }

    public updated(changedProperties: PropertyValues<this>) {
        super.updated(changedProperties);

        if (!changedProperties.has("refreshedAt") || !this.challenge) {
            return;
        }

        this.#logger.debug("refresh triggered");

        if (this.activeController) {
            return this.challenge.interactive
                ? this.activeController.refreshInteractive()
                : this.activeController.refresh();
        }
    }

    #refreshControllers() {
        if (!this.challenge) {
            this.#logger.debug("No challenge, skipping controller refresh.");
            return;
        }

        // First, remove any existing script & listeners...
        window.removeEventListener(LOCALE_STATUS_EVENT, this.#localeStatusListener);

        if (!this.challenge.interactive) {
            document.body.appendChild(this.captchaDocumentContainer);
        }

        const challengeURL =
            this.challenge?.jsUrl && URL.canParse(this.challenge.jsUrl)
                ? new URL(this.challenge.jsUrl)
                : null;

        if (!challengeURL) {
            this.#logger.debug("No challenge URL, skipping controller refresh.");
            return;
        }

        // It's possible that the script has already been loaded by another stage instance.
        // So long as the URL matches, we can reuse it.
        const matchedScript = Iterator.from(this.ownerDocument.querySelectorAll("script")).find(
            (script) => script.src === challengeURL.href,
        );

        if (matchedScript) {
            this.#logger.debug("Reusing existing script element.");

            if (this.activeController) {
                return this.#run(this.activeController);
            }

            return this.#scriptLoadListener();
        }

        // Then, load the new script...
        const scriptElement = document.createElement("script");

        scriptElement.src = challengeURL.toString();
        scriptElement.async = true;
        scriptElement.defer = true;
        scriptElement.onload = this.#scriptLoadListener;

        document.head.appendChild(scriptElement);

        if (this.activeController) {
            this.removeController(this.activeController);
            this.activeController = null;
        }
    }

    #localeStatusListener = (event: CustomEvent<LocaleStatusEventDetail>) => {
        if (!this.activeController) {
            return;
        }

        if (event.detail.status === "error") {
            this.#logger.debug("Error loading locale:", event.detail);
            return;
        }

        if (event.detail.status === "loading") {
            return;
        }

        const { readyLocale } = event.detail;
        this.#logger.debug(`Locale changed to \`${readyLocale}\``);

        this.#run(this.activeController);
    };

    //#endregion

    //#region Resizing

    #mutationObserver?: MutationObserver;
    #resizeObserver?: ResizeObserver;

    /**
     * An event listener that is called through the iframe's `postMessage` API
     * when the iframe has loaded its content.
     */
    #loadListener = () => {
        this.#mutationObserver?.disconnect();
        this.#resizeObserver?.disconnect();

        const iframe = this.iframeRef.value;
        const contentDocument = iframe?.contentDocument;

        if (!iframe || !contentDocument) return;

        let synchronizeHeight: () => void;

        if (this.activeController instanceof GReCaptchaController) {
            // reCAPTCHA's use of nested iframes prevents their internal resize observer from
            // reporting the correct height back to our iframe, so we have to do it ourselves.

            synchronizeHeight = () => {
                if (!this.iframeRef) return;

                const target = contentDocument.getElementById("ak-container");

                if (!target) return;

                const innerIFrame = contentDocument.querySelector<HTMLIFrameElement>(
                    'iframe[style~="height:"]',
                );

                const innerBottom = innerIFrame?.getBoundingClientRect().bottom ?? 0;

                const actualHeight = Math.max(innerBottom, target.clientHeight);

                this.iframeHeight = Math.round(actualHeight * 1.1);

                if (innerIFrame?.parentElement) {
                    innerIFrame.parentElement.style.height = `${actualHeight}px`;
                }
            };

            // We watch for any newly inserted iframes, as they may alter the height
            // of the parent iframe...
            this.#mutationObserver = new MutationObserver((mutations) => {
                for (const mutation of mutations) {
                    if (mutation.type !== "childList") continue;

                    for (const node of mutation.addedNodes as NodeListOf<HTMLElement>) {
                        if (node.tagName !== "IFRAME") continue;

                        // And then resize the iframe to match the new size.
                        //
                        // This doesn't fix the issue entirely since the challenge frame
                        // doesn't yet know the correct height, but at least the user can
                        // try to load the challenge again with the correct height.

                        this.#resizeObserver?.observe(node as HTMLIFrameElement);

                        requestAnimationFrame(synchronizeHeight);
                    }
                }
            });

            this.#mutationObserver.observe(contentDocument.body, {
                childList: true,
                subtree: true,
            });
        } else {
            synchronizeHeight = () => {
                if (!this.iframeRef) return;

                const target = contentDocument.getElementById("ak-container");

                if (!target) return;

                this.iframeHeight = Math.round(target.clientHeight);
            };
        }

        this.#resizeObserver = new ResizeObserver(synchronizeHeight);

        requestAnimationFrame(() => {
            this.#resizeObserver?.observe(contentDocument.body);
            this.onLoad?.();
            this.#iframeLoaded = true;
        });
    };

    //#endregion

    //#region Loading

    /**
     * An event listener that is called when the captcha provider's script has loaded,
     * attempting to initialize each available controller in order.
     */
    #scriptLoadListener = async (event?: Event): Promise<void> => {
        const scriptElement = event?.currentTarget as HTMLScriptElement | null;
        this.#logger.debug("Script loaded", scriptElement?.src ?? "unknown source");

        this.error = null;
        this.#iframeLoaded = false;

        const [Controller, ...rest] = CaptchaController.discover(CaptchaStage.controllers);

        if (!Controller) {
            this.error = msg("Could not find a suitable CAPTCHA provider.");
            return;
        }

        // hCaptcha aliases gReCaptcha for compatibility reasons, no need to panic if that's the case.
        if (
            rest.length &&
            Controller === HCaptchaController &&
            rest.some((C) => C !== GReCaptchaController)
        ) {
            this.#logger.debug(
                `Other CAPTCHA providers were also available: ${rest
                    .map((C) => C?.globalName ?? "unknown")
                    .join(", ")}`,
            );
        }

        const { globalName } = Controller;
        const controller = new Controller(this);

        try {
            await this.#run(controller);
            this.#logger.debug(`[${globalName}]: handler succeeded`);

            this.activeController = controller;
        } catch (error) {
            this.#logger.debug(`[${globalName}]: handler failed`);
            this.#logger.debug(error);

            this.error = pluckErrorDetail(error, "Unspecified error");
            this.removeController(controller);
        }

        // We begin listening for locale changes once a handler has been successfully run
        // to avoid interrupting the initial load.
        window.addEventListener(LOCALE_STATUS_EVENT, this.#localeStatusListener, {
            signal: this.#listenController.signal,
        });
    };

    async #run(controller: CaptchaController): Promise<void> {
        if (!this.challenge) {
            throw new Error("No challenge available");
        }

        if (!this.challenge.interactive) {
            await controller.execute();
        }

        const iframe = this.iframeRef.value;

        if (!iframe) {
            this.#logger.debug(`No iframe found, skipping.`);
            return;
        }

        const { contentDocument } = iframe;

        if (!contentDocument) {
            this.#logger.debug("No iframe content window found, skipping.");

            return;
        }

        this.#logger.debug(`Rendering interactive.`);

        const challengeURL = controller.prepareURL();

        if (!challengeURL) {
            throw new Error("Could not prepare challenge URL");
        }

        const captchaElement = controller.interactive();
        const template = iframeTemplate(captchaElement, {
            challengeURL: challengeURL.toString(),
            theme: this.activeTheme,
        });

        if (
            controller instanceof GReCaptchaController ||
            controller instanceof HCaptchaController
        ) {
            // reCAPTCHA's & hCaptcha's domain verification can't seem to penetrate the true origin
            // of the page when loaded from a blob URL, likely due to their double-nested
            // iframe structure.
            // We fallback to the deprecated `document.write` to get around this.
            this.#iframeSource = "about:blank";

            requestAnimationFrame(() => {
                contentDocument.open();
                contentDocument.write(template);
                contentDocument.close();
            });

            return;
        }

        URL.revokeObjectURL(this.#iframeSource);

        const url = URL.createObjectURL(new Blob([template], { type: "text/html" }));

        this.#iframeSource = url;
        iframe.src = url;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-captcha": CaptchaStage;
    }
}
