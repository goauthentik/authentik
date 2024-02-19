import { msg } from "@lit/localize";

// These two strings are (a) longer than 80 characters, and (b) contain interesting punctuation, and (c) are used in
// multiple locations. They've been extracted to ensure consistency.

export const iconHelperText = msg(
    "Either input a full URL, a relative path, or use 'fa://fa-test' to use the Font Awesome icon \"fa-test\".",
);

export const placeholderHelperText = msg(
    "Path template for users created. Use placeholders like `%(slug)s` to insert the source slug.",
);
