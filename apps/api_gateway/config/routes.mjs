/**
 * Declarative Route Manifest for the API Gateway.
 *
 * To add a new backend service, append an entry to PROXY_ROUTES.
 * The gateway loop in server.mjs will automatically register the proxy
 * and wire up health checks — no handwritten Express code needed.
 *
 * Fields:
 *   pathPrefix   - The public URL prefix exposed to Google Sheets (e.g. "/api/ai")
 *   target       - The internal Docker/network URL of the upstream service
 *   stripPrefix  - If true, strips pathPrefix before forwarding (e.g. /api/ai/v1/chat -> /v1/chat)
 *   healthPath   - The upstream health endpoint used by /readyz and startup probes
 *   description  - Human-readable label for logs and /readyz output
 *   isActive     - Controls whether the route is registered. Driven by env var;
 *                  defaults to true so all services are on unless explicitly disabled.
 */

export const PROXY_ROUTES = [
    {
        pathPrefix: '/api/ai',
        target: process.env.AI_SERVICE_URL || (process.env.IS_DEV === 'true' ? 'http://host.docker.internal:8080' : 'http://ai-service:8080'),
        stripPrefix: true,
        healthPath: '/healthz',
        description: 'AI / LLM Service (Python FastAPI)',
        isActive: process.env.IS_AI_SERVICE_ACTIVE !== 'false',
    },
    {
        pathPrefix: '/api/workflow',
        target: process.env.DOC_SERVICE_URL || 'http://localhost:4000',
        stripPrefix: true,
        healthPath: '/readyz',
        description: 'Document / Approval Workflow Service (Node.js)',
        isActive: process.env.IS_DOC_SERVICE_ACTIVE !== 'false',
    },
    // Uncomment when the Agent Controller service is deployed:
    // {
    //     pathPrefix: '/api/agent',
    //     target: process.env.AGENT_SERVICE_URL || 'http://localhost:9000',
    //     stripPrefix: true,
    //     healthPath: '/healthz',
    //     description: 'Agent Controller (async job queue)',
    //     isActive: process.env.IS_AGENT_SERVICE_ACTIVE !== 'false',
    // },
];
