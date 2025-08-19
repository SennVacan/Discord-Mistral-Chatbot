"""
Database Module for Safi AI Bot

This module handles all database operations for storing and retrieving
message history and other bot data.
"""

import aiosqlite
import json
import logging
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

from constants import DB_FILE, MESSAGE_RETENTION_LIMIT

# Global connection (simplified approach)
_db_connection: Optional[aiosqlite.Connection] = None

async def init_db() -> None:
    """
    Initialize the database connection and ensure proper table structure.

    This function:
    1. Creates a database connection
    2. Checks if required columns exist
    3. Updates table structure if needed
    4. Creates the messages table if it doesn't exist
    """
    global _db_connection
    try:
        _db_connection = await aiosqlite.connect(DB_FILE)

        # Check if columns exist and add them if they don't
        cursor = await _db_connection.execute("PRAGMA table_info(messages)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'message_id' not in column_names or 'reference_id' not in column_names:
            # Create a backup table with the new structure
            await _db_connection.execute('''
                CREATE TABLE IF NOT EXISTS messages_new (
                    channel_id TEXT,
                    user_id TEXT,
                    content TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    message_id TEXT,
                    reference_id TEXT
                )
            ''')

            # Copy data from old table
            await _db_connection.execute('''
                INSERT INTO messages_new (channel_id, user_id, content, timestamp)
                SELECT channel_id, user_id, content, timestamp FROM messages
            ''')

            # Drop old table and rename new one
            await _db_connection.execute('DROP TABLE IF EXISTS messages')
            await _db_connection.execute('ALTER TABLE messages_new RENAME TO messages')

        # Create table if it doesn't exist (with all columns)
        await _db_connection.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                channel_id TEXT,
                user_id TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                message_id TEXT,
                reference_id TEXT
            )
        ''')
        await _db_connection.commit()
        logging.info("Database initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing database: {str(e)}")
        raise

async def get_db_connection() -> aiosqlite.Connection:
    """
    Get the database connection, creating a new one if needed.

    Returns:
        aiosqlite.Connection: Database connection object

    Raises:
        Exception: If database connection cannot be established
    """
    global _db_connection
    if _db_connection is None:
        await init_db()
    if _db_connection is None:  # Double check after init
        raise Exception("Failed to initialize database connection")
    return _db_connection

async def add_message(
    channel_id: str,
    user_id: str,
    content: str,
    message_id: Optional[str] = None,
    reference_id: Optional[str] = None
) -> None:
    """
    Add a message to the database and enforce retention limits.

    Args:
        channel_id: ID of the channel where the message was sent
        user_id: ID of the user who sent the message
        content: Content of the message
        message_id: Optional ID of the message
        reference_id: Optional ID of the message this replies to
    """
    try:
        db = await get_db_connection()
        await db.execute(
            "INSERT INTO messages (channel_id, user_id, content, message_id, reference_id) "
            "VALUES (?, ?, ?, ?, ?)",
            (channel_id, user_id, content, message_id, reference_id)
        )

        # Keep only the configured number of messages per channel
        await db.execute(
            "DELETE FROM messages WHERE channel_id = ? AND rowid NOT IN "
            "(SELECT rowid FROM messages WHERE channel_id = ? "
            "ORDER BY timestamp DESC LIMIT ?)",
            (channel_id, channel_id, MESSAGE_RETENTION_LIMIT)
        )
        await db.commit()
    except Exception as e:
        logging.error(f"Error adding message to database: {str(e)}")
        raise

async def get_last_messages(channel_id: str, limit: int = 7):
    """
    Retrieve the most recent messages from a channel.

    Args:
        channel_id: ID of the channel to get messages from
        limit: Maximum number of messages to retrieve

    Returns:
        List of message tuples (user_id, content, message_id, reference_id)
    """
    try:
        db = await get_db_connection()
        cursor = await db.execute("""
            SELECT user_id, content, message_id, reference_id
            FROM messages
            WHERE channel_id = ?
            ORDER BY timestamp ASC
            LIMIT ?
        """, (channel_id, limit))
        return await cursor.fetchall()
    except Exception as e:
        logging.error(f"Error retrieving messages from database: {str(e)}")
        raise

async def close_db() -> None:
    """Close the database connection if it exists."""
    global _db_connection
    if _db_connection:
        await _db_connection.close()
        _db_connection = None
        logging.info("Database connection closed")