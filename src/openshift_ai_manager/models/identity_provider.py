"""Identity provider configuration models."""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class IdentityProviderConfig(BaseModel):
    """Identity provider configuration."""
    type: Literal["ldap", "htpasswd"] = Field(description="Type of identity provider")
    name: str = Field(description="Identity provider name")
    
    # HTPasswd specific
    username: Optional[str] = Field(
        default=None, 
        description="Admin username for htpasswd"
    )
    password: Optional[str] = Field(
        default=None, 
        description="Admin password for htpasswd"
    )
    
    # LDAP specific
    url: Optional[str] = Field(default=None, description="LDAP server URL")
    bind_dn: Optional[str] = Field(
        default=None, 
        description="LDAP bind DN",
        alias="bindDn"
    )
    bind_password: Optional[str] = Field(
        default=None, 
        description="LDAP bind password",
        alias="bindPassword"
    )
    users_string: Optional[str] = Field(
        default=None, 
        description="LDAP users string",
        alias="usersString"
    )
    passwords_string: Optional[str] = Field(
        default=None, 
        description="LDAP passwords string",
        alias="passwordsString"
    )
    num_users_per_group: int = Field(
        default=20, 
        description="Number of users to create per group",
        alias="numUsersPerGroup"
    )