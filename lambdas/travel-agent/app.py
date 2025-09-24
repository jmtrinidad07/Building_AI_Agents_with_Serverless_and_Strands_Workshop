import logger
import agent
import json
import jwt
import os
import uuid
from user import User

l = logger.get()

JWT_SIGNATURE_SECRET = os.environ['JWT_SIGNATURE_SECRET']
COGNITO_JWKS_URL = os.environ['COGNITO_JWKS_URL']
jwks_client = jwt.PyJWKClient(COGNITO_JWKS_URL)

def get_jwt_claims(authorization_header):
    jwt_string = authorization_header.split(" ")[1]
    signing_key = jwks_client.get_signing_key_from_jwt(jwt_string)
    claims = jwt.decode(jwt_string, signing_key.key, algorithms=["RS256"])
    return claims

def handler(event: dict, ctx):
    # Generate correlation ID for this request
    correlation_id = str(uuid.uuid4())[:8]
    logger.set_correlation_id(correlation_id)
    
    l.info(f"REQUEST_START: correlation_id={correlation_id}")
    
    try:
        # Parse JWT and extract user info
        claims = get_jwt_claims(event["headers"]["Authorization"])
        user = User(id=claims["sub"], name=claims["username"])
        l.info(f"AUTH_SUCCESS: user_id={user.id}, username={user.name}")
        
        # Log request details
        source_ip = event["requestContext"]["identity"]["sourceIp"]
        request_body: dict = json.loads(event["body"])
        prompt_text = request_body["text"]
        
        l.info(f"REQUEST_DETAILS: source_ip={source_ip}, prompt_length={len(prompt_text)}")
        l.info(f"USER_PROMPT: {prompt_text}")
        
        # Build composite prompt
        composite_prompt = f"User name: {user.name}\n"
        composite_prompt += f"User IP: {source_ip}\n"
        composite_prompt += f"User prompt: {prompt_text}"
        
        # Call agent with enhanced logging
        l.info("AGENT_CALL_START")
        response_text = agent.prompt(user, composite_prompt)
        l.info(f"AGENT_CALL_SUCCESS: response_length={len(response_text)}")
        l.info(f"AGENT_RESPONSE: {response_text}")
        
        l.info(f"REQUEST_SUCCESS: correlation_id={correlation_id}")
        return {
            "statusCode": 200,
            "body": json.dumps({"text": response_text}),
            "headers": {"X-Correlation-ID": correlation_id}
        }
        
    except Exception as e:
        l.error(f"REQUEST_ERROR: correlation_id={correlation_id}, error={str(e)}", exc_info=True)
        return {
            "statusCode": 401 if "jwt" in str(e).lower() else 500,
            "body": json.dumps({"error": "Request failed", "correlation_id": correlation_id}),
            "headers": {"X-Correlation-ID": correlation_id}
        }

if __name__ == "__main__":
    debug_token = "your-debug-token"
    l.info("DEBUG_MODE: Running in test mode")
    
    body = json.dumps({"text": "Book me a trip to New York"})
    event = {
        "requestContext": {"identity": {"sourceIp": "70.200.50.45"}},
        "headers": {"Authorization": f"Bearer {debug_token}"},
        "body": body
    }
    
    handler_response = handler(event, None)
    l.info(f"DEBUG_RESPONSE: {handler_response}")
