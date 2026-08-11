import "#elements/messages/MessageContainer";
import "#user/ak-interface-user";

import { globalAK } from "#common/global";

import { initRouter } from "#elements/router/core/config";

// Static imports above run first, but `<ak-router-view>` is only created during
// the interface's first (asynchronously scheduled) render — so this module-body
// call configures the router before the outlet ever reads the config.
initRouter({
    base: globalAK().api.relBase,
    interfaceName: "user",
});

if (process.env.NODE_ENV === "development") {
    await import("@goauthentik/esbuild-plugin-live-reload");
}
