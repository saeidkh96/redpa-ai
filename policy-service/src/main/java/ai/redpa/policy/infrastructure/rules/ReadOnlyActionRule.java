package ai.redpa.policy.infrastructure.rules;

import ai.redpa.policy.application.PolicyEngine;
import ai.redpa.policy.domain.PolicyDecision;
import ai.redpa.policy.domain.PolicyEvaluation;
import ai.redpa.policy.domain.PolicyRequest;
import ai.redpa.policy.domain.PolicyRule;
import ai.redpa.policy.domain.RiskLevel;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;

@Component
@Order(30)
public class ReadOnlyActionRule implements PolicyRule {
    private static final Set<String> SAFE_EXACT = Set.of(
            "calculator",
            "datetime",
            "weather",
            "search",
            "web_search",
            "read_file",
            "file_info",
            "list_files",
            "search_files",
            "list_containers",
            "inspect_container",
            "container_logs",
            "list_images",
            "system_info",
            "list_schemas",
            "list_tables",
            "describe_table",
            "explain",
            "query",
            "repository",
            "branches",
            "commits",
            "issues",
            "pull_requests"
    );

    @Override
    public Optional<PolicyEvaluation> evaluate(PolicyRequest request) {
        String action = normalize(request.action());

        boolean readOnly = SAFE_EXACT.contains(action)
                || action.startsWith("get_")
                || action.startsWith("list_")
                || action.startsWith("read_")
                || action.startsWith("inspect_")
                || action.startsWith("search_")
                || action.startsWith("describe_");

        if (!readOnly) {
            return Optional.empty();
        }

        return Optional.of(new PolicyEvaluation(
                PolicyDecision.ALLOW,
                RiskLevel.LOW,
                "Read-only operation is allowed by policy.",
                List.of("READ_ONLY_ALLOW"),
                PolicyEngine.POLICY_VERSION
        ));
    }

    private String normalize(String value) {
        if (value == null) {
            return "";
        }

        String normalized = value.trim().toLowerCase(Locale.ROOT).replace('-', '_');

        int separator = normalized.lastIndexOf(':');
        if (separator >= 0 && separator + 1 < normalized.length()) {
            normalized = normalized.substring(separator + 1);
        }

        return normalized;
    }
}
