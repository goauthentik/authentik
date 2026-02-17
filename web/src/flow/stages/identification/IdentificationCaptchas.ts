import "#flow/stages/captcha/CaptchaStage";

import { type IdentificationStage } from "./IdentificationStage";

import { CaptchaChallenge } from "@goauthentik/api";

import { html, nothing, ReactiveController, type ReactiveControllerHost } from "lit";
import { createRef, ref } from "lit/directives/ref.js";

type CaptchaHost = IdentificationStage & ReactiveControllerHost;

export class IdentificationCaptchas implements ReactiveController {
    challenge: CaptchaChallenge | null = null;
    host: IdentificationStage;

    protected token = "";
    protected loaded = false;
    protected refreshedAt = new Date();

    constructor(host: CaptchaHost) {
        this.host = host;
        host.addController(this);
    }

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
