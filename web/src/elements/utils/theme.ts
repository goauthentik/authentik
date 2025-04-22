/**
 * @file Theme utilities.
 */
import { UIConfig } from "@goauthentik/common/ui/config";

import { Config, CurrentBrand } from "@goauthentik/api";

/**
 * An element that can be themed.
 */
export interface ThemedElement extends HTMLElement {
    brand?: CurrentBrand;
    uiConfig?: UIConfig;
    config?: Config;
}

export function findThemedRootElement<T extends ThemedElement = ThemedElement>(): T | null {
    const element = document.body.querySelector<T>("[data-ak-interface-root]");

    return element;
}
