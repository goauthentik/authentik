import React from "react";
import Layout from "@theme/Layout";
import Head from "@docusaurus/Head";
import BrowserOnly from "@docusaurus/core/lib/client/exports/BrowserOnly";

function TerraformProviderPage() {
    return (
        <Layout title="terraform-provider">
            <Head>
                <meta
                    name="go-import"
                    content="goauthentik.io/terraform-provider-authentik git https://github.com/goauthentik/terraform-provider-authentik"
                ></meta>
            </Head>
            <BrowserOnly>
                {() => {
                    window.location.assign(
                        "https://registry.terraform.io/providers/goauthentik/authentik/latest/docs"
                    );
                }}
            </BrowserOnly>
        </Layout>
    );
}
export default TerraformProviderPage;
