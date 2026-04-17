---
title: File picker values
authentik_version: "2025.12"
---

Many fields in the authentik Admin interface use the same file picker. You can use it to select an uploaded file, reference a built-in static asset, point at an external URL, or use a Font Awesome icon.

This applies to:

- **System** > **Brands** > **Logo**
- **System** > **Brands** > **Favicon**
- **System** > **Brands** > **Default flow background**
- **Flows and Stages** > **Flows** > **Background**
- **Applications** > **Applications** > **Icon**
- **Applications** > **New Application** wizard > **Icon**
- **Directory** > **Federation and Social login** > source **Icon** fields for SAML, OAuth, Plex, and Kerberos sources

## Accepted values

The file picker accepts the following value types.

| Value type            | Example                                         | Notes                                                                                                                                                                                                                         |
| --------------------- | ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Uploaded file path    | `branding/company-logo.svg`                     | Relative path to a file stored in authentik's media storage. You can upload these from **Customization** > **Files**. When authentik serves these files, it uses a short-lived protected URL rather than a fixed public path. |
| Built-in static asset | `/static/dist/assets/icons/icon_left_brand.svg` | Absolute path to a built-in asset shipped with authentik.                                                                                                                                                                     |
| External URL          | `https://cdn.example.com/branding/logo.svg`     | Useful when files are hosted outside authentik.                                                                                                                                                                               |
| Font Awesome icon     | `fa://fa-circle-user`                           | Supported for icon fields. This is not useful for background image fields.                                                                                                                                                    |

When you open the picker, authentik lists uploaded files and built-in static assets. You can also type a custom value directly into the field.

## Theme-aware values with `%(theme)s`

Some assets can change based on whether the active theme is light or dark. For those cases, you can use the placeholder `%(theme)s` in the path or URL.

Examples:

- `branding/logo-%(theme)s.svg`
- `branding/background-%(theme)s.jpg`
- `/static/dist/assets/icons/icon-%(theme)s.svg`
- `https://cdn.example.com/assets/logo-%(theme)s.svg`

authentik resolves `%(theme)s` to:

- `light`
- `dark`

`automatic` is not substituted directly. When a user is set to automatic theme selection, authentik chooses either the light or dark asset first and then uses the matching resolved URL.

This resolution happens on the backend, which means it also works with storage backends that need signed URLs, such as S3.

The `%(theme)s` placeholder is supported in all current Admin UI fields that use the shared file picker:

- Brand **Logo**
- Brand **Favicon**
- Brand **Default flow background**
- Flow **Background**
- Application **Icon**
- Source **Icon**

## Upload and path rules

When uploading a file in **Customization** > **Files**, or when typing a relative media path manually, use these rules:

- Files uploaded through **Customization** > **Files** are always served through a temporary protected URL
- On S3 storage, authentik generates a presigned S3 URL
- On local file storage, authentik generates an authentik `/files/...` URL with a unique signed token
- Uploaded files can be up to 25 MB each
- Allowed characters are letters, numbers, `.`, `_`, `-`, and `/`
- `%(theme)s` is also allowed anywhere in the path
- Paths must be relative, not absolute
- Parent directory references such as `..` are not allowed
- Duplicate slashes such as `//` are not allowed
- Paths cannot start with `.`
- The full path can be up to 1024 characters long
- Each path segment can be up to 255 characters long

Examples of valid upload names:

- `branding/logo.svg`
- `branding/logo-%(theme)s.svg`
- `sources/oauth/company-icon.png`

If you rename a file during upload, authentik keeps the original file extension.
