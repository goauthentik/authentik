import { ConsoleTestRunner } from "#tests/utils/logger";

export function navigateBrowser(to: string | URL = "/", baseURL = "http://localhost:9000") {
    const nextURL = new URL(to, baseURL);

    ConsoleTestRunner.info("🧭 Navigating to...", nextURL.href);

    return browser.url(nextURL.href);
}
