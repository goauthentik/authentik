import { expect, test as setup } from "#e2e";

setup("Web server availability", async ({ baseURL }) => {
    expect(baseURL, "Base URL is set").toBeTruthy();

    const ok = await fetch(baseURL!)
        .then((res) => res.ok)
        .catch(() => false);

    expect(ok, `Web server should be listening on ${baseURL}`).toBeTruthy();
});
