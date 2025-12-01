/**
 * File utilities and shared types for file management
 */

/**
 * File item as returned by the API (authentik/admin/files/api.py).
 */
export interface FileItem {
    name: string;
    url: string;
    mime_type: string;
}

/**
 * Render function for displaying file names in dropdowns/lists
 */
export const renderFileElement = (item: FileItem) => item.name;

/**
 * Render function for displaying selected file value
 */
export const renderFileValue = (item: FileItem | undefined) => item?.name;
