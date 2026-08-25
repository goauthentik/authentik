import { instance } from "./dist/node.js";
import { patternflyLightTheme } from "./reference.css.js";

import { isCSS, isRef, isVariable, rebuildRegistry } from "@styleframe/core";

function lookup(name, scope, root) {
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

// type TokenValue = PrimitiveTokenValue | Reference | CSS | Array<PrimitiveTokenValue | Reference | CSS>

function getValue(value, scope, root, seen) {
    if (value == null) {
        return ["null", ""];
    }

    if (Array.isArray(value)) {
        return value.map((v) => getValue(v, scope, root, seen)).join(" ");
    }

    if (isCSS(value)) {
        return value.value.map((v) => getValue(v, scope, root, seen)).join("");
    }

    // This is broken. I had to find this one myself. Apparently, the type from @styleframe/core is
    // wrong.
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
            return getValue(found.variable, value, found.scope, root, seen);
        }

        if (value.fallback) {
            const fallback = getValue(value.fallback, scope, root, seen);
            return ["fallback", fallback[1]];
        }

        return ["undefined", name];
    }

    return ["value", value];
}

function getVariable(instance, name, { theme } = {}) {
    const root = instance.root;
    if (!root._registry?.size) {
        rebuildRegistry(root);
    }
    const scope = theme ? (root.themes.find((t) => t.name === theme) ?? root) : root;
    const found = lookup(name, scope, root);
    return found ? getValue(found.variable.value, found.scope, root, new Set([name])) : undefined;
}

for (const [key, value] of Object.entries(patternflyLightTheme)) {
    const found = getVariable(instance, key);
    if (!found) {
        console.log(`${key}: undefined`);
        continue;
    }

    const [kind, resolution] = found;

    if (kind === "value") {
        console.log(
            `${key}: ${`${resolution}` === `${value}` ? value : `MISMATCH: ${resolution} !== ${value}`}`
        );
        continue;
    }

    if (kind === "fallback") {
        console.log(`${key}: Present but undefined in Authentik, using fallback '${value}'`);
        continue;
    }

    if (kind === "undefined") {
        console.log(`${key}: Present but undefined in Authentik, no fallback.`);
        continue;
    }
}
