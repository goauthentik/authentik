import { msg } from "@lit/localize";

// These two strings are (a) longer than 80 characters, and (b) contain interesting punctuation, and (c) are used in
// multiple locations. They've been extracted to ensure consistency.

export const iconHelperText = msg(
    "Select from uploaded files, type a URL, or use a Font Awesome icon like fa://fa-key, fa://fa-shield-halved, or fa://brands/fa-github. Pro families (light, thin, duotone, sharp-solid) work if FA Pro CSS is loaded via custom branding.",
);

export const placeholderHelperText = msg(
    "Path template for users created. Use placeholders like `%(slug)s` to insert the source slug.",
);
