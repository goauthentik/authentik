import type { LitNode } from "../types/lit-jsx.js";

import { test as base } from "@playwright/experimental-ct-react";
import { Locator, Page } from "playwright/test";

export { expect } from "@playwright/test";
/* eslint-disable react-hooks/rules-of-hooks */

export interface InnerMountOptions {}

async function innerMount(page: Page, componentRef: unknown, options = {}) {
    await page.waitForFunction(() => {
        // @ts-ignore
        return !!window.playwrightMount;
    });

    const selector = await page.evaluate(
        async ({ component: component2 }) => {
            let rootElement = document.getElementById("root");

            if (!rootElement) {
                rootElement = document.createElement("div");
                rootElement.id = "root";
                document.body.appendChild(rootElement);
            }

            rootElement.textContent = "Test 123";
            return "#root >> internal:control=component";
        },
        { component: componentRef },
    );
    return selector;
}

interface E2EFixturesTestScope {
    render: (component: LitNode, options?: any) => Promise<Locator>;
}

interface E2EWorkerScope {
    renderWorker: void;
}

export const test = base.extend<E2EFixturesTestScope, E2EWorkerScope>({
    // renderWorker: [async ({ browser }, use, workerInfo) => {}, { scope: "worker" }],
    render: async ({ page }, use) => {
        await use(async (componentRef, options) => {
            const selector = await innerMount(page, componentRef, options);

            const locator = page.locator(selector);

            // Object.assign(locator, {
            //     unmount: async () => {
            //         await locator.evaluate(async () => {
            //             const rootElement = document.getElementById("root");
            //             await window.playwrightUnmount(rootElement);
            //         });
            //     },
            //     update: async (options2) => {
            //         if (isJsxComponent(options2)) return await innerUpdate(page, options2);
            //         await innerUpdate(page, componentRef, options2);
            //     },
            // });

            return locator;
        });
    },
});
