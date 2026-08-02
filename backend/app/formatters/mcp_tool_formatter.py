from __future__ import annotations

from typing import Any


def format_mcp_tool_response(
    *,
    qualified_name: str,
    success: bool,
    structured_content: Any,
    content: list[dict[str, Any]],
    error: str | None,
) -> str:
    if not success:
        message = (
            error
            or _first_text_content(
                content,
            )
            or "The MCP tool could not complete the request."
        )

        return (
            f"MCP tool `{qualified_name}` failed: {message}"
        )

    tool_name = qualified_name.rsplit(
        ":",
        1,
    )[-1]

    if tool_name == "list_files":
        return _format_file_list(
            structured_content,
        )

    if tool_name == "read_file":
        return _format_read_file(
            structured_content,
        )

    if tool_name == "search_files":
        return _format_search_results(
            structured_content,
        )

    if tool_name == "file_info":
        return _format_file_info(
            structured_content,
        )

    if tool_name == "repository":
        return _format_github_repository(
            structured_content,
        )

    if tool_name == "branches":
        return _format_github_branches(
            structured_content,
        )

    if tool_name == "commits":
        return _format_github_commits(
            structured_content,
        )

    if tool_name == "issues":
        return _format_github_issues(
            structured_content,
        )

    if tool_name == "pull_requests":
        return _format_github_pull_requests(
            structured_content,
        )

    if tool_name == "list_schemas":
        return _format_postgres_schemas(
            structured_content,
        )

    if tool_name == "list_tables":
        return _format_postgres_tables(
            structured_content,
        )

    if tool_name == "describe_table":
        return _format_postgres_table_description(
            structured_content,
        )

    if tool_name == "query":
        return _format_postgres_query(
            structured_content,
        )

    if tool_name == "explain":
        return _format_postgres_explain(
            structured_content,
        )

    if tool_name == "list_containers":
        return _format_docker_containers(
            structured_content,
        )

    if tool_name == "inspect_container":
        return _format_docker_container_inspect(
            structured_content,
        )

    if tool_name == "container_logs":
        return _format_docker_logs(
            structured_content,
        )

    if tool_name == "list_images":
        return _format_docker_images(
            structured_content,
        )

    if tool_name == "system_info":
        return _format_docker_system_info(
            structured_content,
        )

    text_content = _first_text_content(
        content,
    )

    if text_content:
        return text_content

    return (
        f"MCP tool `{qualified_name}` completed successfully."
    )


def _format_file_list(
    result: Any,
) -> str:
    if not isinstance(
        result,
        dict,
    ):
        return "The filesystem listing completed successfully."

    entries = result.get(
        "entries",
        [],
    )

    if not isinstance(
        entries,
        list,
    ) or not entries:
        return (
            f"No visible files were found in "
            f"`{result.get('path', '.')}`."
        )

    lines = [
        f"Files in `{result.get('path', '.')}`:",
        "",
    ]

    for entry in entries:
        if not isinstance(
            entry,
            dict,
        ):
            continue

        entry_type = entry.get(
            "type",
            "file",
        )

        marker = (
            "📁"
            if entry_type == "directory"
            else "📄"
        )

        lines.append(
            f"- {marker} `{entry.get('path', entry.get('name', 'unknown'))}`"
        )

    if result.get(
        "truncated",
        False,
    ):
        lines.extend(
            [
                "",
                "The result was truncated.",
            ]
        )

    return "\n".join(
        lines,
    )


def _format_read_file(
    result: Any,
) -> str:
    if not isinstance(
        result,
        dict,
    ):
        return "The file was read successfully."

    path = result.get(
        "path",
        "file",
    )

    content = str(
        result.get(
            "content",
            "",
        )
        or ""
    )

    if not content:
        return (
            f"`{path}` is empty or contains no readable text."
        )

    suffix = str(
        path,
    ).rsplit(
        ".",
        1,
    )[-1].casefold()

    language = {
        "py": "python",
        "json": "json",
        "yml": "yaml",
        "yaml": "yaml",
        "md": "markdown",
        "sql": "sql",
        "toml": "toml",
    }.get(
        suffix,
        "text",
    )

    lines = [
        f"Contents of `{path}`:",
        "",
        f"```{language}",
        content,
        "```",
    ]

    if result.get(
        "truncated",
        False,
    ):
        lines.extend(
            [
                "",
                (
                    "The displayed content was truncated "
                    f"({result.get('characters_returned', 0)} of "
                    f"{result.get('total_characters', 0)} characters)."
                ),
            ]
        )

    return "\n".join(
        lines,
    )


