from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.services.unified_tool_service import (
    UnifiedToolNotFoundError,
    UnifiedToolService,
)


@dataclass(frozen=True, slots=True)
class MCPToolIntent:
    qualified_name: str
    arguments: dict[str, Any]
    matched_signal: str


FILESYSTEM_SERVER = "redpa-filesystem"
GITHUB_SERVER = "redpa-github"
POSTGRES_SERVER = "redpa-postgres"
DOCKER_SERVER = "redpa-docker"

FILESYSTEM_TOOLS = {
    "list_files": (
        f"mcp:{FILESYSTEM_SERVER}:list_files"
    ),
    "read_file": (
        f"mcp:{FILESYSTEM_SERVER}:read_file"
    ),
    "search_files": (
        f"mcp:{FILESYSTEM_SERVER}:search_files"
    ),
    "file_info": (
        f"mcp:{FILESYSTEM_SERVER}:file_info"
    ),
}


GITHUB_TOOLS = {
    "repository": (
        f"mcp:{GITHUB_SERVER}:repository"
    ),
    "branches": (
        f"mcp:{GITHUB_SERVER}:branches"
    ),
    "commits": (
        f"mcp:{GITHUB_SERVER}:commits"
    ),
    "issues": (
        f"mcp:{GITHUB_SERVER}:issues"
    ),
    "pull_requests": (
        f"mcp:{GITHUB_SERVER}:pull_requests"
    ),
}


POSTGRES_TOOLS = {
    "list_schemas": (
        f"mcp:{POSTGRES_SERVER}:list_schemas"
    ),
    "list_tables": (
        f"mcp:{POSTGRES_SERVER}:list_tables"
    ),
    "describe_table": (
        f"mcp:{POSTGRES_SERVER}:describe_table"
    ),
    "query": (
        f"mcp:{POSTGRES_SERVER}:query"
    ),
    "explain": (
        f"mcp:{POSTGRES_SERVER}:explain"
    ),
}


DOCKER_TOOLS = {
    "list_containers": (
        f"mcp:{DOCKER_SERVER}:list_containers"
    ),
    "inspect_container": (
        f"mcp:{DOCKER_SERVER}:inspect_container"
    ),
    "container_logs": (
        f"mcp:{DOCKER_SERVER}:container_logs"
    ),
    "list_images": (
        f"mcp:{DOCKER_SERVER}:list_images"
    ),
    "system_info": (
        f"mcp:{DOCKER_SERVER}:system_info"
    ),
}


async def detect_available_mcp_tool_intent(
    text: str,
) -> MCPToolIntent | None:
    """
    Detect an MCP request and verify that the selected tool exists in
    the current unified catalog before returning it to the planner.
    """

    intent = detect_mcp_tool_intent(
        text,
    )

    if intent is None:
        return None

    try:
        await UnifiedToolService.get_tool(
            qualified_name=intent.qualified_name,
        )
    except UnifiedToolNotFoundError:
        refreshed_catalog = (
            await UnifiedToolService.refresh_catalog()
        )

        if not any(
            item.qualified_name.casefold()
            == intent.qualified_name.casefold()
            for item in refreshed_catalog.items
        ):
            return None

    return intent


def detect_mcp_tool_intent(
    text: str,
) -> MCPToolIntent | None:
    cleaned_text = str(
        text
        or ""
    ).strip()

    if not cleaned_text:
        return None

    docker_intent = _detect_docker_intent(
        cleaned_text,
    )

    if docker_intent is not None:
        return docker_intent

    postgres_intent = _detect_postgres_intent(
        cleaned_text,
    )

    if postgres_intent is not None:
        return postgres_intent

    github_intent = _detect_github_intent(
        cleaned_text,
    )

    if github_intent is not None:
        return github_intent

    search_intent = _detect_search_intent(
        cleaned_text,
    )

    if search_intent is not None:
        return search_intent

    file_info_intent = _detect_file_info_intent(
        cleaned_text,
    )

    if file_info_intent is not None:
        return file_info_intent

    read_intent = _detect_read_intent(
        cleaned_text,
    )

    if read_intent is not None:
        return read_intent

    return _detect_list_intent(
        cleaned_text,
    )





