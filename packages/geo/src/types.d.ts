declare module "*.css" {
    import { CSSResult } from "lit";

    const css: CSSResult & { readonly __brand?: string };
    export default css;
}
