/// <reference types="@types/grecaptcha"/>

export {};

declare global {
    interface Window {
        grecaptcha: ReCaptchaV2.ReCaptcha & {
            enterprise: ReCaptchaV2.ReCaptcha;
        };
    }
}