def _detect_docker_intent(
    text: str,
) -> MCPToolIntent | None:
    lowered = text.casefold()

    if re.search(
        r"\b(?:docker\s+)?(?:system|engine)\s+info(?:rmation)?\b",
        lowered,
    ) or re.search(
        r"\bshow\s+docker\s+info(?:rmation)?\b",
        lowered,
    ):
        return MCPToolIntent(
            qualified_name=DOCKER_TOOLS[
                "system_info"
            ],
            arguments={},
            matched_signal="docker system info request",
        )

    if re.search(
        r"\b(?:list|show|display)\s+"
        r"(?:the\s+)?(?:docker\s+)?images\b",
        lowered,
    ):
        return MCPToolIntent(
            qualified_name=DOCKER_TOOLS[
                "list_images"
            ],
            arguments={
                "all_images": bool(
                    re.search(
                        r"\ball\s+(?:docker\s+)?images\b",
                        lowered,
                    )
                ),
            },
            matched_signal="docker image list request",
        )

    logs_match = re.search(
        r"\b(?:show|display|get|read|tail)\s+"
        r"(?:the\s+)?"
        r"(?:(?:last|latest|tail)\s+\d{1,4}\s+)?"
        r"(?:docker\s+)?logs?\s+"
        r"(?:for|of|from)\s+"
        r"(?P<container>[A-Za-z0-9][A-Za-z0-9_.-]{0,127})",
        text,
        flags=re.IGNORECASE,
    )

    if logs_match is not None:
        return MCPToolIntent(
            qualified_name=DOCKER_TOOLS[
                "container_logs"
            ],
            arguments={
                "container": logs_match.group(
                    "container",
                ),
                "tail": _extract_docker_log_tail(
                    text,
                ),
                "timestamps": True,
            },
            matched_signal="docker container logs request",
        )

    inspect_match = re.search(
        r"\b(?:inspect|describe|show\s+(?:the\s+)?details\s+(?:for|of))\s+"
        r"(?:container\s+)?"
        r"(?P<container>[A-Za-z0-9][A-Za-z0-9_.-]{0,127})",
        text,
        flags=re.IGNORECASE,
    )

    if inspect_match is not None and (
        "docker" in lowered
        or "container" in lowered
        or lowered.startswith(
            "inspect "
        )
    ):
        return MCPToolIntent(
            qualified_name=DOCKER_TOOLS[
                "inspect_container"
            ],
            arguments={
                "container": inspect_match.group(
                    "container",
                ),
            },
            matched_signal="docker container inspect request",
        )

    if re.search(
        r"\b(?:list|show|display)\s+"
        r"(?:the\s+)?"
        r"(?:(?:running|active|all)\s+)?"
        r"(?:docker\s+)?containers\b",
        lowered,
    ):
        running_only = bool(
            re.search(
                r"\b(?:running|active)\s+(?:docker\s+)?containers\b",
                lowered,
            )
        )

        return MCPToolIntent(
            qualified_name=DOCKER_TOOLS[
                "list_containers"
            ],
            arguments={
                "all_containers": not running_only,
            },
            matched_signal="docker container list request",
        )

    return None


def _extract_docker_log_tail(
    text: str,
) -> int:
    patterns = (
        r"\b(?:last|latest|tail)\s+(?P<tail>\d{1,4})\b",
        r"\b(?P<tail>\d{1,4})\s+(?:log\s+)?lines?\b",
    )

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match is None:
            continue

        return max(
            1,
            min(
                int(
                    match.group(
                        "tail",
                    )
                ),
                2_000,
            ),
        )

    return 100


