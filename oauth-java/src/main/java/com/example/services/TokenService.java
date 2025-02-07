package com.example.services;

import com.example.entities.TokenEntity;
import com.example.repositories.TokenRepository;
import io.micronaut.transaction.annotation.Transactional;
import jakarta.inject.Singleton;
import java.time.Instant;
import java.util.Optional;

import io.micronaut.cache.annotation.Cacheable;
import io.micronaut.cache.annotation.CachePut;

@Singleton
public class TokenService {

    private final TokenRepository tokenRepository;

    public TokenService(TokenRepository tokenRepository) {
        this.tokenRepository = tokenRepository;
    }

    @CachePut("tokens") 
    public TokenEntity createToken(String clientId, String scopes) {
        TokenEntity tokenEntity = new TokenEntity();
        tokenEntity.setTokenId(java.util.UUID.randomUUID().toString());
        tokenEntity.setClientId(clientId);
        tokenEntity.setScopes(scopes);
        tokenEntity.setIssuedAt(Instant.now());
        tokenEntity.setExpiresAt(Instant.now().plusSeconds(7200));

        return tokenRepository.save(tokenEntity);
    }

    @Cacheable("tokens") // Cache name
    public Optional<TokenEntity> getToken(String tokenId) {
        return tokenRepository.findById(tokenId)
            .filter(token -> token.getExpiresAt().isAfter(Instant.now())); // Filter out expired tokens
    }
    @Cacheable("tokens") 
    public Optional<TokenEntity> findValidTokenByClientId(String clientId) {
        return tokenRepository.findByClientId(clientId)
            .stream()
            .filter(token -> token.getExpiresAt().isAfter(Instant.now())) // Filter out expired tokens
            .findFirst();
    }
    
     public void purgeExpiredTokens() {
        Instant now = Instant.now();
        // Find all tokens where 'expiresAt' is before the current time
        Iterable<TokenEntity> expiredTokens = tokenRepository.findByExpiresAtBefore(now);
        
        // Delete expired tokens
        expiredTokens.forEach(token -> tokenRepository.delete(token));
    }
}
