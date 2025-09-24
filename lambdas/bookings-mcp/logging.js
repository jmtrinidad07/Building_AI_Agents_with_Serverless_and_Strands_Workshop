import log4js from 'log4js';

const layout = {
    type: 'pattern',
    pattern: '%p [%X{correlationId}] [%f{1}:%l:%M] %m%'
}

log4js.configure({
    appenders: {
        stdout: {
            type: 'stdout',
            enableCallStack: true,
            layout
        }
    },
    categories: {
        default: {
            appenders: ['stdout'],
            level: 'debug',
            enableCallStack: true
        }
    }
});

// Helper function to set correlation ID for request
export const setCorrelationId = (correlationId) => {
    // Use log4js context properly
    const logger = log4js.getLogger();
    logger.addContext('correlationId', correlationId || 'no-correlation');
};

// Helper function to log tool execution with timing
export const logToolExecution = (toolName, userId, startTime, endTime, success, error = null) => {
    const l = log4js.getLogger();
    const duration = endTime - startTime;
    
    if (success) {
        l.info(`TOOL_SUCCESS: ${toolName} for user_id=${userId} completed in ${duration.toFixed(2)}ms`);
    } else {
        l.error(`TOOL_ERROR: ${toolName} for user_id=${userId} failed after ${duration.toFixed(2)}ms: ${error}`);
    }
};
