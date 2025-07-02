import BrowserOnly from "@docusaurus/BrowserOnly";
import ExecutionEnvironment from "@docusaurus/ExecutionEnvironment";
import { DocProvider } from "@docusaurus/plugin-content-docs/client";
import { HtmlClassNameProvider } from "@docusaurus/theme-common";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import useIsBrowser from "@docusaurus/useIsBrowser";
import type { ApiExplorerProps } from "@theme/APIExplorer";
import { createAuth } from "@theme/ApiExplorer/Authorization/slice";
import { createPersistanceMiddleware } from "@theme/ApiExplorer/persistanceMiddleware";
import DocItemLayout from "@theme/ApiItem/Layout";
import CodeBlock from "@theme/CodeBlock";
import DocItemMetadata from "@theme/DocItem/Metadata";
import SkeletonLoader from "@theme/SkeletonLoader";
import clsx from "clsx";
import { ParameterObject, ServerObject } from "docusaurus-plugin-openapi-docs/src/openapi/types";
import type { ApiItem as ApiItemType } from "docusaurus-plugin-openapi-docs/src/types";
import type { ThemeConfig } from "docusaurus-theme-openapi-docs/src/types";
import { ungzip } from "pako";
import React from "react";
import { Provider } from "react-redux";

import { APIStore, createStoreWithoutState, createStoreWithState } from "./store";

let ApiExplorer: React.FC<ApiExplorerProps> = () => <div />;

if (ExecutionEnvironment.canUseDOM) {
    // @ts-expect-error - Dynamic import
    ApiExplorer = await import("@theme/ApiExplorer").then((mod) => mod.default);
}

function base64ToUint8Array(base64: string) {
    const binary = atob(base64);
    const len = binary.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
        bytes[i] = binary.charCodeAt(i);
    }
    return bytes;
}

function decodeAPI(encodedAPI: string): ApiItemType | null {
    try {
        return JSON.parse(
            ungzip(base64ToUint8Array(encodedAPI), {
                to: "string",
            }),
        );
    } catch (_error) {
        return null;
    }
}

interface APIItemSchemeProps {
    content: PropDocContent;
}

const APIItemScheme: React.FC<APIItemSchemeProps> = (props) => {
    const MDXComponent = props.content;
    const docHtmlClassName = `docs-doc-id-${props.content.metadata.id}`;

    const { frontMatter } = MDXComponent;
    const { sample } = frontMatter;

    return (
        <DocProvider content={props.content}>
            <HtmlClassNameProvider className={docHtmlClassName}>
                <DocItemMetadata />
                <DocItemLayout>
                    <div className={clsx("row", "theme-api-markdown")}>
                        <div className="col col--7 openapi-left-panel__container schema">
                            <MDXComponent />
                        </div>
                        <div className="col col--5 openapi-right-panel__container">
                            {sample ? (
                                <CodeBlock language="json" title={`${frontMatter.title}`}>
                                    {JSON.stringify(sample, null, 2)}
                                </CodeBlock>
                            ) : null}
                        </div>
                    </div>
                </DocItemLayout>
            </HtmlClassNameProvider>
        </DocProvider>
    );
};

interface APIItemAPIProps {
    content: PropDocContent;
    api: ApiItemType;
}

