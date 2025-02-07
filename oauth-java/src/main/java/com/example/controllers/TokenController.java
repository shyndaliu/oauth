package com.example.controllers;

import com.example.entities.TokenEntity;
import com.example.services.TokenService;
import io.micronaut.http.annotation.*;
import io.micronaut.http.HttpResponse;

import java.util.Map;
import java.util.Optional;

import java.time.Instant;

@Controller("/")
public class TokenController {

    private final TokenService tokenService;

    public TokenController(TokenService tokenService) {
        this.tokenService = tokenService;
    }

    @Post("/token")
    public HttpResponse<Map<String, Object>> issueToken(@Body Map<String, String> request) {
        String clientId = request.get("client_id");
        String scopes = request.get("scopes");

        // Check if a valid token already exists for the client
        Optional<TokenEntity> existingToken = tokenService.findValidTokenByClientId(clientId);

        if (existingToken.isPresent()) {
            TokenEntity tokenEntity = existingToken.get();
            Instant now = Instant.now();
            Instant expiresAt = tokenEntity.getExpiresAt();
            long tokenLifetime = expiresAt.getEpochSecond() - tokenEntity.getIssuedAt().getEpochSecond();
            long timeElapsed = now.getEpochSecond() - tokenEntity.getIssuedAt().getEpochSecond();

            // Check if 75% of the token's lifetime has passed
            if (timeElapsed >= (0.75 * tokenLifetime)) {
                // Generate a new token
                TokenEntity newToken = tokenService.createToken(clientId, scopes);
                return HttpResponse.ok(Map.of(
                    "token", newToken.getTokenId(),
                    "expires_at", newToken.getExpiresAt()
                ));
            } else {
                // Return the existing token
                return HttpResponse.ok(Map.of(
                    "token", tokenEntity.getTokenId(),
                    "expires_at", tokenEntity.getExpiresAt()
                ));
            }
        } else {
            // No valid token exists, generate a new one
            TokenEntity newToken = tokenService.createToken(clientId, scopes);
            return HttpResponse.ok(Map.of(
                "token", newToken.getTokenId(),
                "expires_at", newToken.getExpiresAt()
            ));
        }
    }

    @Post("/check")
    public HttpResponse<Map<String, Object>> checkToken(@Body Map<String, String> request) {
        String tokenId = request.get("token");

        Optional<TokenEntity> tokenEntity = tokenService.getToken(tokenId);
        if (tokenEntity.isEmpty()) {
            return HttpResponse.ok(Map.of("valid", false, "message", "Token not found"));
        }

        return HttpResponse.ok(Map.of("valid", true, "scopes", tokenEntity.get().getScopes()));
    }
}
