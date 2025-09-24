import './logging.js';
import { setCorrelationId } from './logging.js';
import log4js from 'log4js';
import express from 'express';
import transport from './transport.js';
import packageInfo from './package.json' with { type: 'json'};
import jwt from 'jsonwebtoken';

const JWT_SIGNATURE_SECRET = process.env.JWT_SIGNATURE_SECRET || 'jwt-signature-secret';
const l = log4js.getLogger();
const PORT = process.env.AWS_LWA_PORT || process.env.PORT || 3001;

const app = express();
app.use(express.json());

// Request logging middleware
app.use(async (req, res, next) => {
    const correlationId = req.headers['x-correlation-id'] || 
                         req.headers['correlation-id'] || 
                         Math.random().toString(36).substring(7);
    
    setCorrelationId(correlationId);
    req.correlationId = correlationId;
    
    const startTime = Date.now();
    l.info(`MCP_REQUEST_START: ${req.method} ${req.originalUrl}, correlation_id=${correlationId}`);
    
    // Log request body for debugging (be careful with sensitive data)
    if (req.body && Object.keys(req.body).length > 0) {
        l.debug(`MCP_REQUEST_BODY: ${JSON.stringify(req.body)}`);
    }
    
    // Override res.end to log response
    const originalEnd = res.end;
    res.end = function(chunk, encoding) {
        const duration = Date.now() - startTime;
        l.info(`MCP_REQUEST_END: ${req.method} ${req.originalUrl}, status=${res.statusCode}, duration=${duration}ms, correlation_id=${correlationId}`);
        originalEnd.call(this, chunk, encoding);
    };
    
    return next();
});
    
// MCP authorization middleware
app.use('/mcp', async (req, res, next) => {
    const authorizationHeader = req.headers['authorization'];
    
    try {
        if (!authorizationHeader) {
            l.warn(`MCP_AUTH_MISSING: No authorization header, correlation_id=${req.correlationId}`);
            return res.status(401).send('Authorization header required');
        }
        
        const jwtString = authorizationHeader.split(' ')[1];
        if (!jwtString) {
            l.warn(`MCP_AUTH_MALFORMED: Invalid authorization format, correlation_id=${req.correlationId}`);
            return res.status(401).send('Invalid authorization format');
        }
        
        const claims = jwt.verify(jwtString, JWT_SIGNATURE_SECRET);
        req.auth = claims;
        
        l.info(`MCP_AUTH_SUCCESS: user_id=${claims.user_id}, user_name=${claims.user_name}, agent=${claims.sub}, correlation_id=${req.correlationId}`);
        
    } catch (e) {
        l.warn(`MCP_AUTH_FAILED: ${e.message}, correlation_id=${req.correlationId}`);
        return res.status(401).send('Unauthorized');
    }

    return next();
});

await transport.bootstrap(app);

app.listen(PORT, () => {
    l.info(`MCP_SERVER_STARTED: version=${packageInfo.version}, port=${PORT}`);
});



