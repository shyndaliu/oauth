
---

> [MADR on choosing Python framework](#use-fastapi-for-python-implementation-of-oauth-token-management-system)
> [MADR on choosing Java framework](#use-micronaut-for-java-implementation-of-oauth-token-management-system)
> [MADR on choosing Golang framework](#use-...-for-go-implementation-of-oauth-token-management-system)
> [MADR on choosing Python framework](#use-plain-junit5-for-advanced-test-assertions)

---
# Use FastAPI for Python Implementation of OAuth Token Management System

## Context and Problem Statement

We are implementing an **OAuth token management** system in: Python, Golang, and Java. The system must handle 20K requests per second and is optimized in the such way that the performance depends on programming language. This MADR focuses on selecting the best-performing **Python framework**, which will later be compared with other languages to evaluate performance.

## Decision drivers

* Ability to handle 20k RPS (asynchronous support)
* Support external connection pools seamlessly  
* Resource-efficiency
## Considered Options

* FastAPI
* Django
* Flask

## Decision Outcome

Chosen option: FastAPI because comes out best (see "Pros and Cons of the Options" below).

### Consequences

* Good, because maintains 20K RPS even with single-tenancy
* Good, because easy to maintain connection pool
* Bad, because needs extra steps to overcome memory leaks

## Pros and Cons of the Options

### FastAPI

Homepage: <https://fastapi.tiangolo.com//>

* Good, because is the fastest
* Good, because minimal resource overhead
* Bad, because severe memory leaks

### Django

Homepage: <https://www.djangoproject.com/>

* Good, because scalable
* Bad, because synchronous by default
* Bad, because encourages monolithic structure

### Flask

Homepage: <https://flask.palletsprojects.com/en/stable/>


* Good, low memory usage
* Bad, synchronous by default
* Bad, because manual setup of connection pool

---
# Use Micronaut for Java Implementation of OAuth Token Management System

## Context and Problem Statement

We are implementing an **OAuth token management** system in: Python, Golang, and Java. The system must handle 20K requests per second and is optimized in the such way that the performance depends on programming language. This MADR focuses on selecting the best-performing **Java framework**, which will later be compared with other languages to evaluate performance.

## Decision drivers

* Ability to handle 20k RPS (asynchronous support)
* Support external connection pools seamlessly  
* Resource-efficiency
## Considered Options

* Spring Webflux
* Spring Boot
* Micronaut

## Decision Outcome

Chosen option: Micronaut because comes out best (see "Pros and Cons of the Options" below).

### Consequences

* Good, because designed for microservices
* Good, because low memo and cpu usage
* Bad, because needs extra steps to configure something

## Pros and Cons of the Options

### Spring WebFlux

Homepage: <https://docs.spring.io/spring-framework/reference/web/webflux.html/>

* Good, because reactive programming(high throughput + low resource usage)
* Good, because integrates well
* Bad, because hard, no wide ecosystem

### Spring Boot

Homepage: <https://spring.io/projects/spring-boot/>

* Good, because embedded server + load balancer
* Bad, because synchronous by default
* Bad, consume a lot RAM and CPU on start

### Micronaut

Homepage: <https://micronaut.io/>


* Good, because low memory usage + fast startup
* Good, because both reactive + non-reactive, made for microservices
* Good, because higher throughput
* Bad, because requires custom configuration in advanced cases

---
# Use ... for Go Implementation of OAuth Token Management System

## Context and Problem Statement

We are implementing an **OAuth token management** system in: Python, Golang, and Java. The system must handle 20K requests per second and is optimized in the such way that the performance depends on programming language. This MADR focuses on selecting the best-performing **go framework**, which will later be compared with other languages to evaluate performance.

## Decision drivers

* Ability to handle 20k RPS (asynchronous support)
* Support external connection pools seamlessly  
* Resource-efficiency
## Considered Options

* Fiber
* Gin
* Echo

## Decision Outcome

Chosen option: Fiber because comes out best (see "Pros and Cons of the Options" below).

### Consequences

* Good, because optimized for high throughput
* Good, because low memo and cpu usage
* Bad, because spikes on high load

## Pros and Cons of the Options

### Fiber

Homepage: <https://gofiber.io/>

* Good, because optimized or high performance
* Good, because asynchronous request handling
* Bad, because CPU/RAM spikes

### Gin

Homepage: <https://gin-gonic.com/>

* Good, because it is lightweight and performs well under moderate load, made for microservices
* Bad, because synchronous by default
* Bad, consume more memory under high concurrency

### Echo

Homepage: <https://echo.labstack.com/>


* Good, modular design easy to extend
* Bad, because not as fast as fiber
* Bad, because high memory usage under extreme load




