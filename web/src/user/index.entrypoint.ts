import "#elements/messages/MessageContainer";
import "#user/ak-interface-user";

if (process.env.NODE_ENV === "development") {
    await import("@goauthentik/esbuild-plugin-live-reload");
}
