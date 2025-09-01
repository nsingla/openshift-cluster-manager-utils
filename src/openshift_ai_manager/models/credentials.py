"""Cloud provider credentials models."""

from pydantic import BaseModel, Field


class AWSCredentials(BaseModel):
    """AWS credentials for cluster creation."""
    access_key_id: str = Field(alias="accessKeyId")
    secret_access_key: str = Field(alias="secretAccessKey")
    account_id: str = Field(alias="accountId")


class GCPCredentials(BaseModel):
    """GCP credentials for cluster creation."""
    project_id: str = Field(alias="projectId")
    private_key_id: str = Field(alias="privateKeyId")
    private_key: str = Field(alias="privateKey")
    client_id: str = Field(alias="clientId")
    client_email: str = Field(alias="clientEmail")
    client_x509_cert_url: str = Field(alias="clientX509CertUrl")
    auth_type: str = Field(default="service_account", alias="authType")
    auth_uri: str = Field(
        default="https://accounts.google.com/o/oauth2/auth", 
        alias="authUri"
    )
    token_uri: str = Field(
        default="https://oauth2.googleapis.com/token", 
        alias="tokenUri"
    )
    auth_provider_x509_cert_url: str = Field(
        default="https://www.googleapis.com/oauth2/v1/certs",
        alias="authProviderX509CertUrl"
    )