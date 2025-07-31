from fastapi import FastAPI
from app.services.advanced_scheduler import advanced_scheduler

app = FastAPI()

@app.get("/test-jobs")
async def test_jobs():
    try:
        jobs = advanced_scheduler.list_jobs()
        return {
            "status": "success",
            "jobs_count": len(jobs),
            "jobs": jobs
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "jobs": []
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
