/**
 * @file TypeScript type definitions for eslint-plugin-react-hooks
 */
declare module "eslint-plugin-react-hooks" {
    import { ESLint } from "eslint";
    // We have to do this because ESLint aliases the namespace and class simultaneously.
    type PluginInstance = ESLint.Plugin;
    const Plugin: PluginInstance;

    export default Plugin;
}
