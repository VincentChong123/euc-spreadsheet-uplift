/**
 * Top-level Error Handler Middleware.
 *
 * Express recognises this as an error handler because it has 4 parameters.
 * Mount it AFTER all routes and proxies so it catches:
 *   - Uncaught throws in any middleware
 *   - Rejected promises in async handlers (Express 5+ or with express-async-errors)
 *   - next(err) calls from any layer
 *
 * Returns a consistent JSON envelope that Apps Script can reliably parse.
 */
import { logger } from '../utils/logger.mjs';

// eslint-disable-next-line no-unused-vars -- Express requires all 4 params
export function errorHandler(err, req, res, _next) {
    const request_id = req.id || 'unknown';
    const statusCode = err.statusCode || err.status || 500;

    logger.error(
        { err, request_id, method: req.method, path: req.originalUrl, statusCode },
        `[Gateway] Unhandled error`
    );

    // Prevent double-sending if headers were already flushed (e.g. mid-stream proxy failure)
    if (res.headersSent) {
        return;
    }

    res.status(statusCode).json({
        error: err.message || 'Internal Gateway Error',
        request_id
    });
}