def _format_search_results(
    result: Any,
) -> str:
    if not isinstance(
        result,
        dict,
    ):
        return "The filesystem search completed successfully."

    matches = result.get(
        "matches",
        [],
    )

    query = result.get(
        "query",
        "",
    )

    if not isinstance(
        matches,
        list,
    ) or not matches:
        return (
            f"No matches were found for `{query}` "
            f"inside `{result.get('path', '.')}`."
        )

    lines = [
        (
            f"Matches for `{query}` inside "
            f"`{result.get('path', '.')}`:"
        ),
        "",
    ]

    for match in matches:
        if not isinstance(
            match,
            dict,
        ):
            continue

        lines.append(
            "- "
            f"`{match.get('path', 'unknown')}:{match.get('line_number', '?')}` "
            f"— {match.get('excerpt', '')}"
        )

    if result.get(
        "truncated",
        False,
    ):
        lines.extend(
            [
                "",
                "The result was truncated.",
            ]
        )

    return "\n".join(
        lines,
    )


def _format_file_info(
    result: Any,
) -> str:
    if not isinstance(
        result,
        dict,
    ):
        return "File metadata was retrieved successfully."

    return "\n".join(
        [
            f"Information for `{result.get('path', 'unknown')}`:",
            "",
            f"- Type: {result.get('type', 'unknown')}",
            f"- Size: {result.get('size_bytes', 'n/a')} bytes",
            f"- Extension: {result.get('extension') or 'none'}",
            f"- Modified: {result.get('modified_at', 'unknown')}",
            f"- Read-only: {result.get('read_only', True)}",
        ]
    )



def _format_github_repository(
    result: Any,
) -> str:
    if not isinstance(
        result,
        dict,
    ):
        return "GitHub repository metadata was retrieved successfully."

    repository = result.get(
        "repository",
        "unknown",
    )

    lines = [
        f"GitHub repository: `{repository}`",
        "",
    ]

    description = result.get(
        "description",
    )

    if description:
        lines.extend(
            [
                str(
                    description,
                ),
                "",
            ]
        )

    lines.extend(
        [
            f"- Language: {result.get('language') or 'unknown'}",
            f"- Stars: {result.get('stars', 0)}",
            f"- Forks: {result.get('forks', 0)}",
            f"- Open issues: {result.get('open_issues', 0)}",
            f"- Default branch: {result.get('default_branch') or 'unknown'}",
            f"- License: {result.get('license') or 'unknown'}",
            f"- Archived: {result.get('archived', False)}",
        ]
    )

    html_url = result.get(
        "html_url",
    )

    if html_url:
        lines.extend(
            [
                "",
                str(
                    html_url,
                ),
            ]
        )

    return "\n".join(
        lines,
    )


def _format_github_branches(
    result: Any,
) -> str:
    if not isinstance(
        result,
        dict,
    ):
        return "GitHub branches were retrieved successfully."

    repository = result.get(
        "repository",
        "unknown",
    )

    branches = result.get(
        "branches",
        [],
    )

    if not isinstance(
        branches,
        list,
    ) or not branches:
        return (
            f"No branches were returned for `{repository}`."
        )

    lines = [
        f"Branches for `{repository}`:",
        "",
    ]

    for branch in branches:
        if not isinstance(
            branch,
            dict,
        ):
            continue

        protected = (
            "protected"
            if branch.get(
                "protected",
                False,
            )
            else "not protected"
        )

        lines.append(
            f"- `{branch.get('name', 'unknown')}` "
            f"({protected}) — "
            f"`{str(branch.get('commit_sha') or '')[:12]}`"
        )

    return "\n".join(
        lines,
    )


