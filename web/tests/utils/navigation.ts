import { ConsoleTestRunner } from "#tests/utils/logger";
import { browser } from "@wdio/globals";

export function navigateBrowser(to: string | URL = "/", baseURL = "http://localhost:9000") {
    const nextURL = new URL(to, baseURL);

    ConsoleTestRunner.info("🧭 🔜 Navigating to...", nextURL.href);

    return browser
        .url(nextURL.href)
        .then((request) => {
            if (request?.error) {
                ConsoleTestRunner.error("🧭 ❌ Request error...", nextURL.href);

                throw new Error(`A request error occurred while loading ${nextURL.href}`, {
                    cause: request.error,
                });
            }

            ConsoleTestRunner.info("🧭 ✅ Navigated to...", nextURL.href);
        })
        .catch((error) => {
            ConsoleTestRunner.error("🧭 ❌ Failed to load...", nextURL.href);

            throw new Error(`Failed to load ${nextURL.href}`, { cause: error });
        });
}
