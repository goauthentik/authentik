import React from "react";
import clsx from "clsx";
import Layout from "@theme/Layout";
import BrowserOnly from "@docusaurus/BrowserOnly";

function Home() {
    return (
        <Layout title={`authentik Documentation`}>
            <BrowserOnly>
                {() => {
                    window.location.href = "/docs";
                }}
            </BrowserOnly>
            <header className={clsx("hero hero--primary")}>
                <div className="container">
                    <h1 className="hero__title">authentik Documentation</h1>
                </div>
            </header>
        </Layout>
    );
}

export default Home;
