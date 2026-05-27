import pytest
import uuid
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_create_job_returns_201(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/jobs/",
        json={"job_type": "guide_scan", "input_data": {"seq": "A"}, "priority": 5}
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "PENDING"
    assert data["job_type"] == "guide_scan"
    assert "created_at" in data

async def test_create_job_validates_required_fields(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/jobs/",
        json={"input_data": {"seq": "A"}}
    )
    assert response.status_code == 422

async def test_get_job_returns_200(async_client: AsyncClient):
    create_resp = await async_client.post(
        "/api/v1/jobs/",
        json={"job_type": "guide_scan", "input_data": {}, "priority": 5}
    )
    job_id = create_resp.json()["id"]
    
    get_resp = await async_client.get(f"/api/v1/jobs/{job_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == job_id

async def test_get_nonexistent_job_returns_404(async_client: AsyncClient):
    random_id = str(uuid.uuid4())
    response = await async_client.get(f"/api/v1/jobs/{random_id}")
    assert response.status_code == 404
    assert response.json()["detail"]["error_code"] == "JOB_NOT_FOUND"

async def test_list_jobs_returns_paginated_response(async_client: AsyncClient):
    for i in range(5):
        await async_client.post(
            "/api/v1/jobs/",
            json={"job_type": "type_" + str(i), "input_data": {}, "priority": 5}
        )
        
    response = await async_client.get("/api/v1/jobs/?limit=3&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    assert data["total"] >= 5 # Might be more if tests run concurrently, but db is cleaned

async def test_cancel_pending_job_returns_200(async_client: AsyncClient):
    create_resp = await async_client.post(
        "/api/v1/jobs/",
        json={"job_type": "guide_scan", "input_data": {}, "priority": 5}
    )
    job_id = create_resp.json()["id"]
    
    del_resp = await async_client.delete(f"/api/v1/jobs/{job_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "CANCELLED"

async def test_cancel_running_job_returns_409(async_client: AsyncClient, db_session):
    # Create job
    create_resp = await async_client.post(
        "/api/v1/jobs/",
        json={"job_type": "guide_scan", "input_data": {}, "priority": 5}
    )
    job_id = create_resp.json()["id"]
    
    # Update to RUNNING manually using session since no endpoint for it yet
    from app.services.job_service import update_job_status
    from app.models.job import JobStatus
    await update_job_status(db_session, uuid.UUID(job_id), JobStatus.RUNNING)
    
    del_resp = await async_client.delete(f"/api/v1/jobs/{job_id}")
    assert del_resp.status_code == 409
    assert del_resp.json()["detail"]["error_code"] == "JOB_NOT_CANCELLABLE"

async def test_job_status_endpoint(async_client: AsyncClient):
    create_resp = await async_client.post(
        "/api/v1/jobs/",
        json={"job_type": "guide_scan", "input_data": {"secret": "hide_me"}, "priority": 5}
    )
    job_id = create_resp.json()["id"]
    
    status_resp = await async_client.get(f"/api/v1/jobs/{job_id}/status")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert "id" in data
    assert "status" in data
    assert "progress" in data
    assert "updated_at" in data
    assert "input_data" not in data
    assert "result_data" not in data
