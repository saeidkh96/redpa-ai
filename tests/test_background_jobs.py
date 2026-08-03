from app.background_jobs.schemas import BackgroundJobCreate

def test_job_defaults():
    job = BackgroundJobCreate(job_type="sleep")
    assert job.max_attempts == 3
    assert job.delay_seconds == 0
