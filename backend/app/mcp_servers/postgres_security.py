from __future__ import annotations

import re
from dataclasses import dataclass


class SQLSecurityError(ValueError):
    """Raised when a SQL statement violates the read-only policy."""


BLOCKED_KEYWORDS = {
    "alter",
    "analyze",
    "attach",
    "call",
    "cluster",
    "comment",
    "copy",
    "create",
    "delete",
    "detach",
    "discard",
    "do",
    "drop",
    "execute",
    "grant",
    "insert",
    "listen",
    "load",
    "lock",
    "merge",
    "notify",
    "prepare",
    "refresh",
    "reindex",
    "reset",
    "revoke",
    "security",
    "set",
    "truncate",
    "unlisten",
    "update",
    "vacuum",
}

BLOCKED_FUNCTIONS = {
    "dblink",
    "dblink_connect",
    "lo_export",
    "lo_import",
    "pg_advisory_lock",
    "pg_cancel_backend",
    "pg_create_logical_replication_slot",
    "pg_drop_replication_slot",
    "pg_read_binary_file",
    "pg_read_file",
    "pg_reload_conf",
    "pg_rotate_logfile",
    "pg_sleep",
    "pg_stat_file",
    "pg_terminate_backend",
    "pg_write_file",
}

ALLOWED_START_KEYWORDS = {
    "select",
    "with",
    "values",
}

SAFE_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]{0,62}$"
)


@dataclass(frozen=True, slots=True)
class ValidatedSQL:
    statement: str
    normalized_statement: str


class ReadOnlySQLValidator:
    """
    Validate one read-only PostgreSQL statement.

    This validator is intentionally conservative. It accepts SELECT,
    WITH, and VALUES statements and rejects mutation, DDL, transaction
    control, file access, administrative functions, comments, and
    multiple statements.
    """

    @classmethod
    def validate_query(
        cls,
        sql: str,
    ) -> ValidatedSQL:
        statement = cls._normalize(
            sql,
        )

        cls._reject_comments(
            statement,
        )
        cls._reject_multiple_statements(
            statement,
        )

        normalized = cls._strip_quoted_content(
            statement,
        ).casefold()

        first_keyword_match = re.match(
            r"^\s*([a-z]+)",
            normalized,
        )

        if first_keyword_match is None:
            raise SQLSecurityError(
                "SQL statement is empty or invalid."
            )

        first_keyword = first_keyword_match.group(
            1,
        )

        if first_keyword not in ALLOWED_START_KEYWORDS:
            raise SQLSecurityError(
                "Only SELECT, WITH, or VALUES statements are allowed."
            )

        tokens = set(
            re.findall(
                r"\b[a-z_][a-z0-9_]*\b",
                normalized,
            )
        )

        blocked_tokens = sorted(
            tokens
            & BLOCKED_KEYWORDS
        )

        if blocked_tokens:
            raise SQLSecurityError(
                "Blocked SQL keyword detected: "
                + ", ".join(
                    blocked_tokens,
                )
            )

        blocked_functions = sorted(
            function_name
            for function_name in BLOCKED_FUNCTIONS
            if re.search(
                rf"\b{re.escape(function_name)}\s*\(",
                normalized,
            )
        )

        if blocked_functions:
            raise SQLSecurityError(
                "Blocked PostgreSQL function detected: "
                + ", ".join(
                    blocked_functions,
                )
            )

        if re.search(
            r"\binto\s+(?:temporary\s+|temp\s+)?table\b",
            normalized,
        ):
            raise SQLSecurityError(
                "SELECT INTO is not allowed."
            )

        if re.search(
            r"\bfor\s+(?:update|share|no\s+key\s+update|key\s+share)\b",
            normalized,
        ):
            raise SQLSecurityError(
                "Row-locking SELECT statements are not allowed."
            )

        return ValidatedSQL(
            statement=statement,
            normalized_statement=normalized,
        )

    @classmethod
    def validate_explain_query(
        cls,
        sql: str,
    ) -> ValidatedSQL:
        normalized_input = cls._normalize(
            sql,
        )

        if re.match(
            r"^\s*explain\b",
            normalized_input,
            flags=re.IGNORECASE,
        ):
            normalized_input = re.sub(
                r"^\s*explain"
                r"(?:\s*\([^)]*\))?"
                r"\s+",
                "",
                normalized_input,
                count=1,
                flags=re.IGNORECASE,
            )

        return cls.validate_query(
            normalized_input,
        )

    @staticmethod
    def validate_identifier(
        value: str,
        *,
        field_name: str,
    ) -> str:
        normalized = str(
            value
            or "",
        ).strip()

        if not SAFE_IDENTIFIER_PATTERN.fullmatch(
            normalized,
        ):
            raise SQLSecurityError(
                f"{field_name} contains an invalid PostgreSQL identifier."
            )

        return normalized

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:
        statement = str(
            value
            or "",
        ).strip()

        while statement.endswith(
            ";",
        ):
            statement = statement[:-1].rstrip()

        if not statement:
            raise SQLSecurityError(
                "SQL statement cannot be empty."
            )

        if len(statement) > 20_000:
            raise SQLSecurityError(
                "SQL statement exceeds the 20,000-character limit."
            )

        return statement

    @staticmethod
    def _reject_comments(
        statement: str,
    ) -> None:
        if (
            "--" in statement
            or "/*" in statement
            or "*/" in statement
        ):
            raise SQLSecurityError(
                "SQL comments are not allowed."
            )

    @classmethod
    def _reject_multiple_statements(
        cls,
        statement: str,
    ) -> None:
        unquoted = cls._strip_quoted_content(
            statement,
        )

        if ";" in unquoted:
            raise SQLSecurityError(
                "Multiple SQL statements are not allowed."
            )

    @staticmethod
    def _strip_quoted_content(
        statement: str,
    ) -> str:
        output: list[str] = []
        index = 0
        quote: str | None = None

        while index < len(
            statement,
        ):
            character = statement[
                index
            ]

            if quote is None:
                if character in {
                    "'",
                    '"',
                }:
                    quote = character
                    output.append(
                        " ",
                    )
                else:
                    output.append(
                        character,
                    )

                index += 1
                continue

            if character == quote:
                if (
                    index + 1
                    < len(statement)
                    and statement[
                        index + 1
                    ]
                    == quote
                ):
                    index += 2
                    continue

                quote = None

            output.append(
                " ",
            )
            index += 1

        if quote is not None:
            raise SQLSecurityError(
                "Unterminated SQL string or identifier."
            )

        return "".join(
            output,
        )
