import "#flow/FormStatic";
import "#flow/components/ak-flow-card";

import { pluckErrorDetail } from "#common/errors/network";

import { akEmptyState } from "#elements/EmptyState";
import { ifPresent } from "#elements/utils/attributes";
import { ListenerController } from "#elements/utils/listenerController";
import { randomId } from "#elements/utils/randomId";

import { FlowUserDetails } from "#flow/FormStatic";
import { BaseStage } from "#flow/stages/base";
import { CaptchaHandler, CaptchaProvider, iframeTemplate } from "#flow/stages/captcha/shared";

import { ConsoleLogger } from "#logger/browser";

import { CaptchaChallenge, CaptchaChallengeResponseRequest } from "@goauthentik/api";

import { match } from "ts-pattern";

import { LOCALE_STATUS_EVENT, LocaleStatusEventDetail, msg } from "@lit/localize";
import { css, CSSResult, html, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";

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
export class CaptchaStage extends BaseStage<CaptchaChallenge, CaptchaChallengeResponseRequest> {
    static styles: CSSResult[] = [
        PFLogin,
        PFForm,
        PFFormControl,
        PFTitle,
        css`
            :host {
                --captcha-background-to: var(--pf-global--BackgroundColor--light-100);
                --captcha-background-from: var(--pf-global--BackgroundColor--light-300);
            }

            :host([theme="dark"]) {
                --captcha-background-to: var(--ak-dark-background-light);
                --captcha-background-from: var(--pf-global--BackgroundColor--300);
            }

            @keyframes captcha-background-animation {
                0% {
                    background-color: var(--captcha-background-from);
                }
                50% {
                    background-color: var(--captcha-background-to);
                }
                100% {
                    background-color: var(--captcha-background-from);
                }
            }

            .ak-interactive-challenge {
                /**
                 * We use & here to hint to the ShadyDOM polyfill that this rule is meant
                 * for the iframe itself, not the contents of the iframe.
                 */
                & {
                    width: 100%;
                    min-height: 65px;
                }

                &[data-ready="loading"] {
                    background-color: var(--captcha-background-from);
                    animation: captcha-background-animation 1s infinite
                        var(--pf-global--TimingFunction);
                }
            }
        `,
    ];

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

    @state()
    protected activeHandler: CaptchaProvider | null = null;

    @state()
    protected error: string | null = null;

    @state()
    protected iframeHeight = 65;

    #scriptElement?: HTMLScriptElement;

    #iframeSource = "about:blank";
    #iframeRef = createRef<HTMLIFrameElement>();

    #iframeLoaded = false;

    #captchaDocumentContainer?: HTMLDivElement;
    #listenController = new ListenerController();

    //#endregion

    //#region Getters/Setters

    protected get captchaDocumentContainer(): HTMLDivElement {
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

        return match(data)
            .with({ message: "captcha" }, ({ token }) => this.onTokenChange(token))
            .with({ message: "load" }, this.#loadListener)
            .otherwise(({ message }) => {
                this.#logger.debug(`Unknown message: ${message}`);
            });
    };

    //#endregion

    //#region g-recaptcha

    protected renderGReCaptchaFrame = () => {
        return html`<div
            id="ak-container"
            class="g-recaptcha"
            data-theme="${this.activeTheme}"
            data-sitekey=${ifPresent(this.challenge?.siteKey)}
            data-callback="callback"
        ></div>`;
    };

    async executeGReCaptcha() {
        return grecaptcha.ready(() => {
            return grecaptcha.execute(
                grecaptcha.render(this.captchaDocumentContainer, {
                    sitekey: this.challenge?.siteKey ?? "",
                    callback: this.onTokenChange,
                    size: "invisible",
                    hl: this.activeLanguageTag,
                }),
            );
        });
    }

    async refreshGReCaptchaFrame() {
        this.#iframeRef.value?.contentWindow?.grecaptcha.reset();
    }

    async refreshGReCaptcha() {
        window.grecaptcha.reset();
        window.grecaptcha.execute();
    }

    //#endregion

    //#region h-captcha

    protected renderHCaptchaFrame = () => {
        return html`<div
            id="ak-container"
            class="h-captcha"
            data-sitekey=${ifPresent(this.challenge?.siteKey)}
            data-theme="${this.activeTheme}"
            data-callback="callback"
        ></div>`;
    };

    async executeHCaptcha() {
        await hcaptcha.execute(
            hcaptcha.render(this.captchaDocumentContainer, {
                sitekey: this.challenge?.siteKey ?? "",
                callback: this.onTokenChange,
                size: "invisible",
                hl: this.activeLanguageTag,
            }),
        );
    }

    async refreshHCaptchaFrame() {
        this.#iframeRef.value?.contentWindow?.hcaptcha?.reset();
    }

    async refreshHCaptcha() {
        window.hcaptcha.reset();
        window.hcaptcha.execute();
    }

    //#endregion

    //#region Turnstile

    /**
     * Renders the Turnstile captcha frame.
     *
     * @remarks
     *
     * Turnstile will log a warning if the `data-language` attribute
     * is not in lower-case format.
     *
     * @see {@link https://developers.cloudflare.com/turnstile/reference/supported-languages/ Turnstile Supported Languages}
     */
    protected renderTurnstileFrame = () => {
        const languageTag = this.activeLanguageTag.toLowerCase();

        return html`<div
            id="ak-container"
            class="cf-turnstile"
            data-sitekey=${ifPresent(this.challenge?.siteKey)}
            data-theme="${this.activeTheme}"
            data-callback="callback"
            data-size="flexible"
            data-language=${ifPresent(languageTag)}
        ></div>`;
    };

    async executeTurnstile() {
        window.turnstile.render(this.captchaDocumentContainer, {
            sitekey: this.challenge?.siteKey ?? "",
            callback: this.onTokenChange,
        });
    }

    async refreshTurnstileFrame() {
        this.#iframeRef.value?.contentWindow?.turnstile.reset();
    }

    async refreshTurnstile() {
        window.turnstile.reset();
    }

    //#endregion

    /**
     * Mapping of captcha provider names to their respective JS API global.
     *
     * Note that this is a `Map` to ensure the preferred order of discovering provider globals.
     */
    #handlers = new Map<CaptchaProvider, CaptchaHandler>([
        [
            "grecaptcha",
            {
                interactive: this.renderGReCaptchaFrame,
                execute: this.executeGReCaptcha,
                refreshInteractive: this.refreshGReCaptchaFrame,
                refresh: this.refreshGReCaptcha,
            },
        ],
        [
            "hcaptcha",
            {
                interactive: this.renderHCaptchaFrame,
                execute: this.executeHCaptcha,
                refreshInteractive: this.refreshHCaptchaFrame,
                refresh: this.refreshHCaptcha,
            },
        ],
        [
            "turnstile",
            {
                interactive: this.renderTurnstileFrame,
                refreshInteractive: this.refreshTurnstileFrame,
                execute: this.executeTurnstile,
                refresh: this.refreshTurnstile,
            },
        ],
    ]);

    //#region Render

    renderBody() {
        if (this.error) {
            return akEmptyState({ icon: "fa-times" }, { heading: this.error });
        }

        if (this.challenge?.interactive) {
            return html`
                <iframe
                    aria-label=${msg("CAPTCHA challenge")}
                    ${ref(this.#iframeRef)}
                    style="height: ${this.iframeHeight}px;"
                    data-ready="${this.#iframeLoaded ? "ready" : "loading"}"
                    class="ak-interactive-challenge"
                    id="ak-captcha"
                ></iframe>
            `;
        }

        return akEmptyState({ loading: true }, { heading: msg("Verifying...") });
    }

    renderMain() {
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form">
                ${FlowUserDetails({ challenge: this.challenge })} ${this.renderBody()}
            </form>
        </ak-flow-card>`;
    }

    render() {
        if (!this.challenge) {
            return this.embedded ? nothing : akEmptyState({ loading: true });
        }

        if (!this.embedded) {
            return this.renderMain();
        }

        return this.challenge.interactive ? this.renderBody() : nothing;
    }

    //#endregion;

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

    //#endregion

    public override firstUpdated(changedProperties: PropertyValues<this>) {
        super.firstUpdated(changedProperties);

        if (!(changedProperties.has("challenge") && typeof this.challenge !== "undefined")) {
            return;
        }

        this.#refreshVendor();
    }

    public updated(changedProperties: PropertyValues<this>) {
        super.updated(changedProperties);

        if (!changedProperties.has("refreshedAt") || !this.challenge) {
            return;
        }

        if (!this.activeHandler) {
            return;
        }

        this.#logger.debug("refresh triggered");

        this.#run(this.activeHandler);
    }

    #refreshVendor() {
        // First, remove any existing script & listeners...
        window.removeEventListener(LOCALE_STATUS_EVENT, this.#localeStatusListener);

        this.#scriptElement?.remove();

        // Then, load the new script...
        const scriptElement = document.createElement("script");

        scriptElement.src = this.challenge?.jsUrl ?? "";
        scriptElement.async = true;
        scriptElement.defer = true;
        scriptElement.onload = this.#scriptLoadListener;

        this.#scriptElement?.remove();

        this.#scriptElement = document.head.appendChild(scriptElement);

        if (!this.challenge?.interactive) {
            document.body.appendChild(this.captchaDocumentContainer);
        }
    }

    #localeStatusListener = (event: CustomEvent<LocaleStatusEventDetail>) => {
        if (!this.activeHandler) {
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

        this.#run(this.activeHandler);
    };

    //#endregion

    //#region Resizing

    #loadListener = () => {
        const iframe = this.#iframeRef.value;
        const contentDocument = iframe?.contentDocument;

        if (!iframe || !contentDocument) return;

        let synchronizeHeight: () => void;

        if (this.activeHandler === CaptchaProvider.reCAPTCHA) {
            // reCAPTCHA's use of nested iframes prevents their internal resize observer from
            // reporting the correct height back to our iframe, so we have to do it ourselves.

            synchronizeHeight = () => {
                if (!this.#iframeRef) return;

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
            const mutationObserver = new MutationObserver((mutations) => {
                for (const mutation of mutations) {
                    if (mutation.type !== "childList") continue;

                    for (const node of mutation.addedNodes as NodeListOf<HTMLElement>) {
                        if (node.tagName !== "IFRAME") continue;

                        // And then resize the iframe to match the new size.
                        //
                        // This doesn't fix the issue entirely since the challenge frame
                        // doesn't yet know the correct height, but at least the user can
                        // try to load the challenge again with the correct height.

                        // eslint-disable-next-line @typescript-eslint/no-use-before-define
                        resizeObserver.observe(node as HTMLIFrameElement);

                        requestAnimationFrame(synchronizeHeight);
                    }
                }
            });

            mutationObserver.observe(contentDocument.body, {
                childList: true,
                subtree: true,
            });
        } else {
            synchronizeHeight = () => {
                if (!this.#iframeRef) return;

                const target = contentDocument.getElementById("ak-container");

                if (!target) return;

                this.iframeHeight = Math.round(target.clientHeight);
            };
        }

        const resizeObserver = new ResizeObserver(synchronizeHeight);

        requestAnimationFrame(() => {
            resizeObserver.observe(contentDocument.body);
            this.onLoad?.();
            this.#iframeLoaded = true;
        });
    };

    //#endregion

    //#region Loading

    #scriptLoadListener = async (): Promise<void> => {
        this.#logger.debug("script loaded");

        this.error = null;
        this.#iframeLoaded = false;

        for (const name of this.#handlers.keys()) {
            if (!Object.hasOwn(window, name)) {
                continue;
            }

            try {
                await this.#run(name);
                this.#logger.debug(`[${name}]: handler succeeded`);

                this.activeHandler = name;
            } catch (error) {
                this.#logger.debug(`[${name}]: handler failed`);
                this.#logger.debug(error);

                this.error = pluckErrorDetail(error, "Unspecified error");
            }

            // We begin listening for locale changes once a handler has been successfully run
            // to avoid interrupting the initial load.
            window.addEventListener(LOCALE_STATUS_EVENT, this.#localeStatusListener, {
                signal: this.#listenController.signal,
            });

            return;
        }
    };

    async #run(captchaProvider: CaptchaProvider) {
        const handler = this.#handlers.get(captchaProvider)!;

        if (this.challenge?.interactive) {
            const iframe = this.#iframeRef.value;

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

            const captchaElement = handler.interactive();
            const template = iframeTemplate(captchaElement, {
                challengeURL: this.challenge.jsUrl,
                theme: this.activeTheme,
            });

            if (
                captchaProvider === CaptchaProvider.reCAPTCHA ||
                captchaProvider === CaptchaProvider.hCaptcha
            ) {
                // reCAPTCHA's & hCaptcha's domain verification can't seem to penetrate the true origin
                // of the page when loaded from a blob URL, likely due to their double-nested
                // iframe structure.
                // We fallback to the deprecated `document.write` to get around this.
                this.#iframeSource = "about:blank";
                contentDocument.open();
                contentDocument.write(template);
                contentDocument.close();

                // this.#loadListener();
            } else {
                URL.revokeObjectURL(this.#iframeSource);

                const url = URL.createObjectURL(new Blob([template], { type: "text/html" }));

                this.#iframeSource = url;

                iframe.src = url;
            }

            return;
        }

        await handler.execute.apply(this);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-captcha": CaptchaStage;
    }
}
