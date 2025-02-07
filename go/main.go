package main

import (
	"database/sql"
	"fmt"
	"log"
	"time"

	_ "github.com/denisenkom/go-mssqldb"
	"github.com/gofiber/fiber/v2"
	"github.com/golang-jwt/jwt/v4"
	"github.com/jellydator/ttlcache/v2"
)

// Connection parameters
const (
	username = "uldanone"
	password = "125563_oauth"
	server   = "oauth.database.windows.net"
	database = "oauth_db"
)

type Token struct {
	TokenID   string    `db:"token_id"`
	ClientID  string    `db:"client_id"`
	Scopes    string    `db:"scopes"`
	IssuedAt  time.Time `db:"issued_at"`
	ExpiresAt time.Time `db:"expires_at"`
}

var (
	secretKey = []byte("your-secret-key")
	cache     = ttlcache.NewCache()
)

// Create the connection string
func getConnectionString() string {
	return fmt.Sprintf(
		"sqlserver://%s:%s@%s?database=%s&encrypt=true",
		username, password, server, database,
	)
}

func main() {
	app1 := fiber.New()
	//app2 := fiber.New()

	// Connect to the database
	db, err := sql.Open("sqlserver", getConnectionString())
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	db.SetMaxOpenConns(100)
	db.SetMaxIdleConns(100)
	db.SetConnMaxLifetime(0)
	db.SetConnMaxIdleTime(0)

	// Start the token purger
	go purgeExpiredTokens(db)

	// Define routes for app1 (port 8000)
	app1.Post("/token", issueToken(db))
	app1.Post("/check", checkToken(db))

	// Define routes for app2 (port 8001)
	// app2.Post("/token", issueToken(db))
	// app2.Post("/check", checkToken(db))
	// app2.Get("/health", func(c *fiber.Ctx) error {
	// 	return c.SendString("Server 2 is running on port 8001")
	// })

	// Run both servers concurrently

	log.Fatal(app1.Listen(":8000"))

	//log.Fatal(app2.Listen(":8001"))
}

func createToken(clientID, scopes string) (string, time.Time, error) {
	expiresAt := time.Now().Add(120 * time.Minute)
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"client_id": clientID,
		"scopes":    scopes,
		"exp":       expiresAt.Unix(),
	})
	tokenString, err := token.SignedString(secretKey)
	return tokenString, expiresAt, err
}

func validateToken(tokenString string) (jwt.MapClaims, error) {
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
		return secretKey, nil
	})
	if err != nil {
		return nil, err
	}
	if claims, ok := token.Claims.(jwt.MapClaims); ok && token.Valid {
		return claims, nil
	}
	return nil, fmt.Errorf("invalid or expired token")
}

func purgeExpiredTokens(db *sql.DB) {
	for {
		_, err := db.Exec("DELETE FROM Tokens WHERE expires_at < GETUTCDATE()")
		if err != nil {
			log.Println("Error purging expired tokens:", err)
		}
		time.Sleep(1 * time.Hour)
	}
}

func issueToken(db *sql.DB) fiber.Handler {
	return func(c *fiber.Ctx) error {
		type TokenRequest struct {
			ClientID string `json:"client_id"`
			Scopes   string `json:"scopes"`
		}

		var req TokenRequest
		if err := c.BodyParser(&req); err != nil {
			return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
				"error": "Invalid request",
			})
		}

		// Check cache
		if cachedToken, err := cache.Get(req.ClientID); err == nil {
			if cachedToken.(Token).ExpiresAt.After(time.Now()) {
				timeLeft := cachedToken.(Token).ExpiresAt.Sub(time.Now())
				if timeLeft > 30*time.Minute {
					// Return token from cache if it has more than 30 minutes left
					return c.JSON(fiber.Map{
						"token":      cachedToken.(Token).TokenID,
						"expires_at": cachedToken.(Token).ExpiresAt,
					})
				}
			}
		}

		// Check database for existing token
		var existingToken Token
		err := db.QueryRow("SELECT token_id, client_id, scopes, issued_at, expires_at FROM Tokens WHERE client_id = @client_id", sql.Named("client_id", req.ClientID)).Scan(
			&existingToken.TokenID, &existingToken.ClientID, &existingToken.Scopes, &existingToken.IssuedAt, &existingToken.ExpiresAt,
		)
		if err == nil && existingToken.ExpiresAt.After(time.Now()) {
			// Check if the token has 30 minutes or more left
			timeLeft := existingToken.ExpiresAt.Sub(time.Now())
			if timeLeft > 30*time.Minute {
				// Return token from database if it has more than 30 minutes left
				return c.JSON(fiber.Map{
					"token":      existingToken.TokenID,
					"expires_at": existingToken.ExpiresAt,
				})
			}
		}

		// Create new token
		tokenString, expiresAt, err := createToken(req.ClientID, req.Scopes)
		if err != nil {
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
				"error": "Failed to create token",
			})
		}

		// Insert into database
		_, err = db.Exec("INSERT INTO Tokens (token_id, client_id, scopes, issued_at, expires_at) VALUES (@token_id, @client_id, @scopes, @issued_at, @expires_at)",
			sql.Named("token_id", tokenString),
			sql.Named("client_id", req.ClientID),
			sql.Named("scopes", req.Scopes),
			sql.Named("issued_at", time.Now()),
			sql.Named("expires_at", expiresAt),
		)
		if err != nil {
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
				"error": "Failed to insert token into database",
			})
		}

		// Cache the token
		cache.Set(req.ClientID, Token{
			TokenID:   tokenString,
			ClientID:  req.ClientID,
			Scopes:    req.Scopes,
			IssuedAt:  time.Now(),
			ExpiresAt: expiresAt,
		})

		return c.JSON(fiber.Map{
			"token":      tokenString,
			"expires_at": expiresAt,
		})
	}
}

func checkToken(db *sql.DB) fiber.Handler {
	return func(c *fiber.Ctx) error {
		type CheckRequest struct {
			Token string `json:"token"`
		}

		var req CheckRequest
		if err := c.BodyParser(&req); err != nil {
			return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
				"error": "Invalid request",
			})
		}

		// Validate token
		_, err := validateToken(req.Token)
		if err != nil {
			return c.JSON(fiber.Map{
				"valid": false,
				"error": "Invalid or expired token",
			})
		}

		// Check cache
		for _, clientID := range cache.GetKeys() {
			if cachedToken, err := cache.Get(clientID); err == nil {
				if cachedToken.(Token).TokenID == req.Token {
					return c.JSON(fiber.Map{
						"valid":  true,
						"scopes": cachedToken.(Token).Scopes,
					})
				}
			}
		}

		// Check database
		var dbToken Token
		err = db.QueryRow("SELECT token_id, client_id, scopes, issued_at, expires_at FROM Tokens WHERE token_id = @token_id", sql.Named("token_id", req.Token)).Scan(
			&dbToken.TokenID, &dbToken.ClientID, &dbToken.Scopes, &dbToken.IssuedAt, &dbToken.ExpiresAt,
		)
		if err != nil {
			return c.JSON(fiber.Map{
				"valid": false,
				"error": "Token not found",
			})
		}

		return c.JSON(fiber.Map{
			"valid":  true,
			"scopes": dbToken.Scopes,
		})
	}
}