def _detect_postgres_intent(
    text: str,
) -> MCPToolIntent | None:
    lowered = text.casefold()

    if re.search(
        r"\b(?:explain|query\s+plan|execution\s+plan)\b",
        lowered,
    ):
        sql = _extract_sql_statement(
            text,
        )

        if sql is None:
            return None

        return MCPToolIntent(
            qualified_name=POSTGRES_TOOLS[
                "explain"
            ],
            arguments={
                "sql": sql,
            },
            matched_signal="postgres explain request",
        )

    if re.search(
        r"\b(?:run|execute|query)\b",
        lowered,
    ):
        sql = _extract_sql_statement(
            text,
        )

        if sql is not None:
            return MCPToolIntent(
                qualified_name=POSTGRES_TOOLS[
                    "query"
                ],
                arguments={
                    "sql": sql,
                    "max_rows": _extract_database_row_limit(
                        text,
                        default=100,
                    ),
                },
                matched_signal="postgres query request",
            )

    describe_match = re.search(
        r"\b(?:describe|inspect|show\s+(?:the\s+)?structure\s+of|"
        r"show\s+(?:the\s+)?schema\s+of|columns\s+of)\s+"
        r"(?:table\s+)?"
        r"(?P<table>[A-Za-z_][A-Za-z0-9_]{0,62})"
        r"(?:\s+(?:in|from)\s+(?:schema\s+)?"
        r"(?P<schema>[A-Za-z_][A-Za-z0-9_]{0,62}))?"
        r"\s*[?.!]*$",
        text,
        flags=re.IGNORECASE,
    )

    if describe_match is not None:
        return MCPToolIntent(
            qualified_name=POSTGRES_TOOLS[
                "describe_table"
            ],
            arguments={
                "table": describe_match.group(
                    "table",
                ),
                "schema": (
                    describe_match.group(
                        "schema",
                    )
                    or "public"
                ),
            },
            matched_signal="postgres describe table request",
        )

    tables_match = re.search(
        r"\b(?:list|show|display|what\s+are)\s+"
        r"(?:the\s+)?(?:database\s+)?"
        r"(?:tables|views)"
        r"(?:\s+(?:in|inside|from)\s+(?:schema\s+)?"
        r"(?P<schema>[A-Za-z_][A-Za-z0-9_]{0,62}))?"
        r"\s*[?.!]*$",
        text,
        flags=re.IGNORECASE,
    )

    if tables_match is not None:
        return MCPToolIntent(
            qualified_name=POSTGRES_TOOLS[
                "list_tables"
            ],
            arguments={
                "schema": (
                    tables_match.group(
                        "schema",
                    )
                    or "public"
                ),
            },
            matched_signal="postgres list tables request",
        )

    if re.search(
        r"\b(?:list|show|display|what\s+are)\s+"
        r"(?:the\s+)?(?:database\s+)?schemas\b",
        text,
        flags=re.IGNORECASE,
    ):
        return MCPToolIntent(
            qualified_name=POSTGRES_TOOLS[
                "list_schemas"
            ],
            arguments={},
            matched_signal="postgres list schemas request",
        )

    count_match = re.search(
        r"\b(?:how\s+many|count)\s+"
        r"(?P<table>[A-Za-z_][A-Za-z0-9_]{0,62})"
        r"(?:\s+(?:are\s+)?(?:in|inside|stored\s+in)\s+"
        r"(?:the\s+)?database)?\s*[?.!]*$",
        text,
        flags=re.IGNORECASE,
    )

    if count_match is not None:
        table = count_match.group(
            "table",
        )

        if table.casefold() not in {
            "tables",
            "schemas",
            "columns",
        }:
            return MCPToolIntent(
                qualified_name=POSTGRES_TOOLS[
                    "query"
                ],
                arguments={
                    "sql": (
                        f'SELECT COUNT(*) AS count FROM "{table}"'
                    ),
                    "max_rows": 10,
                },
                matched_signal="postgres count request",
            )

    return None


