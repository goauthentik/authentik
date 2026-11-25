/**
 * @file Unit and drift tests for the dev MCP server's pure parts.
 */

import { SCHEMA_FILES } from "../src/checks/generated.ts";
import { jobs, unmappedJobs } from "../src/checks/lint.ts";
import { genDiffPaths } from "../src/ci.ts";
import type { AllowEntry, Environment, PostgresKind } from "../src/discovery.ts";
import { type Verdict, staticChecks, suggestedAllowlist } from "../src/guard.ts";
import { Result } from "../src/result.ts";
import { INSTRUCTIONS } from "../src/server.ts";
import { readSkill } from "../src/skills.ts";

import { describe, expect, it } from "vitest";

interface EnvOptions {
    host?: string;
    name?: string;
    debug?: unknown;
    kind?: PostgresKind;
    local?: boolean;
    allowed?: AllowEntry[];
}

function makeEnv(options: EnvOptions = {}): Environment {
    const {
        host = "localhost",
        name = "authentik",
        debug = true,
        kind = "container",
        local = true,
        allowed = [],
    } = options;
    return {
        config: {
            debug: { value: debug, source: "local.env.yml" },
            pgHost: { value: host, source: "default" },
            pgPort: { value: 5432, source: "default" },
            pgName: { value: name, source: "default" },
            pgUser: { value: "postgres", source: "local.env.yml" },
            files: ["authentik/lib/default.yml", "local.env.yml"],
            allowedDatabases: allowed,
            password: "",
            error: null,
        },
        runtime: {
            kind: "docker",
            running: true,
            compose: "docker compose",
            dockerComposeWorks: true,
            detail: "",
        },
        postgres: { kind, local, container: null, detail: "" },
        hostTools: {},
        toolchains: {},
        languageServers: {},
    };
}

const failed = (env: Environment, environ: NodeJS.ProcessEnv = {}) =>
    staticChecks(env, environ)
        .filter((c) => !c.ok)
        .map((c) => c.name);

describe("guard", () => {
    it("admits a local dev database however Postgres runs", () => {
        expect(failed(makeEnv())).toEqual([]);
        expect(failed(makeEnv({ kind: "local" }))).toEqual([]);
        expect(failed(makeEnv({ host: "/tmp", kind: "socket" }))).toEqual([]);
    });

    it("refuses debug off", () => {
        expect(failed(makeEnv({ debug: false }))).toEqual(["debug"]);
    });

    it("needs a remote database listed by host, not just by name", () => {
        const remote = { host: "devvm.lan", kind: "remote", local: false } as const;
        expect(failed(makeEnv(remote))).toEqual(["connection"]);
        expect(failed(makeEnv({ ...remote, allowed: [{ name: "authentik" }] }))).toEqual([
            "connection",
        ]);
        expect(
            failed(makeEnv({ ...remote, allowed: [{ name: "authentik", host: "devvm.lan" }] })),
        ).toEqual([]);
    });

    it("needs an unfamiliar database name listed", () => {
        expect(failed(makeEnv({ name: "prod" }))).toEqual(["database_name"]);
        expect(failed(makeEnv({ name: "prod", allowed: [{ name: "prod" }] }))).toEqual([]);
    });

    it("reduces tools when AUTHENTIK_TOKEN is set", () => {
        expect(failed(makeEnv(), { AUTHENTIK_TOKEN: "x" })).toEqual(["no_token"]);
    });

    it("suggests ignoring only the signals that fired", () => {
        const verdict: Verdict = {
            ok: false,
            allowlistChanged: false,
            checks: [
                { name: "signal_license", ok: false, detail: "" },
                { name: "signal_users", ok: true, detail: "" },
                { name: "signal_external_logins", ok: false, detail: "" },
            ],
        };
        const snippet = suggestedAllowlist(makeEnv(), verdict) ?? "";
        expect(snippet).toContain("ignore_signals: [license, external_logins]");
        expect(snippet).not.toContain("host:");
        expect(
            suggestedAllowlist(makeEnv(), { ok: true, checks: [], allowlistChanged: false }),
        ).toBeNull();
    });
});

describe("drift with CI", () => {
    it("maps every ci-lint job in the Makefile and the CI matrix", () => {
        expect([...unmappedJobs()]).toEqual([]);
    });

    it("checks the same generated paths as test-gen", () => {
        const paths = genDiffPaths();
        for (const path of SCHEMA_FILES) expect(paths).toContain(path);
        expect(
            paths.filter((p) => !(SCHEMA_FILES as readonly string[]).includes(p)).sort(),
        ).toEqual(["packages/client-go", "packages/client-rust", "packages/client-ts"]);
    });
});

describe("lint mapping", () => {
    const jobsFor = (path: string) =>
        jobs()
            .filter((j) => j.covers(path))
            .map((j) => j.name);

    it("maps Python, migrations included only for migration files", () => {
        const py = jobsFor("authentik/core/models.py");
        expect(py).toEqual(
            expect.arrayContaining(["ruff", "black", "mypy", "bandit", "pending-migrations"]),
        );
        expect(py).not.toContain("migrations");
        expect(jobsFor("authentik/core/migrations/0099_x.py")).toContain("migrations");
    });

    it("keeps xliff out of the web jobs", () => {
        expect(jobsFor("web/src/admin/AdminInterface.ts")).toContain("web-tsc");
        expect(jobsFor("web/xliff/de.xlf")).toContain("locales");
        expect(jobsFor("web/xliff/de.xlf")).not.toContain("web-tsc");
    });

    it("maps Rust and docs", () => {
        expect(jobsFor("src/server/static.rs")).toEqual(
            expect.arrayContaining(["clippy", "rustfmt"]),
        );
        expect(jobsFor("website/docs/index.mdx")).toContain("website-check");
    });
});

describe("result", () => {
    it("names skipped and unknown items in the summary", () => {
        const result = new Result("t");
        result.skip("clients", "no docker");
        result.unsure("locales", "msgfmt missing");
        result.finish("Checked schema");
        expect(result.summary).toContain("Skipped: clients (no docker)");
        expect(result.summary).toContain("Unknown: locales (msgfmt missing)");
    });
});

describe("skills and instructions", () => {
    it("refuses skill names that leave the skills directory", () => {
        expect(readSkill("../../AGENTS")).toBeNull();
        expect(readSkill("testing")).toContain("name: testing");
    });

    it("keeps the rules in the first 512 characters, for Codex", () => {
        const head = INSTRUCTIONS.slice(0, 512);
        for (const rule of ["akdev_generated", "akdev_lint", "akdev_skill", "skipped"]) {
            expect(head).toContain(rule);
        }
        expect(INSTRUCTIONS.length).toBeLessThanOrEqual(4096);
    });
});
