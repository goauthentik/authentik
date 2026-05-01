import { expect, test as setup } from "#e2e";

setup("Web server availability", async ({ baseURL }) => {
    expect(baseURL, "Base URL is set").toBeTruthy();

    // Probe the default authentication flow rather than the root URL — the root
    // redirects to /setup when AUTHENTIK_BOOTSTRAP_* env vars are unset, and
    // /setup raises FlowNonApplicableException (HTTP 500) once an admin user
    // already has a usable password (as our test-admin blueprint installs).
    const probeURL = new URL("/if/flow/default-authentication-flow/", baseURL!);
    const ok = await fetch(probeURL)
        .then((res) => res.ok)
        .catch(() => false);

    expect(ok, `Web server should be serving ${probeURL}`).toBeTruthy();
});
