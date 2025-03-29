import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { CoreApi } from "@goauthentik/api";
import { MessageLevel } from "@goauthentik/common/messages";
import { showMessage } from "@goauthentik/elements/messages/MessageContainer";

/**
 * Set application icon using a file upload
 * 
 * @param slug Application slug
 * @param file File to upload
 */
export async function setApplicationIcon(slug: string, file: File): Promise<void> {
    const formData = new FormData();
    formData.append("file", file);
    
    try {
        const xhr = new XMLHttpRequest();
        xhr.open("POST", `${DEFAULT_CONFIG.basePath}/core/applications/${slug}/set_icon/`);
        
        const csrfToken = document.cookie.split('; ')
            .find(row => row.startsWith('authentik_csrf='))
            ?.split('=')[1];
        if (csrfToken) {
            xhr.setRequestHeader("X-authentik-CSRF", csrfToken);
        }
        
        xhr.withCredentials = true;
        
        await new Promise<void>((resolve, reject) => {
            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve();
                } else {
                    try {
                        const errorData = JSON.parse(xhr.responseText);
                        reject(new Error(errorData.error || `Failed with status ${xhr.status}`));
                    } catch (e) {
                        reject(new Error(`Failed with status ${xhr.status}`));
                    }
                }
            };
            xhr.onerror = () => reject(new Error("Network error while uploading file"));
            xhr.send(formData);
        });
    } catch (error) {
        const err = error as Error;
        showMessage({
            level: MessageLevel.error,
            message: err.message || "Failed to upload icon",
        });
        throw error;
    }
}

/**
 * Clear application icon
 * 
 * @param slug Application slug
 */
export async function clearApplicationIcon(slug: string): Promise<void> {
    const formData = new FormData();
    formData.append("clear", "true");
    
    try {
        const xhr = new XMLHttpRequest();
        xhr.open("POST", `${DEFAULT_CONFIG.basePath}/core/applications/${slug}/set_icon/`);
        
        const csrfToken = document.cookie.split('; ')
            .find(row => row.startsWith('authentik_csrf='))
            ?.split('=')[1];
        if (csrfToken) {
            xhr.setRequestHeader("X-authentik-CSRF", csrfToken);
        }
        
        xhr.withCredentials = true;
        
        await new Promise<void>((resolve, reject) => {
            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve();
                } else {
                    try {
                        const errorData = JSON.parse(xhr.responseText);
                        reject(new Error(errorData.error || `Failed with status ${xhr.status}`));
                    } catch (e) {
                        reject(new Error(`Failed with status ${xhr.status}`));
                    }
                }
            };
            xhr.onerror = () => reject(new Error("Network error while clearing icon"));
            xhr.send(formData);
        });
    } catch (error) {
        const err = error as Error;
        showMessage({
            level: MessageLevel.error,
            message: err.message || "Failed to clear icon",
        });
        throw error;
    }
}

/**
 * Set application icon using a URL
 * 
 * @param slug Application slug
 * @param url URL to use as icon
 */
export async function setApplicationIconUrl(slug: string, url: string): Promise<void> {
    try {
        const api = new CoreApi(DEFAULT_CONFIG);
        
        const xhr = new XMLHttpRequest();
        xhr.open("POST", `${DEFAULT_CONFIG.basePath}/core/applications/${slug}/set_icon_url/`);
        
        const csrfToken = document.cookie.split('; ')
            .find(row => row.startsWith('authentik_csrf='))
            ?.split('=')[1];
        if (csrfToken) {
            xhr.setRequestHeader("X-authentik-CSRF", csrfToken);
        }
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.withCredentials = true;
        
        await new Promise<void>((resolve, reject) => {
            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve();
                } else {
                    try {
                        const errorData = JSON.parse(xhr.responseText);
                        reject(new Error(errorData.error || `Failed with status ${xhr.status}`));
                    } catch (e) {
                        reject(new Error(`Failed with status ${xhr.status}`));
                    }
                }
            };
            xhr.onerror = () => reject(new Error("Network error while setting icon URL"));
            xhr.send(JSON.stringify({ url }));
        });
    } catch (error) {
        const err = error as Error;
        showMessage({
            level: MessageLevel.error,
            message: err.message || "Failed to set icon URL",
        });
        throw error;
    }
} 