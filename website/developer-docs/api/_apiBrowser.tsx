import React from "react";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import useBaseUrl from "@docusaurus/useBaseUrl";
import BrowserOnly from "@docusaurus/BrowserOnly";
import { useColorMode } from "@docusaurus/theme-common";

export function APIBrowser() {
    const context = useDocusaurusContext();
    const { siteConfig = {} } = context;
    const { colorMode, setColorMode } = useColorMode();
    let bg = "#1b1b1d";
    if (colorMode === "light") {
        bg = "#fff";
    }
    return (
        <BrowserOnly>
            {() => {
                require("rapidoc");
                return (
                    <rapi-doc
                        spec-url={useBaseUrl("schema.yaml")}
                        allow-try="false"
                        show-header="false"
                        theme={colorMode}
                        bg-color={bg}
                        render-style="view"
                        primary-color="#fd4b2d"
                        allow-spec-url-load="false"
                        allow-spec-file-load="false"
                        allow-authentication="false"
                        allow-server-selection="false"
                        show-info="false"
                    ></rapi-doc>
                );
            }}
        </BrowserOnly>
    );
}

export default APIBrowser;
