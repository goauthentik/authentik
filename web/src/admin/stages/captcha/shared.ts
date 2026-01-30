import { CaptchaStage, CaptchaStageRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";

export const CaptchaProviderKeys = [
    "recaptcha_v2",
    "recaptcha_v3",
    "recaptcha_enterprise",
    "hcaptcha",
    "turnstile",
    "custom",
] as const satisfies string[];

export type CaptchaProviderKey = (typeof CaptchaProviderKeys)[number];

export interface CaptchaProviderPreset {
    formatDisplayName: () => string;
    jsUrl: string;
    apiUrl: string;
    interactive: boolean;
    supportsScore: boolean;
    score?: { min: number; max: number };
    formatAPISource?: () => string;
    keyURL?: string;
}

/**
 * Provider presets for common CAPTCHA services.
 * Each preset contains default URLs, settings, and help text with links to provider dashboards.
 * When a provider is selected, these values auto-fill the form but remain editable.
 */
export const CAPTCHA_PROVIDERS = {
    recaptcha_v2: {
        formatDisplayName: () =>
            msg("Google reCAPTCHA v2", {
                id: "captcha.providers.recaptcha-v2",
            }),
        jsUrl: "https://www.recaptcha.net/recaptcha/api.js",
        apiUrl: "https://www.recaptcha.net/recaptcha/api/siteverify",
        interactive: true,
        supportsScore: false,
        formatAPISource: () =>
            msg("reCAPTCHA admin console", {
                id: "captcha.providers.recaptcha.admin-console",
            }),
        keyURL: "https://www.google.com/recaptcha/admin",
    },
    recaptcha_v3: {
        formatDisplayName: () =>
            msg("Google reCAPTCHA v3", {
                id: "captcha.providers.recaptcha-v3",
            }),
        jsUrl: "https://www.recaptcha.net/recaptcha/api.js",
        apiUrl: "https://www.recaptcha.net/recaptcha/api/siteverify",
        interactive: false,
        supportsScore: true,
        score: { min: 0.5, max: 1.0 },
        formatAPISource: () =>
            msg("reCAPTCHA admin console", {
                id: "captcha.providers.recaptcha.api-key-source",
            }),
        keyURL: "https://www.google.com/recaptcha/admin",
    },
    recaptcha_enterprise: {
        formatDisplayName: () =>
            msg("Google reCAPTCHA Enterprise", {
                id: "captcha.providers.recaptcha-enterprise",
            }),
        jsUrl: "https://www.recaptcha.net/recaptcha/enterprise.js",
        apiUrl: "https://www.recaptcha.net/recaptcha/api/siteverify",
        interactive: false,
        supportsScore: true,
        score: { min: 0.5, max: 1.0 },
        formatAPISource: () =>
            msg("Google Cloud Console", {
                id: "captcha.providers.recaptcha-enterprise.api-key-source",
            }),
        keyURL: "https://cloud.google.com/recaptcha-enterprise",
    },
    hcaptcha: {
        formatDisplayName: () =>
            msg("hCaptcha", {
                id: "captcha.providers.hcaptcha",
            }),
        jsUrl: "https://js.hcaptcha.com/1/api.js",
        apiUrl: "https://api.hcaptcha.com/siteverify",
        interactive: true,
        supportsScore: true,
        score: { min: 0.0, max: 0.5 },
        formatAPISource: () =>
            msg("hCaptcha dashboard", {
                id: "captcha.providers.hcaptcha.api-key-source",
            }),
        keyURL: "https://dashboard.hcaptcha.com",
    },
    turnstile: {
        formatDisplayName: () =>
            msg("Cloudflare Turnstile", {
                id: "captcha.providers.turnstile",
            }),
        jsUrl: "https://challenges.cloudflare.com/turnstile/v0/api.js",
        apiUrl: "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        interactive: true,
        supportsScore: false,
        formatAPISource: () =>
            msg("Cloudflare dashboard", {
                id: "captcha.providers.turnstile.api-key-source",
            }),
        keyURL: "https://dash.cloudflare.com",
    },
    custom: {
        formatDisplayName: () =>
            msg("Custom", {
                id: "captcha.providers.custom",
            }),
        jsUrl: "https://www.recaptcha.net/recaptcha/api.js",
        apiUrl: "https://www.recaptcha.net/recaptcha/api/siteverify",
        interactive: false,
        supportsScore: true,
        score: { min: 0.5, max: 1.0 },
    },
} as const satisfies Record<CaptchaProviderKey, CaptchaProviderPreset>;

/**
 * Detect which provider preset matches the given {@linkcode CaptchaStage} instance.
 * This allows the form to show the correct provider in the dropdown when editing
 * an existing CAPTCHA stage. Falls back to "custom" if no match is found.
 */
export function detectProviderFromInstance(stage?: CaptchaStage | null): CaptchaProviderKey {
    if (!stage) return "custom";

    for (const key of CaptchaProviderKeys) {
        const preset = CAPTCHA_PROVIDERS[key];

        if (stage.jsUrl === preset.jsUrl && stage.apiUrl === preset.apiUrl) {
            return key;
        }
    }

    return "custom";
}

/**
 * Get the form values to display, with clear precedence:
 * 1. If editing an existing instance, use instance values
 * 2. Otherwise, use the current preset defaults
 */
export function pluckFormValues(
    instance?: CaptchaStage | null,
    preset: CaptchaProviderPreset = CAPTCHA_PROVIDERS.custom,
): Omit<CaptchaStageRequest, "name" | "publicKey" | "privateKey"> {
    if (instance) {
        return {
            jsUrl: instance.jsUrl,
            apiUrl: instance.apiUrl,
            interactive: instance.interactive,
            scoreMinThreshold: instance.scoreMinThreshold,
            scoreMaxThreshold: instance.scoreMaxThreshold,
            errorOnInvalidScore: instance.errorOnInvalidScore ?? true,
        };
    }

    return {
        jsUrl: preset.jsUrl,
        apiUrl: preset.apiUrl,
        interactive: preset.interactive,
        scoreMinThreshold: preset.score?.min ?? 0.5,
        scoreMaxThreshold: preset.score?.max ?? 1.0,
        errorOnInvalidScore: true,
    };
}
