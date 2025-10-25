/// <reference types="@hcaptcha/types"/>

export {};

declare global {
    interface Window {
        hcaptcha?: HCaptcha;
    }
}
