import React from "react";
import Layout from "@theme/Layout";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import useBaseUrl from "@docusaurus/useBaseUrl";
import BrowserOnly from "@docusaurus/core/lib/client/exports/BrowserOnly";

function APIBrowser() {
    const context = useDocusaurusContext();
    const { siteConfig = {} } = context;
    return (
        <Layout title="API Browser" description={siteConfig.tagline}>
            <BrowserOnly>
                {() => {
                    import("rapidoc");
                    return (
                        <rapi-doc
                            spec-url={useBaseUrl("schema.yaml")}
                            allow-try="false"
                            show-header="false"
                            theme="dark"
                            render-style="view"
                            primary-color="#fd4b2d"
                            allow-spec-url-load="false"
                            allow-spec-file-load="false"
                        ></rapi-doc>
                    );
                }}
            </BrowserOnly>
        </Layout>
    );
}

export default APIBrowser;
