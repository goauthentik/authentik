import type { JSONSchema4, JSONSchema6, JSONSchema7 } from "json-schema";
interface Map<T> {
    [key: string]: T;
}
export interface OpenApiObject {
    openapi: string;
    info: InfoObject;
    servers?: ServerObject[];
    paths: PathsObject;
    components?: ComponentsObject;
    security?: SecurityRequirementObject[];
    tags?: TagObject[];
    externalDocs?: ExternalDocumentationObject;
    swagger?: string;
    webhooks?: PathsObject;
    "x-webhooks"?: PathsObject;
    "x-tagGroups"?: TagGroupObject[];
}
export interface OpenApiObjectWithRef {
    openapi: string;
    info: InfoObject;
    servers?: ServerObject[];
    paths: PathsObjectWithRef;
    components?: ComponentsObjectWithRef;
    security?: SecurityRequirementObject[];
    tags?: TagObject[];
    externalDocs?: ExternalDocumentationObject;
}
export interface InfoObject {
    title: string;
    description?: string;
    termsOfService?: string;
    contact?: ContactObject;
    license?: LicenseObject;
    version: string;
    tags?: TagObject[];
    "x-logo"?: LogoObject;
    "x-dark-logo"?: LogoObject;
    logo?: LogoObject;
    darkLogo?: LogoObject;
}
export interface LogoObject {
    url?: string;
}
export interface ContactObject {
    name?: string;
    url?: string;
    email?: string;
}
export interface LicenseObject {
    name: string;
    url?: string;
}
export interface ServerObject {
    url: string;
    description?: string;
    variables?: Map<ServerVariable>;
}
export interface ServerVariable {
    enum?: string[];
    default: string;
    description?: string;
}
export interface ComponentsObject {
    schemas?: Map<SchemaObject>;
    responses?: Map<ResponseObject>;
    parameters?: Map<ParameterObject>;
    examples?: Map<ExampleObject>;
    requestBodies?: Map<RequestBodyObject>;
    headers?: Map<HeaderObject>;
    securitySchemes?: Map<SecuritySchemeObject>;
    links?: Map<LinkObject>;
    callbacks?: Map<CallbackObject>;
}
export interface ComponentsObjectWithRef {
    schemas?: Map<SchemaObjectWithRef | ReferenceObject>;
    responses?: Map<ResponseObjectWithRef | ReferenceObject>;
    parameters?: Map<ParameterObjectWithRef | ReferenceObject>;
    examples?: Map<ExampleObject | ReferenceObject>;
    requestBodies?: Map<RequestBodyObjectWithRef | ReferenceObject>;
    headers?: Map<HeaderObjectWithRef | ReferenceObject>;
    securitySchemes?: Map<SecuritySchemeObject | ReferenceObject>;
    links?: Map<LinkObject | ReferenceObject>;
    callbacks?: Map<CallbackObjectWithRef | ReferenceObject>;
}
export type PathsObject = Map<PathItemObject>;
export type PathsObjectWithRef = Map<PathItemObjectWithRef>;
export interface PathItemObject {
    $ref?: string;
    summary?: string;
    description?: string;
    get?: OperationObject;
    put?: OperationObject;
    post?: OperationObject;
    delete?: OperationObject;
    options?: OperationObject;
    head?: OperationObject;
    patch?: OperationObject;
    trace?: OperationObject;
    servers?: ServerObject[];
    parameters?: ParameterObject[];
}
export interface PathItemObjectWithRef {
    $ref?: string;
    summary?: string;
    description?: string;
    get?: OperationObjectWithRef;
    put?: OperationObjectWithRef;
    post?: OperationObjectWithRef;
    delete?: OperationObjectWithRef;
    options?: OperationObjectWithRef;
    head?: OperationObjectWithRef;
    patch?: OperationObjectWithRef;
    trace?: OperationObjectWithRef;
    servers?: ServerObject[];
    parameters?: (ParameterObjectWithRef | ReferenceObject)[];
}
export interface OperationObject {
    tags?: string[];
    summary?: string;
    description?: string;
    externalDocs?: ExternalDocumentationObject;
    operationId?: string;
    parameters?: ParameterObject[];
    requestBody?: RequestBodyObject;
    responses: ResponsesObject;
    callbacks?: Map<CallbackObject>;
    deprecated?: boolean;
    security?: SecurityRequirementObject[];
    servers?: ServerObject[];
    "x-deprecated-description"?: string;
}
export interface OperationObjectWithRef {
    tags?: string[];
    summary?: string;
    description?: string;
    externalDocs?: ExternalDocumentationObject;
    operationId?: string;
    parameters?: (ParameterObjectWithRef | ReferenceObject)[];
    requestBody?: RequestBodyObjectWithRef | ReferenceObject;
    responses: ResponsesObjectWithRef;
    callbacks?: Map<CallbackObjectWithRef | ReferenceObject>;
    deprecated?: boolean;
    security?: SecurityRequirementObject[];
    servers?: ServerObject[];
    "x-deprecated-description"?: string;
}
export interface ExternalDocumentationObject {
    description?: string;
    url: string;
}
export interface ParameterObject {
    name: string;
    in: "query" | "header" | "path" | "cookie";
    description?: string;
    required?: boolean;
    deprecated?: boolean;
    allowEmptyValue?: boolean;
    style?: string;
    explode?: string;
    allowReserved?: boolean;
    schema?: SchemaObject;
    example?: any;
    examples?: Map<ExampleObject>;
    content?: Map<MediaTypeObject>;
    param?: Object;
    "x-enumDescriptions"?: Record<string, string>;
}
export interface ParameterObjectWithRef {
    name: string;
    in: string;
    description?: string;
    required?: boolean;
    deprecated?: boolean;
    allowEmptyValue?: boolean;
    style?: string;
    explode?: string;
    allowReserved?: boolean;
    schema?: SchemaObjectWithRef | ReferenceObject;
    example?: any;
    examples?: Map<ExampleObject | ReferenceObject>;
    content?: Map<MediaTypeObjectWithRef>;
}
export interface RequestBodyObject {
    description?: string;
    content: Map<MediaTypeObject>;
    required?: boolean;
}
export interface RequestBodyObjectWithRef {
    description?: string;
    content: Map<MediaTypeObjectWithRef>;
    required?: boolean;
}
export interface MediaTypeObject {
    schema?: SchemaObject;
    example?: any;
    examples?: Map<ExampleObject>;
    encoding?: Map<EncodingObject>;
    type?: any;
}
export interface MediaTypeObjectWithRef {
    schema?: SchemaObjectWithRef | ReferenceObject;
    example?: any;
    examples?: Map<ExampleObject | ReferenceObject>;
    encoding?: Map<EncodingObjectWithRef>;
}
export interface EncodingObject {
    contentType?: string;
    headers?: Map<HeaderObject>;
    style?: string;
    explode?: boolean;
    allowReserved?: boolean;
}
export interface EncodingObjectWithRef {
    contentType?: string;
    headers?: Map<HeaderObjectWithRef | ReferenceObject>;
    style?: string;
    explode?: boolean;
    allowReserved?: boolean;
}
export type ResponsesObject = Map<ResponseObject>;
export type ResponsesObjectWithRef = Map<ResponseObjectWithRef | ReferenceObject>;
export interface ResponseObject {
    description: string;
    headers?: Map<HeaderObject>;
    content?: Map<MediaTypeObject>;
    links?: Map<LinkObject>;
}
export interface ResponseObjectWithRef {
    description: string;
    headers?: Map<HeaderObjectWithRef | ReferenceObject>;
    content?: Map<MediaTypeObjectWithRef>;
    links?: Map<LinkObject | ReferenceObject>;
}
export type CallbackObject = Map<PathItemObject>;
export type CallbackObjectWithRef = Map<PathItemObjectWithRef>;
export interface ExampleObject {
    summary?: string;
    description?: string;
    value?: any;
    externalValue?: string;
}
export interface LinkObject {
    operationRef?: string;
    operationId?: string;
    parameters?: Map<any>;
    requestBody?: any;
    description?: string;
    server?: ServerObject;
}
export type HeaderObject = Omit<ParameterObject, "name" | "in">;
export type HeaderObjectWithRef = Omit<ParameterObjectWithRef, "name" | "in">;
export interface TagObject {
    name?: string;
    description?: string;
    externalDocs?: ExternalDocumentationObject;
    "x-displayName"?: string;
}
export interface TagGroupObject {
    name: string;
    tags: string[];
}
export interface ReferenceObject {
    $ref: string;
}
export type JSONSchema = JSONSchema4 | JSONSchema6 | JSONSchema7;
export type SchemaObject = Omit<JSONSchema, "type" | "allOf" | "oneOf" | "anyOf" | "not" | "items" | "properties" | "additionalProperties"> & {
    type?: "string" | "number" | "integer" | "boolean" | "object" | "array";
    allOf?: SchemaObject[];
    oneOf?: SchemaObject[];
    anyOf?: SchemaObject[];
    not?: SchemaObject;
    items?: SchemaObject;
    properties?: Map<SchemaObject>;
    additionalProperties?: boolean | SchemaObject;
    nullable?: boolean;
    discriminator?: DiscriminatorObject;
    readOnly?: boolean;
    writeOnly?: boolean;
    xml?: XMLObject;
    externalDocs?: ExternalDocumentationObject;
    example?: any;
    deprecated?: boolean;
    "x-tags"?: string[];
    "x-enumDescriptions"?: Record<string, string>;
};
export type SchemaObjectWithRef = Omit<JSONSchema, "type" | "allOf" | "oneOf" | "anyOf" | "not" | "items" | "properties" | "additionalProperties"> & {
    type?: "string" | "number" | "integer" | "boolean" | "object" | "array";
    allOf?: (SchemaObject | ReferenceObject)[];
    oneOf?: (SchemaObject | ReferenceObject)[];
    anyOf?: (SchemaObject | ReferenceObject)[];
    not?: SchemaObject | ReferenceObject;
    items?: SchemaObject | ReferenceObject;
    properties?: Map<SchemaObject | ReferenceObject>;
    additionalProperties?: boolean | SchemaObject | ReferenceObject;
    nullable?: boolean;
    discriminator?: DiscriminatorObject;
    readOnly?: boolean;
    writeOnly?: boolean;
    xml?: XMLObject;
    externalDocs?: ExternalDocumentationObject;
    example?: any;
    deprecated?: boolean;
};
export interface DiscriminatorObject {
    propertyName: string;
    mapping?: Map<string>;
}
export interface XMLObject {
    name?: string;
    namespace?: string;
    prefix?: string;
    attribute?: boolean;
    wrapped?: boolean;
}
export type SecuritySchemeObject = ApiKeySecuritySchemeObject | HttpSecuritySchemeObject | Oauth2SecuritySchemeObject | OpenIdConnectSecuritySchemeObject;
export interface ApiKeySecuritySchemeObject {
    type: "apiKey";
    description?: string;
    name: string;
    in: "query" | "header" | "cookie";
}
export interface HttpSecuritySchemeObject {
    type: "http";
    description?: string;
    scheme: string;
    bearerFormat?: string;
    name?: string;
    in?: string;
}
export interface Oauth2SecuritySchemeObject {
    type: "oauth2";
    description?: string;
    flows: OAuthFlowsObject;
}
export interface OpenIdConnectSecuritySchemeObject {
    type: "openIdConnect";
    description?: string;
    openIdConnectUrl: string;
}
export interface OAuthFlowsObject {
    implicit?: OAuthFlowObject;
    password?: OAuthFlowObject;
    clientCredentials?: OAuthFlowObject;
    authorizationCode?: OAuthFlowObject;
}
export interface OAuthFlowObject {
    authorizationUrl?: string;
    tokenUrl?: string;
    refreshUrl?: string;
    scopes: Map<string>;
}
export type SecurityRequirementObject = Map<string[]>;
export {};
