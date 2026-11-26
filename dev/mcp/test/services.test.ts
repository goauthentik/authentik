import { type Runtime, containerRuntime } from "#dev-mcp/environment/runtime";
import { SERVICES, composeCommand, composeUpFix } from "#dev-mcp/environment/services";
import { run } from "#dev/lib/process";

import { describe, expect, it } from "vitest";

const runtime = (overrides: Partial<Runtime>): Runtime => ({
    kind: "docker",
    running: true,
    compose: "docker compose",
    dockerComposeWorks: true,
    detail: "",
    ...overrides,
});

const none = runtime({ kind: "none", running: false, compose: null, dockerComposeWorks: false });
const podman = runtime({ kind: "podman", compose: "podman compose", dockerComposeWorks: false });

describe("compose commands", () => {
    it("names the services for up, and keeps volumes on down", () => {
        expect(composeCommand(podman, "up")).toEqual([
            "podman",
            "compose",
            "-f",
            "scripts/compose.yml",
            "up",
            "-d",
            ...SERVICES,
        ]);

        expect(composeCommand(runtime({}), "down")).not.toContain("-v");
    });

    it("has nothing to run without a runtime or compose", () => {
        expect(composeCommand(none, "up")).toBeNull();
        expect(composeCommand(runtime({ compose: null }), "status")).toBeNull();
        expect(composeUpFix(none)).toBeNull();
    });

    it("says what to start first", () => {
        expect(composeUpFix(runtime({ kind: "podman", running: false }))).toMatch(/^Start Podman/);
        expect(composeUpFix(runtime({ compose: null }))).toContain("`docker compose -f");
    });
});

// The only test that touches a real runtime: it reads the compose file, never starts anything.
const real = await containerRuntime();
const status = composeCommand(real, "status");

describe.skipIf(!status)("the real compose provider", () => {
    it(`parses scripts/compose.yml with ${real.compose}`, async () => {
        const [command, ...args] = status!.slice(0, -1);
        const out = await run(command!, [...args, "config"], { timeoutMs: 60_000 });

        expect(out.code).toBe(0);

        for (const service of SERVICES) expect(out.stdout).toContain(service);
    });
});
