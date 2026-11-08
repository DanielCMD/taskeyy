"""
Database module for Taskeyy.

Handles PostgreSQL (Neon) database operations for storing
lists, tasks, and comments.

This module abstracts the database layer, providing a
simple interface for CRUD operations.
"""

import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables from the .env file.
load_dotenv()


# =============================================================
# Database class
# =============================================================

class TaskDatabase:
    """
    Manages the connection and operations with the Neon
    PostgreSQL database.

    Provides methods to:
        - Create the necessary tables (lists, tasks, comments).
        - Perform CRUD operations on lists, tasks, and comments.
        - Calculate dashboard statistics.
    """

    def __init__(self) -> None:
        """
        Initialize the database connection.

        Reads the DATABASE_URL from the environment variables
        and opens a connection to the Neon database.

        Raises:
            ValueError:
                If DATABASE_URL is not found in the .env file.
        """

        self.database_url = os.getenv("DATABASE_URL")

        if not self.database_url:

            raise ValueError(
                "DATABASE_URL not found in .env file"
            )

        self.conn = psycopg2.connect(
            self.database_url
        )

        self._create_tables()


    def _create_tables(self) -> None:
        """
        Create the tables (lists, tasks, comments) if they
        do not exist.

        Also creates a default list called 'Inbox' to ensure
        the user always has at least one list to add tasks to.
        """
        cursor = self.conn.cursor()

        # 1. Table: lists
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS lists (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                icon TEXT DEFAULT '📁',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Adiciona a coluna 'icon' se a tabela já existia (migração)
        try:
            cursor.execute("ALTER TABLE lists ADD COLUMN IF NOT EXISTS icon TEXT DEFAULT '📁'")
        except psycopg2.errors.DuplicateColumn:
            self.conn.rollback() # Se der erro, desfaz a transação e continua
        except Exception:
            self.conn.rollback()

        # 2. Table: tasks
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                list_id INTEGER REFERENCES lists(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'Backlog',
                priority TEXT DEFAULT 'Média',
                origin TEXT,
                origin_detail TEXT,
                date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_start DATE,
                date_planned DATE,
                date_real DATE
            )
            """
        )

        # 3. Table: comments
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS comments (
                id SERIAL PRIMARY KEY,
                task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Insert default list if empty
        cursor.execute("SELECT COUNT(*) FROM lists")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO lists (name) VALUES (%s)", 
                ("Inbox",)
            )

        self.conn.commit()


    # ---------------------------------------------------------
    # Lists Operations
    # ---------------------------------------------------------

    def get_lists(self) -> list[dict]:
        """
        Retrieve all lists.

        Returns:
            List of dictionaries containing list data.
        """
        
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT id, name, icon FROM lists ORDER BY name ASC")
        return [dict(row) for row in cursor.fetchall()]


    def create_list(self, name: str, icon: str = "📁") -> bool:
        """
        Create a new list.

        Args:
            name: The name of the list.
            icon: The emoji/icon for the list.

        Returns:
            True if created successfully, False otherwise.
        """
        cursor = self.conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO lists (name, icon) VALUES (%s, %s)", 
                (name, icon)
            )
            self.conn.commit()
            return True
        except psycopg2.IntegrityError:
            self.conn.rollback()
            return False


    # ---------------------------------------------------------
    # Tasks Operations
    # ---------------------------------------------------------

    def get_tasks_by_list(self, list_id: int) -> list[dict]:
        """
        Retrieve all tasks belonging to a specific list.

        Args:
            list_id:
                The ID of the list.

        Returns:
            List of dictionaries containing task data.
        """
        
        cursor = self.conn.cursor(
            cursor_factory=psycopg2.extras.DictCursor
        )
        
        cursor.execute(
            """
            SELECT * FROM tasks 
            WHERE list_id = %s 
            ORDER BY 
                CASE priority 
                    WHEN 'Crítico' THEN 1
                    WHEN 'Alta' THEN 2
                    WHEN 'Média' THEN 3
                    WHEN 'Baixa' THEN 4
                END ASC,
                date_created DESC
            """, 
            (list_id,)
        )
        
        return [dict(row) for row in cursor.fetchall()]


    def get_dashboard_stats(self) -> dict:
        """
        Calculate dashboard statistics for all tasks.

        Returns:
            Dictionary with counts for open tasks (total, today,
            overdue, week) and completed tasks (today, last 7 days).
        """
        
        cursor = self.conn.cursor()
        
        today = datetime.now().date()
        
        # Início e fim da semana atual (Segunda a Domingo)
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        # --- TAREFAS ABERTAS ---
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status != 'Feito'")
        total_open = cursor.fetchone()[0]
        
        cursor.execute(
            "SELECT COUNT(*) FROM tasks WHERE status != 'Feito' AND date_planned = %s",
            (today,)
        )
        today_count = cursor.fetchone()[0]
        
        cursor.execute(
            "SELECT COUNT(*) FROM tasks WHERE status != 'Feito' AND date_planned < %s",
            (today,)
        )
        overdue_count = cursor.fetchone()[0]
        
        cursor.execute(
            """
            SELECT COUNT(*) FROM tasks 
            WHERE status != 'Feito' 
            AND date_planned <= %s
            AND date_planned >= %s
            """,
            (end_of_week, start_of_week)
        )
        week_count = cursor.fetchone()[0]
        
        # --- TAREFAS CONCLUÍDAS (MÉTRICAS DE PRODUTIVIDADE) ---
        
        # Finalizadas hoje
        cursor.execute(
            "SELECT COUNT(*) FROM tasks WHERE status = 'Feito' AND date_real::date = %s",
            (today,)
        )
        done_today = cursor.fetchone()[0]
        
        # Finalizadas nos últimos 7 dias
        seven_days_ago = today - timedelta(days=7)
        cursor.execute(
            "SELECT COUNT(*) FROM tasks WHERE status = 'Feito' AND date_real::date >= %s",
            (seven_days_ago,)
        )
        done_last_7_days = cursor.fetchone()[0]
        
        return {
            "total_open": total_open,
            "today": today_count,
            "overdue": overdue_count,
            "week": week_count,
            "done_today": done_today,
            "done_last_7_days": done_last_7_days
        }

    def create_task(
        self,
        list_id: int,
        title: str,
        description: str = "",
        status: str = "Backlog",
        priority: str = "Média",
        origin: str = "",
        origin_detail: str = "",
        date_start: str = None,
        date_planned: str = None,
        date_real: str = None
    ) -> bool:
        """
        Create a new task in a specific list.
        """
        
        cursor = self.conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO tasks 
            (list_id, title, description, status, priority, origin, origin_detail, date_start, date_planned, date_real)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                list_id,
                title,
                description,
                status,
                priority,
                origin,
                origin_detail,
                date_start if date_start else None,
                date_planned if date_planned else None,
                date_real if date_real else None
            )
        )
        
        self.conn.commit()
        return True


    def update_task_status(self, task_id: int, new_status: str) -> None:
        """
        Update the status of a specific task.

        If the new status is 'Feito', automatically sets the
        'date_real' column to the current date and time.
        If the status is changed back from 'Feito', clears the
        'date_real' column.
        """
        
        cursor = self.conn.cursor()
        
        if new_status == "Feito":
            cursor.execute(
                """
                UPDATE tasks 
                SET status = %s, date_real = CURRENT_TIMESTAMP 
                WHERE id = %s
                """,
                (new_status, task_id)
            )
        else:
            cursor.execute(
                """
                UPDATE tasks 
                SET status = %s, date_real = NULL 
                WHERE id = %s
                """,
                (new_status, task_id)
            )
        
        self.conn.commit()


    def update_task_details(
        self,
        task_id: int,
        title: str,
        description: str,
        priority: str,
        status: str,
        origin: str,
        date_planned: str
    ) -> None:
        """
        Update the details of a specific task.
        """
        
        cursor = self.conn.cursor()
        
        cursor.execute(
            """
            UPDATE tasks 
            SET title = %s, 
                description = %s, 
                priority = %s, 
                status = %s, 
                origin = %s, 
                date_planned = %s
            WHERE id = %s
            """,
            (
                title,
                description,
                priority,
                status,
                origin,
                date_planned,
                task_id
            )
        )
        
        self.conn.commit()


    def delete_task(self, task_id: int) -> None:
        """
        Delete a specific task and its associated comments.
        """
        
        cursor = self.conn.cursor()
        
        cursor.execute(
            "DELETE FROM tasks WHERE id = %s",
            (task_id,)
        )
        
        self.conn.commit()


    # ---------------------------------------------------------
    # Comments Operations
    # ---------------------------------------------------------

    def get_comments_by_task(self, task_id: int) -> list[dict]:
        """
        Retrieve all comments for a specific task.
        """
        
        cursor = self.conn.cursor(
            cursor_factory=psycopg2.extras.DictCursor
        )
        
        cursor.execute(
            "SELECT id, content, created_at FROM comments WHERE task_id = %s ORDER BY created_at ASC",
            (task_id,)
        )
        
        return [dict(row) for row in cursor.fetchall()]


    def create_comment(self, task_id: int, content: str) -> None:
        """
        Add a new comment to a specific task.
        """
        
        cursor = self.conn.cursor()
        
        cursor.execute(
            "INSERT INTO comments (task_id, content) VALUES (%s, %s)",
            (task_id, content)
        )
        
        self.conn.commit()


    def close(self) -> None:
        """
        Close the database connection.
        """
        
        self.conn.close()