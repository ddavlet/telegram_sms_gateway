from a2wsgi import ASGIMiddleware
from main import app  # Import your FastAPI app.

application = ASGIMiddleware(app)

