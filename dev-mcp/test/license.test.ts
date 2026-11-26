/**
 * @file License verification against a throwaway CA chain, built the way authentik's licenses
 *   are: root → intermediate → leaf, P-384 keys, an ES512 JWT carrying the chain in `x5c`.
 */

import { execFileSync } from "node:child_process";
import { createPrivateKey, sign } from "node:crypto";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { licenseSignal } from "#dev-mcp/guard";
import { isDevTestLicense, verifyLicense } from "#dev-mcp/license";

import { afterAll, beforeAll, describe, expect, it } from "vitest";

let dir: string;
let root: Buffer;
let otherRoot: Buffer;
let leafKey: string;
let chain: string[];

const openssl = (...args: string[]) => execFileSync("openssl", args, { cwd: dir, stdio: "pipe" });

function der(pem: string): string {
    return pem.replace(/-----[^-]+-----/g, "").replace(/\s+/g, "");
}

function makeCA(name: string, issuer?: string): void {
    openssl("ecparam", "-name", "secp384r1", "-genkey", "-noout", "-out", `${name}.key`);
    if (!issuer) {
        openssl(
            "req",
            "-x509",
            "-new",
            "-key",
            `${name}.key`,
            "-subj",
            `/CN=${name}`,
            "-days",
            "2",
            "-out",
            `${name}.pem`,
            "-addext",
            "basicConstraints=critical,CA:TRUE",
            "-addext",
            "keyUsage=critical,keyCertSign",
        );
        return;
    }
    writeFileSync(
        join(dir, `${name}.ext`),
        "basicConstraints=critical,CA:TRUE\nkeyUsage=critical,keyCertSign,digitalSignature\n",
    );
    openssl("req", "-new", "-key", `${name}.key`, "-subj", `/CN=${name}`, "-out", `${name}.csr`);
    openssl(
        "x509",
        "-req",
        "-in",
        `${name}.csr`,
        "-CA",
        `${issuer}.pem`,
        "-CAkey",
        `${issuer}.key`,
        "-CAcreateserial",
        "-days",
        "2",
        "-extfile",
        `${name}.ext`,
        "-out",
        `${name}.pem`,
    );
}

function license(claims: Record<string, unknown>, x5c = chain): string {
    const encode = (v: object) => Buffer.from(JSON.stringify(v)).toString("base64url");
    const input = `${encode({ alg: "ES512", typ: "JWT", x5c })}.${encode(claims)}`;
    const signature = sign("sha512", Buffer.from(input), {
        key: createPrivateKey(leafKey),
        dsaEncoding: "ieee-p1363",
    });
    return `${input}.${signature.toString("base64url")}`;
}

const DEV = { name: "dev", exp: 1, aud: "x", non_production: true, dev_test: true };
const STAGING = { name: "staging", exp: 1, aud: "x", non_production: true };

beforeAll(() => {
    dir = mkdtempSync(join(tmpdir(), "akdev-license-"));
    makeCA("root");
    makeCA("intermediate", "root");
    makeCA("leaf", "intermediate");
    makeCA("other");
    root = readFileSync(join(dir, "root.pem"));
    otherRoot = readFileSync(join(dir, "other.pem"));
    leafKey = readFileSync(join(dir, "leaf.key"), "utf8");
    chain = ["leaf", "intermediate"].map((n) => der(readFileSync(join(dir, `${n}.pem`), "utf8")));
});

afterAll(() => rmSync(dir, { recursive: true, force: true }));

describe("verifyLicense", () => {
    it("accepts a license signed through the chain", () => {
        const check = verifyLicense(license(DEV), root);
        expect(check.verified).toBe(true);
        expect(isDevTestLicense(check)).toBe(true);
    });

    it("rejects a chain that doesn't lead to the licensing CA", () => {
        expect(verifyLicense(license(DEV), otherRoot)).toEqual({
            verified: false,
            reason: "certificate chain doesn't lead to authentik's licensing CA",
        });
    });

    it("rejects a payload edited after signing", () => {
        const [h, , s] = license(STAGING).split(".");
        const edited = `${h}.${Buffer.from(JSON.stringify(DEV)).toString("base64url")}.${s}`;
        expect(verifyLicense(edited, root)).toMatchObject({ verified: false });
    });

    it("rejects garbage", () => {
        expect(verifyLicense("not-a-jwt", root)).toMatchObject({ verified: false });
    });
});

describe("licenseSignal", () => {
    it("passes with no license, or only verified dev_test licenses", () => {
        expect(licenseSignal([], root).tripped).toBe(false);
        expect(licenseSignal(null, root).tripped).toBe(false);
        expect(licenseSignal([license(DEV), license(DEV)], root).tripped).toBe(false);
    });

    it("fires for a non_production license without dev_test", () => {
        expect(licenseSignal([license(STAGING)], root).tripped).toBe(true);
    });

    it("fires when any one license isn't dev_test", () => {
        expect(licenseSignal([license(DEV), license(STAGING)], root).tripped).toBe(true);
    });

    it("fires for a dev_test claim from an untrusted chain, and says why", () => {
        const result = licenseSignal([license(DEV)], otherRoot);
        expect(result.tripped).toBe(true);
        expect(result.detail).toContain("doesn't lead to authentik's licensing CA");
    });
});
