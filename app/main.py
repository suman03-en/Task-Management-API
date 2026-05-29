from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"root": "Im root"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", reload=True)