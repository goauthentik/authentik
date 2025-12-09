import OriginalTabs from "@theme-original/Tabs";
import React from "react";

export interface Props extends React.ComponentProps<typeof OriginalTabs> {
    automaticallyDetectPlatform?: boolean;
}

function detectOS(): string {
    console.log("[Tabs Debug] detectOS() called");
    
    if (typeof window === "undefined") {
        console.log("[Tabs Debug] window is undefined, returning 'unknown'");
        return "unknown";
    }

    try {
        const userAgent = window.navigator.userAgent.toLowerCase();
        console.log("[Tabs Debug] userAgent:", userAgent);
        if (
            userAgent.includes("mac") ||
            userAgent.includes("iphone") ||
            userAgent.includes("ipad")
        ) {
            console.log("[Tabs Debug] Detected macOS");
            return "macos";
        }
        if (userAgent.includes("win")) {
            console.log("[Tabs Debug] Detected Windows");
            return "windows";
        }
        if (userAgent.includes("android")) {
            console.log("[Tabs Debug] Detected Android");
            return "android";
        }
        if (userAgent.includes("linux")) {
            console.log("[Tabs Debug] Detected Linux");
            return "linux";
        }

        console.log("[Tabs Debug] No OS detected, returning 'unknown'");
        return "unknown";
    } catch (error) {
        console.error("[Tabs Debug] Error in detectOS:", error);
        return "unknown";
    }
}

const CustomTabs = React.memo(function CustomTabs(props: Props): React.JSX.Element {
    console.log("[Tabs Debug] CustomTabs component rendered with props:", props);
    
    const { automaticallyDetectPlatform, ...tabsProps } = props;
    console.log("[Tabs Debug] automaticallyDetectPlatform:", automaticallyDetectPlatform);
    console.log("[Tabs Debug] tabsProps:", tabsProps);

    React.useEffect(() => {
        if (automaticallyDetectPlatform) {
            console.log("[Tabs Debug] About to call detectOS() in useEffect");
            const detectedOS = detectOS();
            console.log("[Tabs Debug] Detected OS:", detectedOS);
        }
    }, [automaticallyDetectPlatform]);

    console.log("[Tabs Debug] About to render original Tabs component");
    return <OriginalTabs {...tabsProps} />;
});

export default CustomTabs;
