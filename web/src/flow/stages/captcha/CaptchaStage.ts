import "#flow/FormStatic";
import "#flow/components/ak-flow-card";

import { pluckErrorDetail } from "#common/errors/network";

import { akEmptyState } from "#elements/EmptyState";
import { ListenerController } from "#elements/utils/listenerController";

import { AKFormErrors, ErrorProp } from "#components/ak-field-errors";

import { FlowUserDetails } from "#flow/FormStatic";
import { BaseStage } from "#flow/stages/base";
import Styles from "#flow/stages/captcha/CaptchaStage.css";
import { CapController } from "#flow/stages/captcha/controllers/cap";
import {
    CaptchaController,
    CaptchaControllerConstructor,
    CaptchaHandlerHost,
} from "#flow/stages/captcha/controllers/CaptchaController";
import { GReCaptchaController } from "#flow/stages/captcha/controllers/grecaptcha";
import { HCaptchaController } from "#flow/stages/captcha/controllers/hcaptcha";
import { TurnstileController } from "#flow/stages/captcha/controllers/turnstile";
import { loadCaptchaScript } from "#flow/stages/captcha/script-loader";
import { CAPTCHA_SLOT } from "#flow/stages/captcha/shared";

import { ConsoleLogger } from "#logger/browser";

import { CaptchaChallenge, CaptchaChallengeResponseRequest } from "@goauthentik/api";

import { LOCALE_STATUS_EVENT, LocaleStatusEventDetail, msg } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

export type TokenListener = (token: string) => void;

/**
 * The nearest ancestor that sits in the document tree rather than in a shadow root.
 *
 * Returns `null` while the node is detached, when there is no document-tree host to speak
 * of yet.
 */
