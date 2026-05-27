import pytest
import os
import uuid
from httpx import AsyncClient
from io import BytesIO

pytestmark = pytest.mark.asyncio

async def test_upload_valid_fasta_returns_201(async_client: AsyncClient, sample_fasta_content: bytes):
    files = {'file': ('test.fa', sample_fasta_content, 'application/octet-stream')}
    response = await async_client.post("/api/v1/files/upload", files=files)
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["original_name"] == "test.fa"
    assert data["file_size_bytes"] == len(sample_fasta_content)
    assert len(data["md5_hash"]) == 32
    assert len(data["sha256_hash"]) == 64

async def test_upload_invalid_extension_returns_422(async_client: AsyncClient):
    files = {'file': ('test.exe', b"fake executable", 'application/octet-stream')}
    response = await async_client.post("/api/v1/files/upload", files=files)
    
    assert response.status_code == 422
    assert "extension" in response.json()["detail"]

async def test_upload_path_traversal_returns_422(async_client: AsyncClient):
    files = {'file': ('../../etc/passwd.fa', b"fake data", 'application/octet-stream')}
    response = await async_client.post("/api/v1/files/upload", files=files)
    
    assert response.status_code == 422
    assert "invalid" in response.json()["detail"].lower()

async def test_upload_oversized_file_returns_422(async_client: AsyncClient):
    # Mock settings.max_upload_size_mb to a very small value to test easily
    from app.config.settings import get_settings
    settings = get_settings()
    settings.max_upload_size_mb = 0 # 0 MB limit
    
    files = {'file': ('large.fa', b"123456789", 'application/octet-stream')}
    response = await async_client.post("/api/v1/files/upload", files=files)
    
    assert response.status_code == 422
    settings.max_upload_size_mb = 100 # Reset

async def test_get_uploaded_file_returns_200(async_client: AsyncClient, sample_fasta_content: bytes):
    files = {'file': ('test.fa', sample_fasta_content, 'application/octet-stream')}
    create_resp = await async_client.post("/api/v1/files/upload", files=files)
    file_id = create_resp.json()["id"]
    
    get_resp = await async_client.get(f"/api/v1/files/{file_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == file_id

async def test_delete_file_returns_204(async_client: AsyncClient, sample_fasta_content: bytes):
    files = {'file': ('test.fa', sample_fasta_content, 'application/octet-stream')}
    create_resp = await async_client.post("/api/v1/files/upload", files=files)
    file_id = create_resp.json()["id"]
    
    del_resp = await async_client.delete(f"/api/v1/files/{file_id}")
    assert del_resp.status_code == 204
    
    get_resp = await async_client.get(f"/api/v1/files/{file_id}")
    assert get_resp.status_code == 404

async def test_file_physically_deleted(async_client: AsyncClient, sample_fasta_content: bytes):
    files = {'file': ('test2.fa', sample_fasta_content, 'application/octet-stream')}
    create_resp = await async_client.post("/api/v1/files/upload", files=files)
    data = create_resp.json()
    file_id = data["id"]
    file_path = data["file_path"]
    
    assert os.path.exists(file_path)
    
    await async_client.delete(f"/api/v1/files/{file_id}")
    
    assert not os.path.exists(file_path)
