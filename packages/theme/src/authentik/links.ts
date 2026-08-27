/**
 * @file Link tokens — decorations and colors for links
 */

import { instance } from "../shared.js";

import { createUseVariable } from "@styleframe/theme";

const useLinkTextDecorations = createUseVariable("link.text-decoration");

export const linkTextDecoration = useLinkTextDecorations(instance, {
    default: "none",
    hover: "underline",
});
