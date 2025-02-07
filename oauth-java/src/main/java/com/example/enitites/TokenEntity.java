package com.example.entities;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import java.time.Instant;

@Entity
public class TokenEntity {

    @Id
    private String tokenId;
    private String clientId;
    private String scopes;
    private Instant issuedAt;
    private Instant expiresAt;

    // **Getters**
    public String getTokenId() {
        return tokenId;
    }

    public String getClientId() {
        return clientId;
    }

    public String getScopes() {
        return scopes;
    }

    public Instant getIssuedAt() {
        return issuedAt;
    }

    public Instant getExpiresAt() {
        return expiresAt;
    }

    // **Setters (if needed)**
    public void setTokenId(String tokenId) {
        this.tokenId = tokenId;
    }

    public void setClientId(String clientId) {
        this.clientId = clientId;
    }

    public void setScopes(String scopes) {
        this.scopes = scopes;
    }

    public void setIssuedAt(Instant issuedAt) {
        this.issuedAt = issuedAt;
    }

    public void setExpiresAt(Instant expiresAt) {
        this.expiresAt = expiresAt;
    }
}