def _format_github_commits(
    result: Any,
) -> str:
    if not isinstance(
        result,
        dict,
    ):
        return "GitHub commits were retrieved successfully."

    repository = result.get(
        "repository",
        "unknown",
    )

    commits = result.get(
        "commits",
        [],
    )

    if not isinstance(
        commits,
        list,
    ) or not commits:
        return (
            f"No commits were returned for `{repository}`."
        )

    branch = result.get(
        "branch",
    )

    heading = (
        f"Recent commits for `{repository}`"
        + (
            f" on `{branch}`"
            if branch
            else ""
        )
        + ":"
    )

    lines = [
        heading,
        "",
    ]

    for commit in commits:
        if not isinstance(
            commit,
            dict,
        ):
            continue

        lines.extend(
            [
                (
                    f"- `{commit.get('sha', '')}` — "
                    f"{commit.get('message', '')}"
                ),
                (
                    f"  Author: {commit.get('author') or 'unknown'}"
                    f" | Date: {commit.get('date') or 'unknown'}"
                ),
            ]
        )

    return "\n".join(
        lines,
    )


def _format_github_issues(
    result: Any,
) -> str:
    if not isinstance(
        result,
        dict,
    ):
        return "GitHub issues were retrieved successfully."

    repository = result.get(
        "repository",
        "unknown",
    )

    state = result.get(
        "state",
        "open",
    )

    issues = result.get(
        "issues",
        [],
    )

    if not isinstance(
        issues,
        list,
    ) or not issues:
        return (
            f"No {state} issues were returned for `{repository}`."
        )

    lines = [
        f"{str(state).title()} issues for `{repository}`:",
        "",
    ]

    for issue in issues:
        if not isinstance(
            issue,
            dict,
        ):
            continue

        lines.append(
            f"- #{issue.get('number', '?')} "
            f"{issue.get('title', '')} "
            f"— {issue.get('author') or 'unknown'} "
            f"({issue.get('comments', 0)} comments)"
        )

    return "\n".join(
        lines,
    )


def _format_github_pull_requests(
    result: Any,
) -> str:
    if not isinstance(
        result,
        dict,
    ):
        return "GitHub pull requests were retrieved successfully."

    repository = result.get(
        "repository",
        "unknown",
    )

    state = result.get(
        "state",
        "open",
    )

    pull_requests = result.get(
        "pull_requests",
        [],
    )

    if not isinstance(
        pull_requests,
        list,
    ) or not pull_requests:
        return (
            f"No {state} pull requests were returned "
            f"for `{repository}`."
        )

    lines = [
        (
            f"{str(state).title()} pull requests "
            f"for `{repository}`:"
        ),
        "",
    ]

    for pull_request in pull_requests:
        if not isinstance(
            pull_request,
            dict,
        ):
            continue

        draft_marker = (
            " [draft]"
            if pull_request.get(
                "draft",
                False,
            )
            else ""
        )

        lines.append(
            f"- #{pull_request.get('number', '?')} "
            f"{pull_request.get('title', '')}"
            f"{draft_marker} — "
            f"`{pull_request.get('head_branch') or '?'} → "
            f"{pull_request.get('base_branch') or '?'}`"
        )

    return "\n".join(
        lines,
    )



def _format_postgres_schemas(
    result: Any,
) -> str:
    if not isinstance(result, dict):
        return "PostgreSQL schemas were retrieved successfully."

    schemas = result.get("schemas", [])

    if not isinstance(schemas, list) or not schemas:
        return "No user-visible PostgreSQL schemas were found."

    lines = [
        "PostgreSQL schemas:",
        "",
    ]

    for schema in schemas:
        if not isinstance(schema, dict):
            continue

        lines.append(
            f"- `{schema.get('schema_name', 'unknown')}` "
            f"(owner: {schema.get('owner_name') or 'unknown'})"
        )

    return "\n".join(lines)


def _format_postgres_tables(
    result: Any,
) -> str:
    if not isinstance(result, dict):
        return "PostgreSQL tables were retrieved successfully."

    schema = result.get("schema", "public")
    tables = result.get("tables", [])

    if not isinstance(tables, list) or not tables:
        return f"No tables or views were found in schema `{schema}`."

    lines = [
        f"Tables and views in schema `{schema}`:",
        "",
    ]

    for table in tables:
        if not isinstance(table, dict):
            continue

        lines.append(
            f"- `{table.get('table_name', 'unknown')}` "
            f"— {table.get('table_type', 'unknown')}"
        )

    return "\n".join(lines)


