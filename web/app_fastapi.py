import os
import dotenv
import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
import oauth
import httpx

dotenv.load_dotenv()

AGENT_ENDPOINT_URL = os.getenv("AGENT_ENDPOINT_URL")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="secret")

# Configure for CloudFront
app.root_path = "/proxy/8000"

oauth.add_oauth_routes(app)

@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    # Check if user is authenticated
    if not "access_token" in request.session or not "username" in request.session:
        return f'<script>window.location.href="/login"</script>'
    
    username = request.session.get('username', 'Guest')
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Travel Agent</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            #chat { border: 1px solid #ccc; height: 400px; overflow-y: scroll; padding: 10px; margin-bottom: 10px; }
            .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
            .user { background: #e3f2fd; text-align: right; }
            .assistant { background: #f5f5f5; }
            #input { width: 70%; padding: 10px; }
            #send { padding: 10px 20px; }
        </style>
    </head>
    <body>
        <h1>AcmeCorp Travel Agent</h1>
        <p>Welcome, """ + username + """! <a href='/logout'>Logout</a></p>
        <div id="chat"></div>
        <input type="text" id="input" placeholder="Ask me about travel...">
        <button id="send">Send</button>
        
        <script>
            const chat = document.getElementById('chat');
            const input = document.getElementById('input');
            const send = document.getElementById('send');
            
            function addMessage(content, role) {
                const div = document.createElement('div');
                div.className = `message ${role}`;
                div.textContent = content;
                chat.appendChild(div);
                chat.scrollTop = chat.scrollHeight;
            }
            
            async function sendMessage() {
                const message = input.value.trim();
                if (!message) return;
                
                addMessage(message, 'user');
                input.value = '';
                
                try {
                    const response = await fetch(`/proxy/8000/api/chat?message=${encodeURIComponent(message)}`);
                    
                    const result = await response.text();
                    addMessage(result, 'assistant');
                } catch (error) {
                    addMessage(`Error: ${error.message}`, 'assistant');
                }
            }
            
            send.onclick = sendMessage;
            input.onkeypress = (e) => { if (e.key === 'Enter') sendMessage(); };
        </script>
    </body>
    </html>
    """

@app.get("/api/chat")
async def chat_endpoint(message: str, request: Request):
    print(f"🔥 CHAT ENDPOINT CALLED: {message}")
    
    # Check authentication
    if not "access_token" in request.session:
        return "Please login first"
    
    token = request.session["access_token"]
    username = request.session["username"]
    
    try:
        print(f"🔥 User: {username}")
        # Use direct API Gateway URL instead of CloudFront
        direct_url = AGENT_ENDPOINT_URL
        print(f"🔥 Making request to: {direct_url} (bypassing CloudFront)")
        print(f"🔥 Token (first 50 chars): {token[:50]}...")
        print(f"🔥 Full request headers: Authorization: Bearer {token[:20]}...")
        
        response = httpx.post(
            direct_url,
            headers={"Authorization": f"Bearer {token}"},
            json={"text": message},
            timeout=30
        )
        
        print(f"🔥 Response status: {response.status_code}")
        print(f"🔥 Response headers: {response.headers}")
        print(f"🔥 Response text: {response.text}")
        
        if response.status_code == 403:
            print(f"🔥 403 DEBUG - Token might be expired or invalid")
            print(f"🔥 403 DEBUG - Trying direct API Gateway URL")
        
        if response.status_code == 200:
            return response.json()["text"]
        else:
            return f"Agent error: {response.status_code} - {response.text[:100]}"
            
    except Exception as e:
        print(f"🔥 Exception: {str(e)}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)