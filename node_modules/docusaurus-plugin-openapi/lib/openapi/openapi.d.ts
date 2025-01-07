import { OpenApiObjectWithRef } from "./types";
import { ApiMetadata } from "../types";
interface OpenApiFiles {
    source: string;
    sourceDirName: string;
    data: OpenApiObjectWithRef;
}
export declare function readOpenapiFiles(openapiPath: string, _options: {}): Promise<OpenApiFiles[]>;
export declare function processOpenapiFiles(files: OpenApiFiles[], options: {
    baseUrl: string;
    routeBasePath: string;
    siteDir: string;
}): Promise<ApiMetadata[]>;
export declare function processOpenapiFile(openapiDataWithRefs: OpenApiObjectWithRef): Promise<ApiMetadata[]>;
export {};
