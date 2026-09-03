import "#common/sentry/apply";
import "#elements/messages/MessageContainer";
import "#admin/ak-interface-admin";

import { globalAK } from "#common/global";

import { initRouter } from "#elements/router/core/config";

initRouter({
    base: globalAK().api.relBase,
    interfaceName: "admin",
});

if (process.env.NODE_ENV === "development") {
    await import("@goauthentik/esbuild-plugin-live-reload");
}
