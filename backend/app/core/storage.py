"""Object storage client wrapper for MinIO / S3 compatible storage."""

import io
import logging
from typing import Optional
from minio import Minio
from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Manages document storage with MinIO S3-compatible backend."""

    def __init__(self):
        self.endpoint = settings.MINIO_ENDPOINT
        self.access_key = settings.MINIO_ROOT_USER
        self.secret_key = settings.MINIO_ROOT_PASSWORD
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self.secure = settings.MINIO_USE_SSL
        self._client: Optional[Minio] = None

    @property
    def client(self) -> Minio:
        if self._client is None:
            self._client = Minio(
                endpoint=self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure,
            )
            self._ensure_bucket()
        return self._client

    def _ensure_bucket(self) -> None:
        """Verifica se o bucket existe; cria se necessario."""
        try:
            if not self._client.bucket_exists(self.bucket_name):
                self._client.make_bucket(self.bucket_name)
                logger.info(f"Bucket MinIO '{self.bucket_name}' criado com sucesso.")
        except Exception as exc:
            logger.warning(
                f"Nao foi possivel verificar/criar bucket '{self.bucket_name}': {str(exc)}"
            )

    def upload_file(
        self, file_data: bytes, object_name: str, content_type: str = "application/pdf"
    ) -> str:
        """Faz upload de arquivo para o MinIO e retorna o storage_path."""
        data_stream = io.BytesIO(file_data)
        self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
            data=data_stream,
            length=len(file_data),
            content_type=content_type,
        )
        storage_path = f"s3://{self.bucket_name}/{object_name}"
        logger.info(f"Arquivo enviado ao MinIO: {storage_path}")
        return storage_path

    def download_file(self, object_name: str, destination_path: str) -> None:
        """Baixa um objeto do MinIO para um arquivo local."""
        self.client.fget_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
            file_path=destination_path,
        )

    def get_file_bytes(self, object_name: str) -> bytes:
        """Recupera os bytes de um objeto diretamente do MinIO."""
        response = None
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            return response.read()
        finally:
            if response:
                response.close()
                response.release_conn()


storage_service = StorageService()