const APIItemAPI: React.FC<APIItemAPIProps> = ({ content: MDXComponent, api }) => {
    const docHtmlClassName = `docs-doc-id-${MDXComponent.metadata.id}`;

    const frontMatter = MDXComponent.frontMatter;

    const { siteConfig } = useDocusaurusContext();
    const themeConfig = siteConfig.themeConfig as ThemeConfig;
    const options = themeConfig.api;
    const isBrowser = useIsBrowser();

    // Regex for 2XX status
    const statusRegex = new RegExp("(20[0-9]|2[1-9][0-9])");

    let store: APIStore;
    const persistanceMiddleware = createPersistanceMiddleware(options);

    // Init store for SSR
    if (!isBrowser) {
        store = createStoreWithoutState({}, [persistanceMiddleware]);
    } else {
        // Init store for CSR to hydrate components
        // Create list of only 2XX response content types to create request samples from
        const acceptArrayInit: string[][] = [];
        for (const [code, content] of Object.entries(api.responses ?? [])) {
            if (statusRegex.test(code)) {
                acceptArrayInit.push(Object.keys(content.content ?? {}));
            }
        }
        const acceptArray = acceptArrayInit.flat();

        const content = api.requestBody?.content ?? {};
        const contentTypeArray = Object.keys(content);
        const servers = api.servers ?? [];
        const params = {
            path: [] as ParameterObject[],
            query: [] as ParameterObject[],
            header: [] as ParameterObject[],
            cookie: [] as ParameterObject[],
        };

        api.parameters?.forEach((param: { in: "path" | "query" | "header" | "cookie" }) => {
            const paramType = param.in;
            const paramsArray: ParameterObject[] = params[paramType];
            paramsArray.push(param as ParameterObject);
        });

        const auth = createAuth({
            security: api.security,
            securitySchemes: api.securitySchemes,
            options,
        });

        const server = window?.sessionStorage.getItem("server");
        const serverObject = (JSON.parse(server!) as ServerObject) ?? {};

        store = createStoreWithState(
            {
                accept: {
                    value: acceptArray[0],
                    options: acceptArray,
                },
                contentType: {
                    value: contentTypeArray[0],
                    options: contentTypeArray,
                },
                server: {
                    value: serverObject.url ? serverObject : undefined,
                    options: servers,
                },
                response: { value: undefined },
                body: { type: "empty" },
                params,
                auth,
            },
            [persistanceMiddleware],
        );
    }

    return (
        <DocProvider content={MDXComponent}>
            <HtmlClassNameProvider className={docHtmlClassName}>
                <DocItemMetadata />
                <DocItemLayout>
                    <Provider store={store}>
                        <div className={clsx("row", "theme-api-markdown")}>
                            <div className="col col--7 openapi-left-panel__container">
                                <MDXComponent />
                            </div>
                            <div className="col col--5 openapi-right-panel__container">
                                <BrowserOnly fallback={<SkeletonLoader size="lg" />}>
                                    {() => {
                                        return (
                                            <ApiExplorer
                                                item={api}
                                                infoPath={frontMatter.info_path}
                                            />
                                        );
                                    }}
                                </BrowserOnly>
                            </div>
                        </div>
                    </Provider>
                </DocItemLayout>
            </HtmlClassNameProvider>
        </DocProvider>
    );
};

interface APIItemProps {
    content: PropDocContent;
}

const ApiItem: React.FC<APIItemProps> = ({ content: MDXComponent }) => {
    const frontMatter = MDXComponent.frontMatter;

    if (frontMatter.schema) {
        return <APIItemScheme content={MDXComponent} />;
    }

    if (!MDXComponent.api) {
        // Non-API docs
        return (
            <DocProvider content={MDXComponent}>
                <HtmlClassNameProvider className={`docs-doc-id-${MDXComponent.metadata.id}`}>
                    <DocItemMetadata />
                    <DocItemLayout>
                        <div className="row">
                            <div className="col col--12 markdown">
                                <MDXComponent />
                            </div>
                        </div>
                    </DocItemLayout>
                </HtmlClassNameProvider>
            </DocProvider>
        );
    }

    return (
        <BrowserOnly fallback={<SkeletonLoader size="lg" />}>
            {() => {
                const api = decodeAPI(MDXComponent.api!);

                if (!api) {
                    console.error("Failed to decode API", frontMatter);
                    throw new Error("Failed to decode API");
                }

                return <APIItemAPI content={MDXComponent} api={api} />;
            }}
        </BrowserOnly>
    );
};

export default ApiItem;
