import "#flow/stages/captcha/CaptchaStage";

import type { IdentificationHost } from "#flow/stages/identification/IdentificationStage";

import { CaptchaChallenge } from "@goauthentik/api";

import { html, nothing, ReactiveController } from "lit";
import { createRef, ref } from "lit/directives/ref.js";

/**
 * Handle the lifecycle of an embedded captcha.
 *
 * @remarks
 *
 * If the server is so configured, the user will presented with a CAPTCHA challenge along with the
 * other challenges related to identifying the user. That logic is peripheral to the main tasks of
 * IdentifyingStage, so it's placed into its own controller. The only thing a client needs to do is
 * remember to try and render it; if it's not enabled, it just returns `nothing`.
 */
export class CaptchaController implements ReactiveController {
    private challenge: CaptchaChallenge | null = null;

    protected token = "";
    protected loaded = false;
    protected refreshedAt = new Date();

    constructor(private host: IdentificationHost) {}

    public hostUpdate() {
        if (this.challenge !== this.host.challenge?.captchaStage) {
            this.challenge = this.host.challenge?.captchaStage ?? null;
        }
    }

    public get live() {
        return !!this.challenge;
    }

    public get pending() {
        return this.challenge && this.challenge.interactive && !this.loaded;
    }

    #inputRef = createRef<HTMLInputElement>();

    #loadListener = () => {
        this.loaded = true;
        this.host.requestUpdate();
    };

    #tokenChangeListener = (token: string) => {
        const input = this.#inputRef.value;
        if (!input) return;
        input.value = token;
    };

    public onFailure() {
        const captchaInput = this.#inputRef.value;
        if (captchaInput) {
            captchaInput.value = "";
        }
        this.refreshedAt = new Date();
        this.host.requestUpdate();
    }

    #renderCaptchaStage(challenge: CaptchaChallenge) {
        return html` <div class="captcha-container">
            <ak-stage-captcha
                .challenge=${challenge}
                .onTokenChange=${this.#tokenChangeListener}
                .onLoad=${this.#loadListener}
                .refreshedAt=${this.refreshedAt}
                embedded
            >
            </ak-stage-captcha>
            <input
                aria-hidden="true"
                class="faux-input"
                ${ref(this.#inputRef)}
                name="captchaToken"
                type="text"
                required
                value=""
            />
        </div>`;
    }

    public render() {
        return this.challenge ? this.#renderCaptchaStage(this.challenge) : nothing;
    }
}

export default CaptchaController;
