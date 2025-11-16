"""
Database Session Management

This file manages the connection to our PostgreSQL database using SQLAlchemy.

What's a database session?
- Think of it like opening a file: you open it, use it, then close it
- A session represents a conversation with the database
- It handles transactions, connections, and connection pooling

Why SQLAlchemy?
- ORM (Object Relational Mapping) - work with Python objects instead of SQL
- Connection pooling - reuse database connections for better performance
- Transaction management - automatically commit or rollback changes

Example:
    Instead of writing SQL:
        SELECT * FROM transactions WHERE user_id = 'user_123'

    We can write Python:
        db.query(Transaction).filter(Transaction.user_id == "user_123").all()

Architecture:
    API Endpoint → get_db() → SessionLocal → PostgreSQL Database
                              (connection pool)
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings


# CREATE DATABASE ENGINE
# The engine is the "connection manager" to the database
# It handles connection pooling, query execution, and database dialect
engine = create_engine(
    settings.DATABASE_URL,  # e.g., "postgresql://user:pass@localhost:5432/sentinel"

    # Connection Pool Settings
    # Instead of creating a new database connection for every request (slow),
    # we maintain a "pool" of reusable connections

    pool_size=settings.DB_POOL_SIZE,  # How many connections to keep open (default: 5)
                                       # More connections = handle more concurrent requests
                                       # Too many = waste database resources

    max_overflow=settings.DB_MAX_OVERFLOW,  # Extra connections when pool is full (default: 10)
                                             # Total max connections = pool_size + max_overflow
                                             # Example: 5 + 10 = 15 max concurrent connections

    pool_pre_ping=True,  # Verify connections before using
                         # This prevents "database connection lost" errors
                         # Before using a connection, SQLAlchemy checks if it's still alive
                         # If dead, automatically creates a new connection

    echo=settings.DEBUG,  # Log all SQL queries to console
                         # In development (DEBUG=True): See all SQL queries for debugging
                         # In production (DEBUG=False): Silent for performance
                         # Example log: "SELECT * FROM transactions WHERE id = 123"
)


# CREATE SESSION FACTORY
# SessionLocal is a "factory" that creates database sessions
# Each session is a separate conversation with the database
# Think of it like a checkout counter at a store - one customer at a time
SessionLocal = sessionmaker(
    autocommit=False,  # Don't auto-commit changes (we manually call commit())
                       # This allows transactions: all-or-nothing operations
                       # Example: Transfer money - debit AND credit must both succeed

    autoflush=False,   # Don't auto-flush pending changes
                      # Gives us control over when changes are sent to database
                      # Improves performance by batching multiple operations

    bind=engine       # Connect this session factory to our engine
)


def get_db() -> Session:
    """
    Get database session (dependency injection for FastAPI)

    This is a "dependency" function used by FastAPI endpoints.
    It provides a database session to the endpoint, then automatically
    cleans it up when the request is done.

    How it works:
    1. Create a new database session
    2. Yield it to the endpoint (endpoint uses it)
    3. When endpoint is done, close the session (cleanup)

    Why use dependency injection?
    - Automatic cleanup (session always closed, even if endpoint crashes)
    - No connection leaks (every opened session is guaranteed to close)
    - Clean code (no try/finally blocks in every endpoint)

    Usage in FastAPI endpoint:
        @app.get("/transactions")
        def get_transactions(db: Session = Depends(get_db)):
            # db is automatically provided by FastAPI
            transactions = db.query(Transaction).all()
            return transactions
            # After this function returns, db is automatically closed

    Example flow:
        1. User makes request: GET /transactions
        2. FastAPI calls get_db()
        3. get_db() creates session from pool
        4. Session yielded to endpoint
        5. Endpoint uses db to query transactions
        6. Endpoint returns response
        7. get_db() automatically closes session
        8. Session returned to connection pool (reused for next request)

    Returns:
        Database session (SQLAlchemy Session object)

    Note:
        This is a generator function (uses 'yield' instead of 'return')
        FastAPI handles generator functions specially for dependency injection
    """
    # Create new session from the session factory
    # This gets a connection from the connection pool
    db = SessionLocal()

    try:
        # Yield the session to the endpoint
        # Everything after this line runs AFTER the endpoint completes
        yield db

    finally:
        # Cleanup: Close the session no matter what happens
        # This runs even if the endpoint raises an exception
        # Ensures no connection leaks
        db.close()

        # After closing, the connection is returned to the pool
        # It can be reused by the next request (efficient!)
