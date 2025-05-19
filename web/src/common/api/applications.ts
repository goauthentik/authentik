import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";

import { CoreApi } from "@goauthentik/api";

/**
 * Response from icon upload/update operations
 */
export interface IconResponse {
    meta_icon?: string;
    message?: string;
    operation?: string;
    error?: string;
}

/**
 * Error type for API errors
 */
export interface ApiError {
    response?: {
        data?: {
            error?: string;
        };
    };
    message?: string;
}

/**
 * Helper function to handle common error patterns
 *
 * @param error Error object from catch block
 * @returns Standardized error response
 */
function handleApiError(error: ApiError): IconResponse {
    if (error.response?.data?.error) {
        return { error: error.response.data.error };
    }
    if (error.message) {
        return { error: error.message };
    }
    return { error: "An unknown error occurred" };
}

/**
 * Set application icon using a file upload
 *
 * @param slug Application slug
 * @param file File to upload
 * @param retryCount Optional retry count for network issues
 * @returns Promise with the icon URL or error
 */
export async function setApplicationIcon(
    slug: string,
    file: File,
    retryCount = 1,
): Promise<IconResponse> {
    const api = new CoreApi(DEFAULT_CONFIG);

    try {
        const formData = new FormData();
        formData.append("file", file);

        const result = await api.coreApplicationsIconCreate({
            slug: slug,
            file: file,
        }) as unknown as IconResponse;

        if (!result.meta_icon) {
            return { error: "Server did not return a valid icon URL" };
        }

        // Accept Font Awesome icons or any URL (including S3 signed URLs)
        if (!result.meta_icon.startsWith('fa://')) {
            // For S3 URLs, we don't validate the URL format since they contain signing parameters
            if (result.meta_icon.includes('AWSAccessKeyId=') || result.meta_icon.includes('X-Amz-Signature=')) {
                return result;
            }
            // For other URLs, validate the format
            try {
                new URL(result.meta_icon);
            } catch {
                return { error: "Server returned an invalid icon URL format" };
            }
        }

        return result;
    } catch (error: unknown) {
        // Handle network errors with retry
        const apiError = error as ApiError;
        if (retryCount > 0 && apiError.message?.includes("network")) {
            return setApplicationIcon(slug, file, retryCount - 1);
        }
        return handleApiError(apiError);
    }
}

/**
 * Modify application icon using a file upload
 *
 * @param slug Application slug
 * @param file File to upload
 * @param retryCount Optional retry count for network issues
 * @returns Promise with the icon URL or error
 */
export async function modifyApplicationIcon(
    slug: string,
    file: File,
    retryCount = 1,
): Promise<IconResponse> {
    const api = new CoreApi(DEFAULT_CONFIG);

    try {
        const result = await api.coreApplicationsIconPartialUpdate({
            slug: slug,
            file: file,
        }) as unknown as IconResponse;
        return result;
    } catch (error: unknown) {
        // Handle network errors with retry
        const apiError = error as ApiError;
        if (retryCount > 0 && apiError.message?.includes("network")) {
            return modifyApplicationIcon(slug, file, retryCount - 1);
        }
        return handleApiError(apiError);
    }
}

/**
 * Remove application icon
 *
 * @param slug Application slug
 * @param retryCount Optional retry count for network issues
 * @returns Promise with operation result
 */
export async function removeApplicationIcon(slug: string, retryCount = 1): Promise<IconResponse> {
    const api = new CoreApi(DEFAULT_CONFIG);

    try {
        const result = await api.coreApplicationsIconDestroy({
            slug: slug,
        }) as unknown as IconResponse;
        return result;
    } catch (error: unknown) {
        // Handle network errors with retry
        const apiError = error as ApiError;
        if (retryCount > 0 && apiError.message?.includes("network")) {
            return removeApplicationIcon(slug, retryCount - 1);
        }
        return handleApiError(apiError);
    }
}

/**
 * Set application icon using a URL
 *
 * @param slug Application slug
 * @param url URL to use as icon
 * @param retryCount Optional retry count for network issues
 * @returns Promise with the icon URL or error
 */
export async function setApplicationIconUrl(
    slug: string,
    url: string,
    retryCount = 1,
): Promise<IconResponse> {
    const api = new CoreApi(DEFAULT_CONFIG);

    try {
        // Accept Font Awesome icons, S3 signed URLs, or any valid URL format
        if (!url.startsWith('fa://')) {
            // For S3 URLs, we don't validate the URL format since they contain signing parameters
            if (url.includes('AWSAccessKeyId=') || url.includes('X-Amz-Signature=')) {
                // Pass through S3 URLs without validation
            } else {
                // For other URLs, validate the format
                try {
                    new URL(url);
                } catch (_error) {
                    return { error: "Invalid URL format" };
                }
            }
        }

        const result = await api.coreApplicationsIconPartialUpdate({
            slug: slug,
            url: url,
        }) as unknown as IconResponse;

        if (!result.meta_icon) {
            return { error: "Server did not return a valid icon URL" };
        }

        // Accept Font Awesome icons, S3 signed URLs, or any valid URL format
        if (!result.meta_icon.startsWith('fa://')) {
            // For S3 URLs, we don't validate the URL format since they contain signing parameters
            if (result.meta_icon.includes('AWSAccessKeyId=') || result.meta_icon.includes('X-Amz-Signature=')) {
                return result;
            }
            // For other URLs, validate the format
            try {
                new URL(result.meta_icon);
            } catch {
                return { error: "Server returned an invalid icon URL format" };
            }
        }

        return result;
    } catch (error: unknown) {
        // Handle network errors with retry
        const apiError = error as ApiError;
        if (retryCount > 0 && apiError.message?.includes("network")) {
            return setApplicationIconUrl(slug, url, retryCount - 1);
        }
        return handleApiError(apiError);
    }
}

/**
 * Modify application icon using a URL
 *
 * @param slug Application slug
 * @param url URL to use as icon
 * @param retryCount Optional retry count for network issues
 * @returns Promise with the icon URL or error
 */
export async function modifyApplicationIconUrl(
    slug: string,
    url: string,
    retryCount = 1,
): Promise<IconResponse> {
    const api = new CoreApi(DEFAULT_CONFIG);

    try {
        // Validate URL format before sending
        try {
            new URL(url);
        } catch (_error) {
            return { error: "Invalid URL format" };
        }

        const result = await api.coreApplicationsIconPartialUpdate({
            slug: slug,
            url: url,
        }) as unknown as IconResponse;
        return result;
    } catch (error: unknown) {
        // Handle network errors with retry
        const apiError = error as ApiError;
        if (retryCount > 0 && apiError.message?.includes("network")) {
            return modifyApplicationIconUrl(slug, url, retryCount - 1);
        }
        return handleApiError(apiError);
    }
}
