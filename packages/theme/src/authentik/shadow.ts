import { instance } from "../shared.js";

import { createUseVariable } from "@styleframe/theme";

// Styleframe's own box-shadow helper would also emit its defaults.
const useBoxShadowDesignTokens = createUseVariable("box-shadow");

const shadow = (opacity: number) => `rgba(3, 3, 3, ${opacity})`;

const mrem = (dim: number) => (Math.abs(dim) < 1 / 128 ? "0" : `${dim}rem`);

type LiftProgression = [
    size: string,
    cast_scale: number,
    cast_opacity: number,
    halo_scale: number,
    halo_opacity: number,
];

// PatternFly 4's scale, which isn't regular: `sm` sits where `xs` would.
// prettier-ignore
const liftedProgressions: LiftProgression[] = [
    ['sm',  1, 0.12, 1, 0.06],
    ['md',  4, 0.12, 2, 0.06],
    ['lg',  8, 0.16, 3, 0.08],
    ['xl', 16, 0.16, 4, 0.10]];

export const liftedBoxShadows = useBoxShadowDesignTokens(
    instance,
    liftedProgressions.reduce(
        (acc, [size, cast_scale, cast_opacity, halo_scale, halo_opacity]) => ({
            ...acc,
            [size]:
                `0 ${mrem(0.0625 * cast_scale)} ${mrem(0.125 * cast_scale)} 0 ${shadow(cast_opacity)}, ` +
                `0 0 ${mrem(0.125 * halo_scale)} 0 ${shadow(halo_opacity)}`,
        }),
        {} as Record<string, string>,
    ),
);

type EdgeProgression = [
    size: string,
    cast_scale: number,
    blur_scale: number,
    spread_scale: number,
    opacity: number,
];

// PatternFly 4's `xl` edge shadow keeps the `lg` spread.
// prettier-ignore
const edgeProgressions: EdgeProgression[] = [
    ["sm", 1, 1, 1, 0.16],
    ["md", 4, 2, 6, 0.18],
    ["lg", 6, 3, 8, 0.18],
    ["xl", 8, 4, 8, 0.20]
];

type Edges = [direction: string, x: number, y: number];

// prettier-ignore
const edges: Edges[] = [
    ["top",     0, -1],
    ["right",   1,  0],
    ["bottom",  0,  1],
    ["left",   -1,  0]
];

export const edgeBoxShadows = useBoxShadowDesignTokens(
    instance,
    edgeProgressions.reduce(
        (acc, [size, cast_scale, blur_scale, spread_scale, opacity]) => {
            const shade = `${mrem(0.25 * blur_scale)} ${mrem(-0.0625 * spread_scale)} ${shadow(opacity)}`;
            for (const [direction, x, y] of edges) {
                acc[`${size}-${direction}`] =
                    `${mrem(0.125 * cast_scale * x)} ${mrem(0.125 * cast_scale * y)} ${shade}`;
            }
            return acc;
        },
        {} as Record<string, string>,
    ),
);

export const insetBoxShadow = useBoxShadowDesignTokens(instance, {
    inset: "inset 0 0 0.625rem 0 rgba(3, 3, 3, 0.25)",
});