def _format_postgres_table_description(
    result: Any,
) -> str:
    if not isinstance(result, dict):
        return "PostgreSQL table metadata was retrieved successfully."

    schema = result.get("schema", "public")
    table = result.get("table", "unknown")
    columns = result.get("columns", [])
    constraints = result.get("constraints", [])
    indexes = result.get("indexes", [])

    lines = [
        f"Table `{schema}.{table}`:",
        "",
        "Columns:",
    ]

    if isinstance(columns, list) and columns:
        for column in columns:
            if not isinstance(column, dict):
                continue

            nullable = (
                "nullable"
                if column.get("is_nullable") == "YES"
                else "not null"
            )

            lines.append(
                f"- `{column.get('column_name', 'unknown')}` "
                f"{column.get('data_type', 'unknown')} ({nullable})"
            )
    else:
        lines.append("- No columns returned.")

    if isinstance(constraints, list) and constraints:
        lines.extend(
            [
                "",
                "Constraints:",
            ]
        )

        for constraint in constraints:
            if not isinstance(constraint, dict):
                continue

            lines.append(
                f"- {constraint.get('constraint_type', 'unknown')}: "
                f"`{constraint.get('constraint_name', 'unknown')}` "
                f"on `{constraint.get('column_name') or 'n/a'}`"
            )

    if isinstance(indexes, list) and indexes:
        lines.extend(
            [
                "",
                "Indexes:",
            ]
        )

        for index in indexes:
            if not isinstance(index, dict):
                continue

            lines.append(
                f"- `{index.get('index_name', 'unknown')}`"
            )

    return "\n".join(lines)


