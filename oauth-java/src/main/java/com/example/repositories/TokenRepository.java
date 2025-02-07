package com.example.repositories;

import com.example.entities.TokenEntity;
import io.micronaut.data.annotation.Repository;
import io.micronaut.data.repository.CrudRepository;
import java.time.Instant;
import java.util.List;

@Repository
public interface TokenRepository extends CrudRepository<TokenEntity, String> {

    // Find tokens where 'expiresAt' is before the current time
    Iterable<TokenEntity> findByExpiresAtBefore(Instant instant);
    // Find tokens by client ID
    List<TokenEntity> findByClientId(String clientId);
}