function documentTreeHost(node: Node): Element | null {
    let current: Node = node;

    for (;;) {
        const root = current.getRootNode();

        if (!(root instanceof ShadowRoot)) {
            return current.isConnected && current instanceof Element ? current : null;
        }

        current = root.host;
    }
}

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
     * Order is a tie-breaker for the global-matching fallback in
     * {@linkcode CaptchaController.resolve}; challenges whose script URL is recognized are
     * matched exactly regardless of position.
     */
    public static readonly controllers = new Set<CaptchaControllerConstructor>([
        // ---
        HCaptchaController,
        GReCaptchaController,
        TurnstileController,
        CapController,
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

    /**
     * Whether the provider has reported its widget as rendered.
     */
    @state()
    protected widgetLoaded = false;

    /**
     * The currently active Captcha controller, if any.
     */
    @state()
    protected activeController: CaptchaController | null = null;

    #container?: HTMLDivElement;
    #listenController = new ListenerController();

    /**
     * Guards against a slow script load resolving after the challenge has moved on.
     */
    #loadGeneration = 0;

    /**
     * Identifies the challenge the active controller was built for.
     */
    #loadedSignature: string | null = null;

    //#endregion

    //#region Container

    /**
     * The element a provider renders its widget into.
     *
     * Attached to the nearest document-tree ancestor — the flow executor — and projected
     * back down into the card through {@linkcode CAPTCHA_SLOT}. reCAPTCHA and hCaptcha
     * resolve their own elements through `document`, so a container whose `getRootNode()`
     * is a `ShadowRoot` renders but can never finish verifying: the checkbox spins
     * forever. Slotting moves nothing, so the container stays in the document tree while
     * appearing inside the card.
     */
    protected get container(): HTMLDivElement {
        if (this.#container) return this.#container;

        const container = document.createElement("div");

        container.slot = CAPTCHA_SLOT;
        container.className = "ak-captcha-container";

        // Set here rather than in the stage's stylesheet: the container lives in the
        // document tree, out of reach of this element's shadow root.
        //
        // Vendors size their widget frames with the `height` content attribute, and that
        // hint does not survive on authentik's pages — a plain `<iframe height="78">`
        // computes to the 150px replaced-element default here, while identical markup
        // computes to 78px on a page outside the app — so the frame spills below the widget
        // as a blank band. Inside the old wrapper iframe the surrounding stylesheets never
        // reached it. Clipping to the box the vendor actually declared is safe: every
        // provider renders its expanded challenge as an overlay on `document.body`, never
        // inside this container.
        container.style.overflow = "hidden";

        this.#container = container;

        return container;
    }

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
                <div
                    role="group"
                    aria-label=${msg("CAPTCHA challenge")}
                    class="ak-interactive-challenge"
                    data-ready=${this.widgetLoaded ? "ready" : "loading"}
                >
                    <slot name=${CAPTCHA_SLOT}></slot>
                </div>
            `;
        }

        return html`${akEmptyState({ loading: true }, { heading: msg("Verifying...") })}
            <slot name=${CAPTCHA_SLOT} class="ak-invisible-challenge"></slot>`;
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

        return this.renderBody();
    }

    //#endregion

    //#region Lifecycle

    public disconnectedCallback(): void {
        this.#listenController.abort();
        this.#teardown();

        super.disconnectedCallback();
    }

    public updated(changedProperties: PropertyValues<this>) {
        super.updated(changedProperties);

        // A flow can present several CAPTCHA stages in a row, and the executor reuses this
        // element for each of them rather than replacing it — only `challenge` changes. The
        // widget therefore has to be rebuilt here, not just when the element first renders,
        // or the second stage keeps showing the first stage's solved widget.
        if (
            changedProperties.has("challenge") &&
            this.#challengeSignature !== this.#loadedSignature
        ) {
            this.#loadedSignature = this.#challengeSignature;
            this.#load();

            return;
        }

        if (!changedProperties.has("refreshedAt") || !this.challenge) {
            return;
        }

        this.#logger.debug("Refresh triggered");

        this.activeController?.reset().catch((error: unknown) => {
            this.#logger.warn("Failed to reset challenge", error);
        });
    }

    /**
     * Identity of the current challenge, as far as the widget is concerned.
     *
     * The executor hands us a fresh object on every update, so object identity would
     * rebuild the widget on unrelated re-renders.
     */
    get #challengeSignature(): string | null {
        const { challenge } = this;

        if (!challenge) return null;

        return [challenge.jsUrl, challenge.siteKey, challenge.interactive].join("|");
    }

    #teardown() {
        if (this.activeController) {
            this.removeController(this.activeController);
            this.activeController.unmount();
            this.activeController = null;
        }

        // The container lives outside this element's subtree, so dropping the stage does
        // not take it with it.
        this.#container?.remove();
        this.#container = undefined;
        this.widgetLoaded = false;
    }

    //#endregion

    //#region Loading

    async #load(): Promise<void> {
        const generation = ++this.#loadGeneration;

        this.#teardown();
        this.error = null;

        const source = this.challenge?.jsUrl;

        if (!source || !URL.canParse(source)) {
            this.#logger.debug("No challenge URL, skipping load.");
            return;
        }

        const challengeURL = new URL(source);
        const resolution = CaptchaController.resolve(CaptchaStage.controllers, challengeURL);

        if (!resolution) {
            this.error = msg("Could not find a suitable CAPTCHA provider.");
            return;
        }

        const { Controller, matched } = resolution;

        if (matched === "global") {
            // Nothing about the URL identified a vendor, so the choice came from whichever
            // global is already on `window` — which may well have been installed by a
            // different stage. Worth saying out loud when a widget misbehaves.
            this.#logger.warn(
                `No provider matched \`${challengeURL.href}\`; falling back to the \`${Controller.globalName}\` global. ` +
                    `Proxied CAPTCHA script URLs can be mis-detected when several providers are in play.`,
            );
        }

        const controller = new Controller(this);

        try {
            await loadCaptchaScript({
                url: controller.prepareURL() ?? challengeURL,
                type: Controller.scriptType,
                isAvailable: () => Controller.isAvailable(),
            });

            // The challenge changed while the vendor script was in flight; whatever we
            // mount now would belong to a stage the user has already left.
            if (generation !== this.#loadGeneration) {
                this.#logger.debug("Stale load, discarding.");
                this.removeController(controller);
                return;
            }

            const host = documentTreeHost(this);

            if (!host) {
                this.#logger.debug("No document-tree host, skipping.");
                return;
            }

            // The container has to be attached before a provider renders into it — several
            // of them measure it on the spot.
            host.appendChild(this.container);

            if (this.challenge?.interactive) {
                await controller.mount(this.container);
            } else {
                await controller.execute(this.container);
            }

            this.activeController = controller;
            this.#logger.debug(`[${Controller.globalName}]: mounted`);
        } catch (error) {
            this.#logger.warn(`[${Controller.globalName}]: failed to mount`, error);

            this.error = pluckErrorDetail(error, "Unspecified error");
            this.removeController(controller);
            return;
        }

        // Locale changes are only interesting once the widget is up; reacting earlier
        // would re-enter the load we are still inside.
        window.addEventListener(LOCALE_STATUS_EVENT, this.#localeStatusListener, {
            signal: this.#listenController.signal,
        });
    }

    #localeStatusListener = (event: CustomEvent<LocaleStatusEventDetail>) => {
        if (!this.activeController) return;

        if (event.detail.status === "error") {
            this.#logger.debug("Error loading locale:", event.detail);
            return;
        }

        if (event.detail.status === "loading") return;

        this.#logger.debug(`Locale changed to \`${event.detail.readyLocale}\``);

        // Providers take their language at render time, so the widget has to be rebuilt
        // rather than told about the change.
        this.#load();
    };

    //#endregion

    //#region Host callbacks

    public onWidgetLoad = (): void => {
        this.widgetLoaded = true;
        this.onLoad?.();
    };

    //#endregion
}

export default CaptchaStage;

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-captcha": CaptchaStage;
    }
}
