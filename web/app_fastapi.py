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
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                max-width: 900px; margin: 0 auto; padding: 20px; 
                background: #f8f9fa; color: #333;
            }
            .header {
                background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            #chat { 
                background: white; border-radius: 10px; height: 500px; 
                overflow-y: auto; padding: 20px; margin-bottom: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .message { 
                margin: 15px 0; padding: 12px 16px; border-radius: 18px; 
                max-width: 80%; word-wrap: break-word; line-height: 1.4;
            }
            .user { 
                background: #007bff; color: white; margin-left: auto; 
                border-bottom-right-radius: 4px;
            }
            .assistant { 
                background: #f1f3f4; color: #333; margin-right: auto;
                border-bottom-left-radius: 4px;
            }
            .input-container {
                background: white; padding: 20px; border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1); display: flex; gap: 10px;
            }
            #input { 
                flex: 1; padding: 12px 16px; border: 2px solid #e9ecef; 
                border-radius: 25px; font-size: 16px; outline: none;
            }
            #input:focus { border-color: #007bff; }
            #send { 
                padding: 12px 24px; background: #007bff; color: white; 
                border: none; border-radius: 25px; cursor: pointer; font-weight: 500;
            }
            #send:hover { background: #0056b3; }
            #send:disabled { background: #6c757d; cursor: not-allowed; }
            .loader {
                display: none; align-items: center; gap: 8px; color: #666;
                margin: 10px 0; padding: 12px 16px;
            }
            .typing-dots {
                display: flex; gap: 4px;
            }
            .typing-dots span {
                width: 8px; height: 8px; border-radius: 50%; 
                background: #007bff; animation: typing 1.4s infinite;
            }
            .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
            .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
            @keyframes typing {
                0%, 60%, 100% { transform: translateY(0); }
                30% { transform: translateY(-10px); }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🧳 AcmeCorp Travel Agent</h1>
            <p>Welcome, <strong>""" + username + """</strong>! <a href='/logout'>Logout</a></p>
        </div>
        
        <div id="chat"></div>
        
        <div class="loader" id="loader">
            <span>Agent is typing</span>
            <div class="typing-dots">
                <span></span><span></span><span></span>
            </div>
        </div>
        
        <div class="input-container">
            <input type="text" id="input" placeholder="Ask me about travel bookings...">
            <button id="send">Send</button>
        </div>
        
        <script>
            const chat = document.getElementById('chat');
            const input = document.getElementById('input');
            const send = document.getElementById('send');
            const loader = document.getElementById('loader');
            
            function addMessage(content, role) {
                const div = document.createElement('div');
                div.className = 'message ' + role;
                div.textContent = content;
                chat.appendChild(div);
                chat.scrollTop = chat.scrollHeight;
            }
            
            function showLoader() {
                loader.style.display = 'flex';
                send.disabled = true;
                input.disabled = true;
            }
            
            function hideLoader() {
                loader.style.display = 'none';
                send.disabled = false;
                input.disabled = false;
            }
            
            async function sendMessage() {
                const message = input.value.trim();
                if (!message) return;
                
                addMessage(message, 'user');
                input.value = '';
                showLoader();
                
                try {
                    const response = await fetch('/proxy/8000/api/chat?message=' + encodeURIComponent(message));
                    const result = await response.text();
                    hideLoader();
                    addMessage(result, 'assistant');
                } catch (error) {
                    hideLoader();
                    addMessage('Error: ' + error.message, 'assistant');
                }
            }
            
            send.onclick = sendMessage;
            input.onkeypress = function(e) { 
                if (e.key === 'Enter' && !send.disabled) sendMessage(); 
            };
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