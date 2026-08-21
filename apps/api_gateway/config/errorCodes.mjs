/**
 * Shared error registry — single source of truth for the gateway.
 *
 * Mirror of docs/03_Reference/error_code_spec.md. Source code MUST reference an error_key
 * (not a bare HTTP number); `statusFor()` resolves the number.
 *
 * Directionality:
 *   error_key -> http_status   deterministic (statusFor)
 *   http_status -> error_key   one-to-many  (keysForStatus)  — the precise key
 *                                            travels in the response body.
 *
 * When editing, update docs/03_Reference/error_code_spec.md and app/errors.py identically.
 */

// Canonical registry: error_key -> { status, retryable, description }.
export const ERROR_REGISTRY = Object.freeze({
    // -- Client errors (4xx) --
    __ERROR_BAD_REQUEST__:            { status: 400, retryable: false, description: 'Malformed request or envelope mismatch' },
    __ERROR_UNAUTHENTICATED__:        { status: 401, retryable: false, description: 'Missing or invalid credentials' },
    __ERROR_FORBIDDEN__:              { status: 403, retryable: false, description: 'Authenticated but not permitted' },
    __ERROR_NOT_FOUND__:              { status: 404, retryable: false, description: 'Route or resource does not exist' },
    __ERROR_PAYLOAD_TOO_LARGE__:      { status: 413, retryable: false, description: 'Body exceeds the configured size limit' },
    __ERROR_VALIDATION__:             { status: 422, retryable: false, description: 'Well-formed but semantically invalid' },
    __ERROR_RATE_LIMIT__:             { status: 429, retryable: true,  description: 'Too many requests' },

    // -- MFA / step-up (second factor; see docs/01_Architecture/specs/totp_mfa_spec.md) --
    __ERROR_OTP_REQUIRED__:           { status: 401, retryable: false, description: 'Sensitive action needs a second factor; none supplied' },
    __ERROR_OTP_INVALID__:            { status: 401, retryable: false, description: 'Submitted TOTP code is wrong' },
    __ERROR_OTP_EXPIRED__:            { status: 401, retryable: false, description: 'TOTP code outside the accepted time window' },
    __ERROR_OTP_NOT_ENROLLED__:       { status: 403, retryable: false, description: 'User has no confirmed TOTP secret' },

    // -- Server / gateway errors (5xx) --
    __ERROR_INTERNAL__:               { status: 500, retryable: false, description: 'Unhandled gateway error' },
    __ERROR_NOT_IMPLEMENTED__:        { status: 501, retryable: false, description: 'Endpoint not implemented' },
    __ERROR_UPSTREAM_FAILURE__:       { status: 502, retryable: true,  description: 'Upstream unreachable or returned an error' },
    __ERROR_UPSTREAM_INVALID_RESPONSE__: { status: 502, retryable: false, description: 'Upstream returned non-JSON / unparseable body' },
    __ERROR_AUTH_UNAVAILABLE__:       { status: 502, retryable: true,  description: 'Could not mint an upstream credential' },
    __ERROR_SERVICE_UNAVAILABLE__:    { status: 503, retryable: true,  description: 'Not ready / a dependency is down' },
    __ERROR_UPSTREAM_TIMEOUT__:       { status: 504, retryable: true,  description: 'Upstream did not respond within the timeout' },
});

// Convenience: ERROR_KEYS.UPSTREAM_TIMEOUT === '__ERROR_UPSTREAM_TIMEOUT__'.
// Lets call sites use short names while the value stays the full sentinel.
export const ERROR_KEYS = Object.freeze(
    Object.fromEntries(
        Object.keys(ERROR_REGISTRY).map((k) => [k.replace(/^__ERROR_|__$/g, ''), k]),
    ),
);

/** error_key -> http_status (throws on unknown key to catch typos early). */
export function statusFor(errorKey) {
    const entry = ERROR_REGISTRY[errorKey];
    if (!entry) {
        throw new Error(`Unknown error_key '${errorKey}' — add it to errorCodes.mjs / error_code_spec.md`);
    }
    return entry.status;
}

/** error_key -> retryable flag. */
export function isRetryable(errorKey) {
    return Boolean(ERROR_REGISTRY[errorKey]?.retryable);
}

/** http_status -> [error_key, …] (one-to-many; disambiguate via body.error_key). */
export function keysForStatus(httpStatus) {
    return Object.entries(ERROR_REGISTRY)
        .filter(([, v]) => v.status === httpStatus)
        .map(([k]) => k);
}
