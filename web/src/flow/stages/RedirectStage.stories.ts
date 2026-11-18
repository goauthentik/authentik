import "@patternfly/patternfly/components/Login/login.css";
import { RedirectStage } from "#flow/stages/RedirectStage";

import { flowFactory } from "#stories/flow-interface";

export default {
    title: "Flow / Stages / <ak-stage-redirect>",
};

/**
 * The stage navigates the window as soon as it renders, which would take the Storybook iframe
 * with it. Stub navigation for the duration of each story, and optionally force the "inspector
 * is open" prompt, which otherwise requires loading the real flow inspector and its API calls.
 */
function stubRedirect(promptUser = false) {
    return () => {
        const proto = RedirectStage.prototype;
        const navigate = Object.getOwnPropertyDescriptor(proto, "navigate")!;
        const prompt = Object.getOwnPropertyDescriptor(proto, "promptUser")!;

        proto.navigate = (to: string) => console.debug("Storybook: suppressed navigation to", to);
        Object.defineProperty(proto, "promptUser", { configurable: true, get: () => promptUser });

        return () => {
            Object.defineProperty(proto, "navigate", navigate);
            Object.defineProperty(proto, "promptUser", prompt);
        };
    };
}

// What a user sees with the flow inspector open: the redirect waits for confirmation.
export const PromptUser = flowFactory(
    "xak-flow-redirect",
    { to: "https://sp.example.com/acs?SAMLResponse=response" },
    { beforeEach: stubRedirect(true) },
);

// The default: redirect immediately and show a spinner while the browser leaves.
export const Redirecting = flowFactory(
    "xak-flow-redirect",
    { to: "https://sp.example.com/acs?SAMLResponse=response" },
    { beforeEach: stubRedirect() },
);

// A non-HTTP target is handed off to an OS-level handler, so the page can be closed.
export const CustomProtocol = flowFactory(
    "xak-flow-redirect",
    { to: "myapp://callback?code=abc123" },
    { beforeEach: stubRedirect() },
);
