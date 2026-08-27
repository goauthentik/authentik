import { variable } from "../shared.js";

const pfvar = (pfKey: string, akKey: string) => variable(`pf-global.${pfKey}`, `@${akKey}`);

pfvar("ListStyle", "list-style");
pfvar("arrow.width", "arrow.width.md");
pfvar("arrow.width-lg", "arrow.width.lg");
pfvar("target-size.MinWidth", "target-size.min-width");
pfvar("target-size.MinHeight", "target-size.min-height");
pfvar("font-path", "font-path");
pfvar("fonticon-path", "fonticon-path");
