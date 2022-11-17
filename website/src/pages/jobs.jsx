import React from "react";
import Layout from "@theme/Layout";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import { useEffect } from "react";
import { useColorMode } from "@docusaurus/theme-common";

const useScript = (url, selector = "body", async = true) => {
    useEffect(() => {
        const element = document.querySelector(selector);
        const script = document.createElement("script");
        script.src = url;
        script.async = async;
        element.appendChild(script);
        return () => {
            element.removeChild(script);
        };
    }, [url]);
};

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
    useScript(
        "https://boards.greenhouse.io/embed/job_board/js?for=authentiksecurity"
    );
    const { colorMode, setColorMode } = useColorMode();
    if (colorMode !== "light") {
        setColorMode("light");
    }
    return <div id="grnhse_app"></div>;
}

export default JobBoardWrapper;