def _extract_sql_statement(
    text: str,
) -> str | None:
    fenced_match = re.search(
        r"```(?:sql)?\s*(?P<sql>.+?)```",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if fenced_match is not None:
        sql = fenced_match.group(
            "sql",
        ).strip()

        return sql or None

    inline_match = re.search(
        r"\b(?P<sql>(?:SELECT|WITH|VALUES)\b.+)$",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if inline_match is None:
        return None

    sql = inline_match.group(
        "sql",
    ).strip()

    return sql or None


def _extract_database_row_limit(
    text: str,
    *,
    default: int,
) -> int:
    match = re.search(
        r"\b(?:limit|max(?:imum)?\s+rows?|first|top)\s+"
        r"(?P<limit>\d{1,4})\b",
        text,
        flags=re.IGNORECASE,
    )

    if match is None:
        return default

    return max(
        1,
        min(
            int(
                match.group(
                    "limit",
                )
            ),
            200,
        ),
    )


def _detect_github_intent(
    text: str,
) -> MCPToolIntent | None:
    repository = _extract_repository_name(
        text,
    )

    if repository is None:
        return None

    lowered = text.casefold()

    if re.search(
        r"\b(pull\s+requests?|prs?)\b",
        lowered,
    ):
        state = _extract_github_state(
            lowered,
        )

        return MCPToolIntent(
            qualified_name=GITHUB_TOOLS[
                "pull_requests"
            ],
            arguments={
                "repository": repository,
                "state": state,
                "limit": _extract_limit(
                    text,
                    default=20,
                ),
            },
            matched_signal="github pull request request",
        )

    if re.search(
        r"\bissues?\b",
        lowered,
    ):
        state = _extract_github_state(
            lowered,
        )

        return MCPToolIntent(
            qualified_name=GITHUB_TOOLS[
                "issues"
            ],
            arguments={
                "repository": repository,
                "state": state,
                "limit": _extract_limit(
                    text,
                    default=20,
                ),
            },
            matched_signal="github issue request",
        )

    if re.search(
        r"\bcommits?\b",
        lowered,
    ):
        branch = _extract_branch(
            text,
        )

        arguments: dict[str, Any] = {
            "repository": repository,
            "limit": _extract_limit(
                text,
                default=10,
            ),
        }

        if branch is not None:
            arguments["branch"] = branch

        return MCPToolIntent(
            qualified_name=GITHUB_TOOLS[
                "commits"
            ],
            arguments=arguments,
            matched_signal="github commit request",
        )

    if re.search(
        r"\bbranches?\b",
        lowered,
    ):
        return MCPToolIntent(
            qualified_name=GITHUB_TOOLS[
                "branches"
            ],
            arguments={
                "repository": repository,
                "limit": _extract_limit(
                    text,
                    default=20,
                ),
            },
            matched_signal="github branch request",
        )

    if re.search(
        r"\b(repository|repo|github)\b",
        lowered,
    ):
        return MCPToolIntent(
            qualified_name=GITHUB_TOOLS[
                "repository"
            ],
            arguments={
                "repository": repository,
            },
            matched_signal="github repository request",
        )

    return None


def _extract_repository_name(
    text: str,
) -> str | None:
    url_match = re.search(
        r"https?://github\.com/"
        r"(?P<owner>[A-Za-z0-9_.-]{1,100})/"
        r"(?P<name>[A-Za-z0-9_.-]{1,100})",
        text,
        flags=re.IGNORECASE,
    )

    if url_match is not None:
        return (
            f"{url_match.group('owner')}/"
            f"{url_match.group('name').rstrip('.,?!')}"
        )

    repository_match = re.search(
        r"(?<![A-Za-z0-9_.-])"
        r"(?P<owner>[A-Za-z0-9_.-]{1,100})/"
        r"(?P<name>[A-Za-z0-9_.-]{1,100})"
        r"(?![A-Za-z0-9_.-])",
        text,
    )

    if repository_match is None:
        return None

    return (
        f"{repository_match.group('owner')}/"
        f"{repository_match.group('name').rstrip('.,?!')}"
    )


def _extract_github_state(
    lowered_text: str,
) -> str:
    if re.search(
        r"\b(closed|resolved|merged)\b",
        lowered_text,
    ):
        return "closed"

    if re.search(
        r"\b(all|every)\b",
        lowered_text,
    ):
        return "all"

    return "open"


def _extract_limit(
    text: str,
    *,
    default: int,
) -> int:
    patterns = (
        r"\b(?:latest|recent|last|top|first)\s+"
        r"(?P<limit>\d{1,3})\b",
        r"\blimit\s+(?P<limit>\d{1,3})\b",
        r"\b(?P<limit>\d{1,3})\s+"
        r"(?:(?:open|closed|all)\s+)?"
        r"(?:commits?|issues?|branches?|pull\s+requests?|prs?)\b",
    )

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match is None:
            continue

        return max(
            1,
            min(
                int(
                    match.group(
                        "limit",
                    )
                ),
                100,
            ),
        )

    return default


def _extract_branch(
    text: str,
) -> str | None:
    match = re.search(
        r"\b(?:branch|on)\s+"
        r"(?P<branch>[A-Za-z0-9_./-]{1,200})",
        text,
        flags=re.IGNORECASE,
    )

    if match is None:
        return None

    branch = match.group(
        "branch",
    ).rstrip(
        ".,?!"
    )

    if branch.casefold() in {
        "the",
        "a",
        "an",
    }:
        return None

    return branch


def _detect_list_intent(
    text: str,
) -> MCPToolIntent | None:
    patterns = (
        r"\b(?:list|show|display|find)\s+"
        r"(?:me\s+)?(?:the\s+)?"
        r"(?:files|directories|folders|contents|entries)"
        r"(?:\s+(?:in|inside|under|from|of)\s+|\s+)"
        r"(?P<path>.+?)\s*[?.!]*$",
        r"\bwhat\s+(?:files|directories|folders)"
        r"\s+(?:are\s+)?(?:in|inside|under)\s+"
        r"(?P<path>.+?)\s*[?.!]*$",
        r"^\s*(?:ls|dir)\s+(?P<path>.+?)\s*$",
    )

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match is None:
            continue

        path = _normalize_project_path(
            match.group(
                "path",
            )
        )

        if path is None:
            continue

        recursive = bool(
            re.search(
                r"\b(recursive|recursively|all\s+subfolders|"
                r"all\s+subdirectories)\b",
                text,
                flags=re.IGNORECASE,
            )
        )

        return MCPToolIntent(
            qualified_name=FILESYSTEM_TOOLS[
                "list_files"
            ],
            arguments={
                "path": path,
                "recursive": recursive,
                "max_entries": 100,
            },
            matched_signal="filesystem list request",
        )

    return None


def _detect_read_intent(
    text: str,
) -> MCPToolIntent | None:
    patterns = (
        r"\b(?:read|open|show|display|print)\s+"
        r"(?:me\s+)?(?:the\s+)?"
        r"(?:file\s+)?(?P<path>"
        r"(?:backend|docs)/[^\s?]+|README\.md)"
        r"\s*[?.!]*$",
        r"\b(?:content|contents)\s+of\s+"
        r"(?P<path>(?:backend|docs)/[^\s?]+|README\.md)"
        r"\s*[?.!]*$",
        r"\bwhat(?:'s|\s+is)\s+in\s+"
        r"(?P<path>(?:backend|docs)/[^\s?]+|README\.md)"
        r"\s*[?.!]*$",
    )

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match is None:
            continue

        path = _normalize_project_path(
            match.group(
                "path",
            )
        )

        if path is None:
            continue

        return MCPToolIntent(
            qualified_name=FILESYSTEM_TOOLS[
                "read_file"
            ],
            arguments={
                "path": path,
                "max_characters": 20_000,
            },
            matched_signal="filesystem read request",
        )

    return None


def _detect_search_intent(
    text: str,
) -> MCPToolIntent | None:
    patterns = (
        r"\b(?:search|find)\s+(?:for\s+)?"
        r"(?:the\s+)?(?:text|string|term|code)?\s*"
        r"[\"']?(?P<query>.+?)[\"']?\s+"
        r"(?:in|inside|under|within)\s+"
        r"(?P<path>backend(?:/[^\s?]+)?|docs(?:/[^\s?]+)?)"
        r"\s*[?.!]*$",
        r"\blook\s+for\s+"
        r"(?:the\s+)?(?:text|string|term|code)?\s*"
        r"[\"']?(?P<query>.+?)[\"']?\s+"
        r"(?:in|inside|under|within)\s+"
        r"(?P<path>backend(?:/[^\s?]+)?|docs(?:/[^\s?]+)?)"
        r"\s*[?.!]*$",
        r"\bwhere\s+is\s+[\"']?(?P<query>.+?)[\"']?"
        r"\s+(?:used|defined|mentioned)\s+"
        r"(?:in|inside|under)\s+"
        r"(?P<path>backend(?:/[^\s?]+)?|docs(?:/[^\s?]+)?)"
        r"\s*[?.!]*$",
    )

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match is None:
            continue

        query = str(
            match.group(
                "query",
            )
        ).strip(
            " \"'?.!"
        )

        path = _normalize_project_path(
            match.group(
                "path",
            )
        )

        if not query or path is None:
            continue

        file_pattern = (
            "*.py"
            if path.startswith(
                "backend"
            )
            else "*"
        )

        return MCPToolIntent(
            qualified_name=FILESYSTEM_TOOLS[
                "search_files"
            ],
            arguments={
                "query": query,
                "path": path,
                "file_pattern": file_pattern,
                "case_sensitive": False,
                "max_results": 50,
            },
            matched_signal="filesystem search request",
        )

    return None


def _detect_file_info_intent(
    text: str,
) -> MCPToolIntent | None:
    match = re.search(
        r"\b(?:file\s+info|file\s+information|metadata|"
        r"details|size|modified\s+time)\s+"
        r"(?:for|of|about)?\s*"
        r"(?P<path>(?:backend|docs)/[^\s?]+|README\.md)"
        r"\s*[?.!]*$",
        text,
        flags=re.IGNORECASE,
    )

    if match is None:
        return None

    path = _normalize_project_path(
        match.group(
            "path",
        )
    )

    if path is None:
        return None

    return MCPToolIntent(
        qualified_name=FILESYSTEM_TOOLS[
            "file_info"
        ],
        arguments={
            "path": path,
        },
        matched_signal="filesystem metadata request",
    )


def _normalize_project_path(
    value: str,
) -> str | None:
    path = str(
        value
        or ""
    ).strip(
        " \t\r\n\"'?.!"
    )

    path = path.replace(
        "\\",
        "/",
    )

    while path.startswith(
        "./",
    ):
        path = path[2:]

    if not path:
        return ""

    if path.casefold() == "readme.md":
        return "README.md"

    allowed_prefixes = (
        "backend",
        "docs",
    )

    if path.casefold() in allowed_prefixes:
        return path.casefold()

    for prefix in allowed_prefixes:
        prefix_with_separator = (
            prefix
            + "/"
        )

        if path.casefold().startswith(
            prefix_with_separator,
        ):
            return (
                prefix
                + path[
                    len(prefix):
                ]
            )

    return None
