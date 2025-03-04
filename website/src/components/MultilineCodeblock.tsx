import React, {
    ReactNode,
    useState,
    isValidElement,
    useCallback,
    useEffect,
    useRef,
} from "react";
import createDOMPurify from "dompurify";

type IntegrationsMultilineCodeblockProps = {
    children: ReactNode;
    className?: string;
};

type CopyButtonState = {
    isCopied: boolean;
    className: string;
};

// Configuration for allowed HTML tags in the sanitized output
const allowedTags = ["em", "code", "pre"];

/**
 * Initializes DOMPurify safely for both browser and server environments
 * @returns DOMPurify instance or null
 */
const getDOMPurify = () => {
    if (typeof window !== "undefined") {
        return createDOMPurify(window);
    }
    return null;
};

const domPurifyInstance = getDOMPurify();

/**
 * Component for rendering secure code blocks with copy functionality
 * - Safely sanitizes HTML content
 * - Handles both string and JSX content
 * - Provides copy-to-clipboard functionality
 */
const IntegrationsMultilineCodeblock: React.FC<
    IntegrationsMultilineCodeblockProps
> = ({ children, className = "" }) => {
    // State for managing copy button appearance and behavior
    const [copyState, setCopyState] = useState<CopyButtonState>({
        isCopied: false,
        className: "",
    });

    // State for storing sanitized content after processing
    const [sanitizedContent, setSanitizedContent] = useState<string | null>(
        null,
    );

    // Ref to access the actual DOM element for text extraction
    const codeRef = useRef<HTMLElement>(null);

    /**
     * Recursively converts React children to plain text string
     * @param nodes - React children nodes to process
     * @returns Flattened string representation
     */
    const childrenAsString = useCallback((nodes: ReactNode): string => {
        return React.Children.toArray(nodes).reduce<string>((acc, node) => {
            if (typeof node === "string") {
                return acc + node;
            } else if (isValidElement(node)) {
                return acc + childrenAsString(node.props.children);
            } else if (typeof node === "number") {
                return acc + String(node);
            }
            return acc;
        }, "");
    }, []);

    /**
     * Sanitizes content while preserving allowed HTML tags
     * @param children - React children to process
     * @returns Sanitized HTML string
     */
    const processContent = useCallback(
        (children: ReactNode): string => {
            const rawText = childrenAsString(children);

            // Client-side sanitization with DOMPurify
            if (domPurifyInstance) {
                return domPurifyInstance
                    .sanitize(rawText, {
                        ALLOWED_TAGS: allowedTags,
                        KEEP_CONTENT: true,
                        RETURN_TRUSTED_TYPE: false,
                    })
                    .trim();
            }

            // Server-side fallback (no sanitization, will be re-processed client-side)
            return rawText.trim();
        },
        [childrenAsString],
    );

    // Process content after component mounts to ensure browser environment
    useEffect(() => {
        setSanitizedContent(processContent(children));
    }, [children, processContent]);

    /**
     * Handles copy-to-clipboard functionality
     */
    const handleCopy = async (): Promise<void> => {
        // Get raw text content from DOM element, stripping all HTML tags
        const textToCopy = codeRef.current?.textContent || "";

        try {
            await navigator.clipboard.writeText(textToCopy);
            setCopyState({
                isCopied: true,
                className: "integration-codeblock__copy-btn--copied",
            });
            setTimeout(() => {
                setCopyState((prev) =>
                    prev.isCopied ? { isCopied: false, className: "" } : prev,
                );
            }, 2000);
        } catch (error) {
            console.error("Failed to copy content:", error);
        }
    };

    // SVG icon component for copy buttons
    const Icon: React.FC<{ className: string; path: string }> = React.memo(
        ({ className, path }) => (
            <svg viewBox="0 0 24 24" className={className}>
                <path fill="currentColor" d={path} />
            </svg>
        ),
    );

    return (
        <pre className={`integration-codeblock ${className}`.trim()}>
            {/* Attach ref to access rendered text content */}
            <code className="integration-codeblock__content" ref={codeRef}>
                {typeof children === "string" ? (
                    // Render sanitized HTML for string content
                    <span
                        dangerouslySetInnerHTML={{
                            __html: sanitizedContent || children,
                        }}
                    />
                ) : (
                    // Directly render JSX children (already safe)
                    children
                )}
            </code>

            {/* Copy button with state-dependent styling */}
            <button
                onClick={handleCopy}
                className={`integration-codeblock__copy-btn ${copyState.className}`.trim()}
                aria-label="Copy code to clipboard"
                title="Copy"
                type="button"
                disabled={copyState.isCopied}
            >
                <span
                    className="integration-codeblock__copy-icons"
                    aria-hidden="true"
                >
                    {/* Copy icon */}
                    <Icon
                        className="integration-codeblock__copy-icon"
                        path="M19,21H8V7H19M19,5H8A2,2 0 0,0 6,7V21A2,2 0 0,0 8,23H19A2,2 0 0,0 21,21V7A2,2 0 0,0 19,5M16,1H4A2,2 0 0,0 2,3V17H4V3H16V1Z"
                    />
                    {/* Success checkmark */}
                    <Icon
                        className="integration-codeblock__copy-success-icon"
                        path="M21,7L9,19L3.5,13.5L4.91,12.09L9,16.17L19.59,5.59L21,7Z"
                    />
                </span>
            </button>
        </pre>
    );
};

export default IntegrationsMultilineCodeblock;
