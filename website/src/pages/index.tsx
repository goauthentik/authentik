import { PluginOptions } from "@docusaurus/plugin-content-docs";
import { Options } from "@docusaurus/preset-classic";
import { Redirect } from "@docusaurus/router";
import { PresetConfigDefined } from "@docusaurus/types";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import React from "react";

function Home() {
    const { siteConfig } = useDocusaurusContext();
    const presets = siteConfig.presets as PresetConfigDefined[];
    const presetClassic = presets
        .filter((v) => {
            return !(v instanceof String);
        })
        .filter(([name, _]) => {
            return name === "@docusaurus/preset-classic";
        })
        .map(([_, config]) => {
            return config;
        });
    const presetConfig = presetClassic[0] as Options;
    const docsConfig = presetConfig.docs as PluginOptions;
    const presetURL = `/${docsConfig.routeBasePath}`;
    return <Redirect to={presetURL} />;
}

export default Home;
