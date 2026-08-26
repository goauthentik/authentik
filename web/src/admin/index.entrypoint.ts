import "#common/sentry/apply";
import "#elements/messages/MessageContainer";
import "#admin/ak-interface-admin";

if (process.env.NODE_ENV === "development") {
    await import("@goauthentik/esbuild-plugin-live-reload");
}
