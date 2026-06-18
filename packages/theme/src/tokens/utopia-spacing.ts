/**
 * @file Spacing tokens — single scale from xs (4px) to 4xl (80px) at 16px base.
 */

import { instance } from "../shared.js";

import { createUseVariable } from "@styleframe/theme";
// 4, 8, 16, 24, 32, 48, 60 pixels: the "standard" progression.
import { calculateSpaceScale } from "utopia-core";

const useSpacing = createUseVariable("space");

const utopiaScale = calculateSpaceScale({
    minWidth: 320,
    maxWidth: 1440,
    minSize: 13,
    maxSize: 18,
    positiveSteps: [1.5, 2, 3, 4, 6],
    negativeSteps: [0.25, 0.5],
}).sizes;

if (utopiaScale === undefined) {
    throw new Error("Failed to parse utopiaScale configuration for utopia spacing.");
}

const utopiaSpacing = ["xs", "sm", "md", "lg", "xl", "2xl", "3xl", "4xl"].reduce((acc, s, idx) => {
    const size = utopiaScale[idx];
    if (!size) {
        throw new Error("Scale elements out of range for utopia spacing.");
    }
    return {
        ...acc,
        [s]: size.clamp
    }
},
    {}
);

export const space = useSpacing(instance, utopiaSpacing);
