/**
 * Request ID Middleware.
 *
 * Assigns a unique X-Request-ID to every inbound request.
 * If the caller (e.g. Apps Script) already sends one, it is preserved.
 * The ID is:
 *   1. Attached to req.id for use by downstream middleware and loggers
 *   2. Set as a response header so Apps Script can store it in __Prompt_records
 *   3. Forwarded to upstream services via onProxyReq (configured in server.mjs)
 */
import { randomUUID } from 'crypto';

export function requestId(req, res, next) {
    const id = req.headers['x-request-id'] || randomUUID();
    req.id = id;
    res.setHeader('X-Request-ID', id);
    next();
}
