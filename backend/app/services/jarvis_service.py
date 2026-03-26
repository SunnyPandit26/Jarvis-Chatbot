from app.services.jarvis_core import run_jarvis

def process_query(message: str):
    response = run_jarvis(message)

    return {
        "text": response
    }