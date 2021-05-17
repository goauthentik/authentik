import React from "react";
import Layout from "@theme/Layout";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import useBaseUrl from "@docusaurus/useBaseUrl";

function APIBrowser() {
    const context = useDocusaurusContext();
    const { siteConfig = {} } = context;
    import('rapidoc');
    return (
        <Layout title="API Browser" description={siteConfig.tagline}>
            <rapi-doc
                spec-url={useBaseUrl("schema.yml")}
                allow-try="false"
                show-header="false"
                theme="dark"
                render-style="view"
                primary-color="#fd4b2d"
                allow-spec-url-load="false"
                allow-spec-file-load="false">
            </rapi-doc>
        </Layout>
    );
}

export default APIBrowser;
