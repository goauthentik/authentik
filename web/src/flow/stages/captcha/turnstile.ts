/* eslint-disable @typescript-eslint/triple-slash-reference */
/// <reference types="turnstile-types"/>
import { TurnstileObject } from "turnstile-types";

declare global {
    interface Window {
        turnstile: TurnstileObject;
    }
}
