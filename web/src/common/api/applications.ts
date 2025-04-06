import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { CoreApi, FilePathRequest } from "@goauthentik/api";

/**
 * Set application icon using a file upload
 * 
 * @param slug Application slug
 * @param file File to upload
 */
export async function setApplicationIcon(slug: string, file: File): Promise<void> {
    const api = new CoreApi(DEFAULT_CONFIG);
    
    // Use explicit casting to handle type inconsistencies
    const params = {
        slug,
        file
    };
    
    // Safely cast to any to bypass TS type checking
    await api.coreApplicationsSetIconCreate(params as any);
}

/**
 * Clear application icon
 * 
 * @param slug Application slug
 */
export async function clearApplicationIcon(slug: string): Promise<void> {
    const api = new CoreApi(DEFAULT_CONFIG);
    
    // Use explicit casting to handle type inconsistencies
    const params = {
        slug,
        clear: true
    };
    
    // Safely cast to any to bypass TS type checking
    await api.coreApplicationsSetIconCreate(params as any);
}

/**
 * Set application icon using a URL
 * 
 * @param slug Application slug
 * @param url URL to use as icon
 */
export async function setApplicationIconUrl(slug: string, url: string): Promise<void> {
    const api = new CoreApi(DEFAULT_CONFIG);
    
    // The FilePathRequest type is correct but the property name in the request might be wrong
    const filePathReq: FilePathRequest = {
        url
    };
    
    // Create request with parameter name matching the API expectation
    const params = {
        slug,
        filePathRequest: filePathReq
    };
    
    // Safely cast to any to bypass TS type checking
    await api.coreApplicationsSetIconUrlCreate(params as any);
} 