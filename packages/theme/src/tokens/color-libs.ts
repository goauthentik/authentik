import { createVariableFunction } from "styleframe";
import { createUseVariable } from "@styleframe/theme";
import { formatHex, oklch as toOklch, toGamut } from "culori";

import { type Reference } from "styleframe";
export type Variable = ReturnType<ReturnType<typeof createVariableFunction>>;
export type VPPair = [Variable, string];

/*
 * Restrict the OKLCH values to six decimal places; Javascript will give it to you accurate to 16
 * places, but OKLCH doesn't much care past six, and 16 is just unreadable.
 *
 * Includes in each OKLCH output line a comment containing the RGB value, to help IDEs show the
 * color accurately.
 */


const toSrgb = toGamut("rgb", "oklch");
const round = (v: number, precision = 6) => Number(v.toFixed(precision)).toString();
export const oklchTransform = (value: string | Reference<string>) => {
    if (typeof value !== "string") {
        return value;
    }
    
    const c = toOklch(value);
    if (!c || c.l === null || c.c === null) {
        return value;
    }
    
    const result = `oklch(${round(c.l)} ${round(c.c)} ${round(c.h ?? 0)} / ${round(c.alpha ?? 1)})`;
    return `${result} /* ${formatHex(toSrgb(c))} */`;
};
export const useColorDesignTokens = createUseVariable("color", { transform: oklchTransform });
