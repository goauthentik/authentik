import "#elements/messages/MessageContainer";
import "#admin/AdminInterface/ak-interface-admin";

if (process.env.NODE_ENV === "development") {
    await import("@goauthentik/esbuild-plugin-live-reload");
}