def _format_postgres_query(
    result: Any,
) -> str:
    if not isinstance(result, dict):
        return "The read-only PostgreSQL query completed successfully."

    columns = result.get("columns", [])
    rows = result.get("rows", [])

    if not isinstance(rows, list) or not rows:
        return "The read-only query completed and returned no rows."

    if not isinstance(columns, list) or not columns:
        columns = list(rows[0].keys()) if isinstance(rows[0], dict) else []

    lines = [
        "Read-only query result:",
        "",
        "| " + " | ".join(str(column) for column in columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]

    for row in rows:
        if not isinstance(row, dict):
            continue

        values = [
            str(row.get(column, "")).replace("|", "\\|").replace("\n", " ")
            for column in columns
        ]

        lines.append(
            "| " + " | ".join(values) + " |"
        )

    if result.get("truncated", False):
        lines.extend(
            [
                "",
                f"Results were truncated to {result.get('max_rows', len(rows))} rows.",
            ]
        )

    return "\n".join(lines)


def _format_postgres_explain(
    result: Any,
) -> str:
    if not isinstance(result, dict):
        return "The PostgreSQL execution plan was retrieved successfully."

    import json

    query = result.get("query", "")
    plan = result.get("plan")

    rendered_plan = json.dumps(
        plan,
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    return "\n".join(
        [
            "PostgreSQL execution plan:",
            "",
            "Query:",
            "```sql",
            str(query),
            "```",
            "",
            "Plan:",
            "```json",
            rendered_plan,
            "```",
            "",
            "ANALYZE was not executed.",
        ]
    )



def _format_docker_containers(
    result: Any,
) -> str:
    if not isinstance(result, dict):
        return "Docker containers were retrieved successfully."

    containers = result.get(
        "containers",
        [],
    )

    if not isinstance(containers, list) or not containers:
        return "No Docker containers were found."

    lines = [
        "Docker containers:",
        "",
        "| Name | Image | State | Status | ID |",
        "|---|---|---|---|---|",
    ]

    for container in containers:
        if not isinstance(container, dict):
            continue

        names = container.get(
            "names",
            [],
        )

        name = (
            names[0]
            if isinstance(names, list) and names
            else "unknown"
        )

        values = [
            name,
            container.get(
                "image",
                "unknown",
            ),
            container.get(
                "state",
                "unknown",
            ),
            container.get(
                "status",
                "unknown",
            ),
            container.get(
                "id",
                "",
            ),
        ]

        lines.append(
            "| "
            + " | ".join(
                str(value).replace(
                    "|",
                    "\\|",
                )
                for value in values
            )
            + " |"
        )

    return "\n".join(lines)


def _format_docker_container_inspect(
    result: Any,
) -> str:
    if not isinstance(result, dict):
        return "Docker container metadata was retrieved successfully."

    state = result.get(
        "state",
        {},
    )

    if not isinstance(state, dict):
        state = {}

    ports = result.get(
        "ports",
        [],
    )

    lines = [
        f"Docker container `{result.get('name', 'unknown')}`:",
        "",
        f"- ID: `{result.get('id', '')}`",
        f"- Image: `{result.get('image', 'unknown')}`",
        f"- Platform: {result.get('platform') or 'unknown'}",
        f"- Status: {state.get('status') or 'unknown'}",
        f"- Running: {state.get('running', False)}",
        f"- Health: {state.get('health') or 'not configured'}",
        f"- Exit code: {state.get('exit_code')}",
        f"- Restart policy: {result.get('restart_policy') or 'none'}",
        f"- Networks: {', '.join(result.get('networks', [])) or 'none'}",
    ]

    if isinstance(ports, list) and ports:
        lines.extend(
            [
                "",
                "Ports:",
            ]
        )

        for port in ports:
            if not isinstance(port, dict):
                continue

            host_binding = (
                f"{port.get('host_ip')}:{port.get('host_port')}"
                if port.get(
                    "host_port",
                )
                else "not published"
            )

            lines.append(
                f"- `{port.get('container_port', 'unknown')}` → "
                f"`{host_binding}`"
            )

    return "\n".join(lines)


def _format_docker_logs(
    result: Any,
) -> str:
    if not isinstance(result, dict):
        return "Docker logs were retrieved successfully."

    logs = result.get(
        "logs",
        [],
    )

    if not isinstance(logs, list) or not logs:
        return (
            f"No recent logs were returned for "
            f"`{result.get('container', 'unknown')}`."
        )

    rendered_logs = "\n".join(
        str(line)
        for line in logs
    )

    return "\n".join(
        [
            (
                f"Recent logs for "
                f"`{result.get('container', 'unknown')}`:"
            ),
            "",
            "```text",
            rendered_logs,
            "```",
        ]
    )


def _format_docker_images(
    result: Any,
) -> str:
    if not isinstance(result, dict):
        return "Docker images were retrieved successfully."

    images = result.get(
        "images",
        [],
    )

    if not isinstance(images, list) or not images:
        return "No Docker images were found."

    lines = [
        "Docker images:",
        "",
        "| Tags | ID | Size (MB) | Created |",
        "|---|---|---:|---|",
    ]

    for image in images:
        if not isinstance(image, dict):
            continue

        tags = image.get(
            "repository_tags",
            [],
        )

        rendered_tags = (
            ", ".join(
                str(tag)
                for tag in tags
            )
            if isinstance(tags, list) and tags
            else "<none>"
        )

        size_mb = round(
            float(
                image.get(
                    "size_bytes",
                    0,
                )
            )
            / 1_048_576,
            2,
        )

        lines.append(
            "| "
            + " | ".join(
                [
                    rendered_tags.replace(
                        "|",
                        "\\|",
                    ),
                    str(
                        image.get(
                            "id",
                            "",
                        )
                    ),
                    str(
                        size_mb,
                    ),
                    str(
                        image.get(
                            "created_at",
                        )
                        or "unknown"
                    ),
                ]
            )
            + " |"
        )

    return "\n".join(lines)


def _format_docker_system_info(
    result: Any,
) -> str:
    if not isinstance(result, dict):
        return "Docker system information was retrieved successfully."

    memory_gb = round(
        float(
            result.get(
                "memory_bytes",
                0,
            )
        )
        / 1_073_741_824,
        2,
    )

    return "\n".join(
        [
            "Docker Engine information:",
            "",
            f"- Name: {result.get('name') or 'unknown'}",
            f"- Server version: {result.get('server_version') or 'unknown'}",
            f"- Operating system: {result.get('operating_system') or 'unknown'}",
            f"- Architecture: {result.get('architecture') or 'unknown'}",
            f"- CPUs: {result.get('cpus', 0)}",
            f"- Memory: {memory_gb} GB",
            f"- Containers: {result.get('containers', 0)}",
            f"- Running: {result.get('containers_running', 0)}",
            f"- Paused: {result.get('containers_paused', 0)}",
            f"- Stopped: {result.get('containers_stopped', 0)}",
            f"- Images: {result.get('images', 0)}",
            f"- Storage driver: {result.get('driver') or 'unknown'}",
        ]
    )


def _first_text_content(
    content: list[dict[str, Any]],
) -> str | None:
    for item in content:
        if not isinstance(
            item,
            dict,
        ):
            continue

        text = item.get(
            "text",
        )

        if text:
            return str(
                text,
            ).strip()

    return None
