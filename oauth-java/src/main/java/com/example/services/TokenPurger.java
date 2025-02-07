package com.example.services;

import io.micronaut.scheduling.annotation.Scheduled;
import jakarta.inject.Singleton;


@Singleton
public class TokenPurger {
    private final TokenService tokenService;

    public TokenPurger(TokenService tokenService) {
        this.tokenService = tokenService;
    }

    @Scheduled(fixedDelay = "1h")
    void purgeTokens() {
        tokenService.purgeExpiredTokens();
    }
}
