/// <reference types="docusaurus-theme-openapi-docs" />
/// <reference types="docusaurus-plugin-openapi-docs" />

declare module "@docusaurus/plugin-content-docs/src/sidebars/types" {
    export * from "@docusaurus/plugin-content-docs/src/sidebars/types.ts";
}

declare module "@theme/RequestSchema";
declare module "@theme/ParamsDetails";
declare module "@theme/StatusCodes";
declare module "@theme/OperationTabs";

declare module "@theme/SkeletonLoader" {
    import { FC } from "react";

    const SkeletonLoader: FC<{ size: "sm" | "md" | "lg" }>;
    export default SkeletonLoader;
}

declare module "@theme/APIExplorer" {
    import { FC } from "react";

    export interface ApiExplorerProps {
        item: unknown;
        infoPath: unknown;
    }

    const ApiExplorer: FC<ApiExplorerProps>;
    export default ApiExplorer;
}

declare module "@theme/ApiExplorer/persistanceMiddleware" {
    import { Middleware } from "@reduxjs/toolkit";
    import type { ThemeConfig } from "docusaurus-theme-openapi-docs/src/types";

    export const createPersistanceMiddleware: (options: ThemeConfig["api"]) => Middleware;
}
