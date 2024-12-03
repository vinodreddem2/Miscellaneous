import asyncio
import sys
import logging
import uvicorn
import os
import threading
from django.core.asgi import get_asgi_application

from starlette.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RedirectHttpToHttpsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, enable_redirect: bool):
        super().__init__(app)
        self.enable_redirect = enable_redirect

    async def dispatch(self, request, call_next):
        if request.scope['scheme'] == 'http' and self.enable_redirect:
            host = request.headers.get('host', '')
            # Construct the new URL with HTTPS scheme
            new_url = f"https://{host}{request.url.path}"
            if request.url.query:
                new_url += f'?{request.url.query}'            
            return RedirectResponse(url=new_url)

        # Call the next middleware or request handler in the chain
        response = await call_next(request)
        return response
    

ssl_keyfile = "" #Path of key file
ssl_certfile = "" # Path of Cert file
asgi_app = get_asgi_application()
https_config = uvicorn.Config(app=asgi_app, port=443, host="0.0.0.0",
                                              ssl_keyfile=ssl_keyfile, ssl_certfile=ssl_certfile)
https_server = uvicorn.Server(https_config)

enable_redirect = True # True or False to redieect http requests to https
if enable_redirect:
    http_asgi_app = RedirectHttpToHttpsMiddleware(asgi_app, enable_redirect)    
else:
    http_asgi_app = asgi_app

http_config = uvicorn.Config(app=http_asgi_app, port=80, host="0.0.0.0")
http_server = uvicorn.Server(http_config)

# Run both servers asynchronously using asyncio
async def run_servers():    
    # Run both servers
    loop = asyncio.get_event_loop()
    await asyncio.gather(
        loop.run_in_executor(None, http_server.run),
        loop.run_in_executor(None, https_server.run),
    )

asyncio.run(run_servers())