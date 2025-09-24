import logging
import os
import json
import time
import uuid
from functools import wraps

log_format = '%(asctime)s %(levelname)s [%(correlation_id)s] %(filename)s:%(lineno)d :: %(message)s'

class CorrelationFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = getattr(self, 'correlation_id', 'no-correlation')
        return True

def get():
    l = logging.getLogger()
    l.setLevel(logging.INFO)
    
    correlation_filter = CorrelationFilter()
    
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        for handler in l.handlers:
            handler.setFormatter(logging.Formatter(log_format))
            handler.addFilter(correlation_filter)
    else:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(log_format))
        handler.addFilter(correlation_filter)
        l.addHandler(handler)

    return l

def set_correlation_id(correlation_id):
    """Set correlation ID for current request"""
    for handler in logging.getLogger().handlers:
        for filter_obj in handler.filters:
            if isinstance(filter_obj, CorrelationFilter):
                filter_obj.correlation_id = correlation_id

def log_agent_interaction(func):
    """Decorator to log agent interactions with timing"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        l = logging.getLogger(__name__)
        start_time = time.time()
        
        try:
            l.info(f"AGENT_START: {func.__name__} with args: {json.dumps(str(args), default=str)}")
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            l.info(f"AGENT_SUCCESS: {func.__name__} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            l.error(f"AGENT_ERROR: {func.__name__} failed after {duration:.2f}s: {str(e)}")
            raise
    return wrapper
