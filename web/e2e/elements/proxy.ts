/* eslint-disable @typescript-eslint/no-explicit-any */
import type { LocatorContext } from "#e2e/selectors/types";
import { ConsoleLogger } from "#logger/node";
import { Locator, Page, expect } from "@playwright/test";
import { kebabCase } from "change-case";

export type LocatorMatchers = ReturnType<typeof expect<Locator>>;

export interface LocatorProxy extends Pick<Locator, keyof Locator> {
    $: Locator;
    expect: LocatorMatchers;
}

// Type helpers to extract the shape of the proxy
export type DeepLocatorProxy<T> =
    Disposable & T extends Record<string, any>
        ? T extends HTMLElement
            ? LocatorProxy
            : {
                  [K in keyof T]: DeepLocatorProxy<T[K]>;
              }
        : LocatorProxy;

export function createLocatorProxy<T extends Record<string, any>>(
    ctx: LocatorContext,
    initialPathPrefix: string[] = [],
    dataAttribute: string = "test-id",
): DeepLocatorProxy<T> {
    dataAttribute = kebabCase(dataAttribute);

    function createProxy(path: string[] = initialPathPrefix): any {
        const proxyCache = new Map<string, LocatorProxy>();

        return new Proxy({} as any, {
            get(_, property: string) {
                // Build the current path
                const currentPath = [...path, property];

                // Convert the path to kebab-case and join with hyphens
                const selectorValue = currentPath.map((segment) => kebabCase(segment)).join("-");
                const selector = `[data-${dataAttribute}="${selectorValue}"]`;

                // Create a locator for the current selector
                const locator = ctx.locator(selector);

                if (proxyCache.has(selector)) {
                    ConsoleLogger.debug(`Using cached locator for ${selector}`);
                    return proxyCache.get(selector)!;
                }

                // Return a new proxy that also behaves like a Locator
                // This allows us to either continue chaining or use Locator methods
                const nextProxy = new Proxy(locator, {
                    get(target, prop) {
                        if (typeof prop === "string") {
                            // The user is likely trying to access a property on the page.
                            if (prop === "$") {
                                return target as any;
                            }

                            if (prop === "expect") {
                                return expect(target);
                            }
                        }

                        // If the property exists on the Locator, use it
                        if (prop in target) {
                            const value = (target as any)[prop];
                            // Bind methods to the locator instance
                            if (typeof value === "function") {
                                return value.bind(target);
                            }
                            return value;
                        }
                        // Otherwise, continue building the path

                        return createProxy(currentPath)[prop];
                    },
                });

                proxyCache.set(selector, nextProxy as LocatorProxy);

                return nextProxy;
            },
        });
    }

    return createProxy() as DeepLocatorProxy<T>;
}
