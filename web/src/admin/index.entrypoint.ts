import "#elements/messages/MessageContainer";
import "#elements/router/RouterOutlet";
import "#elements/commands/ak-command-palette-user-modal";
import "#admin/AdminInterface/ak-interface-admin";

if (process.env.NODE_ENV === "development") {
    await import("@goauthentik/esbuild-plugin-live-reload");
}
