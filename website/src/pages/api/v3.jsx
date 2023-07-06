import React from "react";
import Layout from "@theme/Layout";
import Head from "@docusaurus/Head";
import BrowserOnly from "@docusaurus/core/lib/client/exports/BrowserOnly";

function APIPage() {
    return (
        <Layout title="API">
            <Head>
                <meta
                    name="go-import"
                    content="goauthentik.io/api/v3 git https://github.com/goauthentik/client-go"
                ></meta>
            </Head>
            <BrowserOnly>
                {() => {
                    window.location.pathname = "/developer-docs/api/";
                }}
            </BrowserOnly>
        </Layout>
    );
}
export default APIPage;
