import type { OpenAPIContact, OpenAPIInfo, OpenAPILicense } from '../../types';
import type { OpenAPIParser } from '../OpenAPIParser';
import { RedocNormalizedOptions } from '../RedocNormalizedOptions';
export declare class ApiInfoModel implements OpenAPIInfo {
    private parser;
    private options;
    title: string;
    version: string;
    description: string;
    summary: string;
    termsOfService?: string;
    contact?: OpenAPIContact;
    license?: OpenAPILicense;
    downloadLink?: string;
    downloadFileName?: string;
    constructor(parser: OpenAPIParser, options?: RedocNormalizedOptions);
    private getDownloadLink;
    private getDownloadFileName;
}
