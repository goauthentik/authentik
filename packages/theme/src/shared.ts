import { styleframe } from "@styleframe/core";
import { createUseVariable } from "@styleframe/theme";
import { defaultVariableNameFn } from "@styleframe/transpiler";

export const instance = styleframe({
    indent: "    ",
    variables: {
        name: ({ name }) =>
            name.startsWith("pf-global.")
                ? defaultVariableNameFn({ name })
                : defaultVariableNameFn({ name: `ak-global.${name}` }),
    },
});

export const createPfGlobal = (category: string) => createUseVariable(`pf-global.${category}`);

export const {
    variable,
    theme,
    ref,
    selector,
    atRule,
    keyframes,
    media,
    css,
    utility,
    modifier,
    recipe,
} = instance;
