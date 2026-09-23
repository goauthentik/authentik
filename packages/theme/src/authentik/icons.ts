/**
 * @file Icon sizes
 */

import { instance } from "../shared.js";

import { createUseVariable } from "@styleframe/theme";

const useIconSize = createUseVariable("icon.font-size");

export const iconSizes = useIconSize(instance, {
    sm: "0.625rem",
    md: "1.125rem",
    lg: "1.5rem",
    xl: "3.375rem",
});
