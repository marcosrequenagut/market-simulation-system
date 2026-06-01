from fastapi import FastAPI

app = FastAPI(title="SP500 Analyzer", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}
