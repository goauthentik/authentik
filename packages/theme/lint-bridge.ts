import { instance } from "./dist/node.js";
import { patternflyLightTheme } from "./reference.css.ts";

import { isCSS, isRef, isVariable, rebuildRegistry } from "@styleframe/core";
import { formatHex8, parse } from "culori";

interface Scope {
    parentId?: string;
    variables?: { name: string; value: unknown }[];
}

interface Root extends Scope {
    _registry: Map<string, Scope>;
    themes: (Scope & { name: string })[];
}

type Resolution = [kind: "value" | "fallback" | "undefined" | "null", value: unknown];

function lookup(name: string, scope: Scope | undefined, root: Root) {
    let current = scope;
    while (current) {
        const found = current.variables?.find((v) => v.name === name);
        if (found) {
            return { variable: found, scope: current };
        }
        current = current.parentId ? root._registry.get(current.parentId) : undefined;
    }
    return undefined;
}

function getValue(value: unknown, scope: Scope, root: Root, seen: Set<string>): Resolution {
    if (value == null) {
        return ["null", ""];
    }

    if (Array.isArray(value)) {
        return ["value", value.map((v) => getValue(v, scope, root, seen)[1]).join(" ")];
    }

    if (isCSS(value)) {
        return ["value", value.value.map((v) => getValue(v, scope, root, seen)[1]).join("")];
    }

    // @styleframe/core's type for this value is wrong.
    if (isVariable(value)) {
        return getValue(value.value, lookup(value.name, scope, root)?.scope ?? scope, root, seen);
    }

    if (isRef(value)) {
        const { name } = value;
        if (seen.has(name)) {
            throw new Error(`Already seen this one, cycle? ${name}`);
        }

        seen.add(name);

        const found = lookup(name, scope, root);
        if (found) {
            return getValue(found.variable, found.scope, root, seen);
        }

        if (value.fallback) {
            const fallback = getValue(value.fallback, scope, root, seen);
            return ["fallback", fallback[1]];
        }

        return ["undefined", name];
    }

    return ["value", value];
}

function getVariable(name: string, { theme }: { theme?: string } = {}): Resolution | undefined {
    const root = instance.root as unknown as Root;
    if (!root._registry?.size) {
        rebuildRegistry(instance.root);
    }
    const scope = theme ? (root.themes.find((t) => t.name === theme) ?? root) : root;
    const found = lookup(name, scope, root);
    return found ? getValue(found.variable.value, found.scope, root, new Set([name])) : undefined;
}

const normalize = (value: unknown) => {
    const text = `${value}`
        .replace(/\/\*.*?\*\//g, "")
        .replace(/\s+/g, " ")
        .trim();
    const color = parse(text);

    return color ? formatHex8(color) : text;
};

let failures = 0;

for (const [key, expected] of Object.entries(patternflyLightTheme)) {
    const found = getVariable(key);

    if (!found || found[0] === "undefined") {
        console.log(`${key}: not defined by the bridge`);
        continue;
    }

    const [kind, resolution] = found;

    if (kind === "fallback") {
        console.log(`${key}: using fallback '${resolution}'`);
        continue;
    }

    const actual = normalize(resolution);

    if (!actual) {
        console.error(`${key}: EMPTY`);
        failures++;
    } else if (actual !== normalize(expected)) {
        console.error(`${key}: MISMATCH: ${resolution} !== ${expected}`);
        failures++;
    }
}

if (failures) {
    console.error(`${failures} PatternFly variable(s) differ from PatternFly 4's defaults.`);
    process.exitCode = 1;
}
