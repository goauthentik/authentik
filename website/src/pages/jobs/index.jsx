import React from "react";
import Layout from "@theme/Layout";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import { useColorMode } from "@docusaurus/theme-common";
import { useEffect } from "react";

function JobBoardWrapper() {
    const context = useDocusaurusContext();
    const { siteConfig = {} } = context;
    return (
        <Layout title="Jobs" description={siteConfig.tagline}>
            <JobBoard />
        </Layout>
    );
}

function JobBoard() {
    const { colorMode, setColorMode } = useColorMode();
    if (colorMode !== "light") {
        setColorMode("light");
    }
    useEffect(() => {
        Grnhse.Iframe.load();
    }, []);
    return <div id="grnhse_app"></div>;
}

export default JobBoardWrapper;
