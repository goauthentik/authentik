import { instance } from "../shared.js";

import { styleframe } from "@styleframe/core";
import { createUseVariable } from "@styleframe/theme";

export const createPfGlobal = (category: string) => createUseVariable(`pf-global.${category}`);

export const bridge =
    (prefix: string) =>
    (names: string | string[], ...rest: string[]) =>
        Object.fromEntries(
            (Array.isArray(names) ? [...names, ...rest] : [names, ...rest]).map((name) => [
                `${name}`,
                `${prefix}${name ? "." : ""}${name}`,
            ])
        );

const extractKeys = (instance: ReturnType<typeof styleframe>, namespace: string): string[] =>
    instance.root.variables
        .map(({ name }) => name as string)
        .filter((name) => name.startsWith(namespace))
        .map((name) => name.replace(`${namespace}.`, ""));

export const bridgePFGlobals = (pfns: string, akns: string, ...rest: [object] | string[]) => {
    const keys = (rest.length === 0 ? extractKeys(instance, akns) : rest) as string[];
    return createPfGlobal(pfns)(instance, bridge(`@${akns}`)(keys));
};
