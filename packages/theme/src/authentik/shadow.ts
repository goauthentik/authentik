import { instance } from "../shared.js";

import { createUseVariable } from "@styleframe/theme";

// This is almost the same as the definition in Styleframe/theme, but:
// - Doesn't include Styleframe's defaults
// - Emphasizes that this is *just* a namespace

const useBoxShadowDesignTokens = createUseVariable("box-shadow");

// If you go look at Patternfly's ["Shadow Utility"
// page](https://v5-archive.patternfly.org/utility-classes/box-shadow), you can see what they're
// trying to do: there are two kinds of shadows, one that just lifts the paper above its surface
// evenly, with a slight extra push to the south, and one that lifts the paper directionally, as if
// it were curling up on edge.
//
// So, for each "size" (sm, md, lg, xl), there are five different shadows:
//
// 1. The "lifted" one, and
// 2. The "curled" ones, which are directional, rotated once for each direction. Patternfly calls
//    these "edged."
//
// Each "lifted" shadow actually has two shadows. The first is shifted down a bit, and tends to be
// darker (higher opacity), with a strong blur radius. It's the shadow cast by the object. The
// second one is supposed to be light bouncing off the *underside* of the lifted element, so it's
// uniform, with a lower blur radius and an even lower opacity, creating the subtle "halo" around
// the rest of the box.

// Each "lifted" shadow is progessively twice as "heavy" as the previous:
// 0 0.25rem 0.5rem 0rem rgba(3, 3, 3, 0.12), 0 0 0.25rem 0 rgba(3, 3, 3, 0.06);
// 0 0.5rem 1rem 0 rgba(3, 3, 3, 0.16), 0 0 0.375rem 0 rgba(3, 3, 3, 0.08);
//
// The exception to this is `sm`, which is actually placed where `xs` would be. Not sure why. The
// only other thing I haven't been able to figure out is the opacity; as near as I can tell, it's
// "it just looked right."

// Opacities are all clamped to three places anyway in the Patternfly code

const shadow = (opacity: number) => `rgba(3, 3, 3, ${opacity})`;

const mrem = (dim: number) => (Math.abs(dim) < 1 / 128 ? "0" : `${dim}rem`);

type LiftProgression = [
    size: string,
    cast_scale: number,
    cast_opacity: number,
    halo_scale: number,
    halo_opacity: number,
];

// prettier-ignore
const liftedProgressions: LiftProgression[] = [
    ['sm',  1, 0.12, 1, 0.06],
    ['md',  4, 0.12, 2, 0.06],
    ['lg',  8, 0.16, 3, 0.08],
    ['xl', 16, 0.16, 4, 0.10]]

//  sm: 0 0.0625rem 0.125rem 0rem rgba(3, 3, 3, 0.12), 0 0 0.125rem 0 rgba(3, 3, 3, 0.06);
//  md: 0   0.25rem   0.5rem 0rem rgba(3, 3, 3, 0.12), 0 0  0.25rem 0 rgba(3, 3, 3, 0.06);
//  lg: 0    0.5rem     1rem 0rem rgba(3, 3, 3, 0.16), 0 0 0.375rem 0 rgba(3, 3, 3, 0.08);
//  xl: 0      1rem     2rem 0rem rgba(3, 3, 3, 0.16), 0 0   0.5rem 0 rgba(3, 3, 3, 0.1);

// It's a little gross how Patternfly just assumes that you're a 16px person, and so 0.0625 is just
// "one pixel."  But it probably works all the time.

export const liftedBoxShadows = useBoxShadowDesignTokens(
    instance,
    liftedProgressions.reduce(
        (acc, [size, cast_scale, cast_opacity, halo_scale, halo_opacity]) => ({
            ...acc,
            [size]:
                `0 ${mrem(0.0625 * cast_scale)} ${mrem(0.125 * cast_scale)} 0 ${shadow(cast_opacity)}, ` +
                `0 0 ${mrem(0.125 * halo_scale)} 0 ${shadow(halo_opacity)}`,
        }),
        {} as Record<string, string>
    )
);

// The "edged" ones are much more straightforward, *except* XL, which chickens out and doesn't
// go for a full 0.75rem spread at the end.

type EdgeProgression = [
    size: string,
    cast_scale: number,
    blur_scale: number,
    spread_scale: number,
    opacity: number,
];

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

//   sm-top: 0 -0.125rem 0.25rem -0.0625rem rgba(3, 3, 3, 0.16);
//   sm-right: 0.125rem 0 0.25rem -0.0625rem rgba(3, 3, 3, 0.16);
//   sm-bottom: 0 0.125rem 0.25rem -0.0625rem rgba(3, 3, 3, 0.16);
//   sm-left: -0.125rem 0 0.25rem -0.0625rem rgba(3, 3, 3, 0.16);
//   md-top: 0 -0.5rem 0.5rem -0.375rem rgba(3, 3, 3, 0.18);
//   md-right: 0.5rem 0 0.5rem -0.375rem rgba(3, 3, 3, 0.18);
//   md-bottom: 0 0.5rem 0.5rem -0.375rem rgba(3, 3, 3, 0.18);
//   md-left: -0.5rem 0 0.5rem -0.375rem rgba(3, 3, 3, 0.18);
//   lg-top: 0 -0.75rem 0.75rem -0.5rem rgba(3, 3, 3, 0.18);
//   lg-right: 0.75rem 0 0.75rem -0.5rem rgba(3, 3, 3, 0.18);
//   lg-bottom: 0 0.75rem 0.75rem -0.5rem rgba(3, 3, 3, 0.18);
//   lg-left: -0.75rem 0 0.75rem -0.5rem rgba(3, 3, 3, 0.18);
//   xl-top: 0 -1rem 1rem -0.5rem rgba(3, 3, 3, 0.2);
//   xl-right: 1rem 0 1rem -0.5rem rgba(3, 3, 3, 0.2);
//   xl-bottom: 0 1rem 1rem -0.5rem rgba(3, 3, 3, 0.2);
//   xl-left: -1rem 0 1rem -0.5rem rgba(3, 3, 3, 0.2);
//

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
        {} as Record<string, string>
    )
);

export const insetBoxShadow = useBoxShadowDesignTokens(instance, {
    inset: "inset 0 0 0.625rem 0 rgba(3, 3, 3, 0.25)",
});
