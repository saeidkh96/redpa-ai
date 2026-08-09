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
@Order(10)
public class DestructiveActionRule implements PolicyRule {
    private static final Set<String> DENY_EXACT = Set.of(
            "drop_database",
            "drop_table",
            "truncate_table",
            "delete_database",
            "destroy_cluster",
            "delete_all"
    );

    @Override
    public Optional<PolicyEvaluation> evaluate(PolicyRequest request) {
        String action = normalize(request.action());

        boolean destructive = DENY_EXACT.contains(action)
                || action.startsWith("drop_")
                || action.startsWith("truncate_")
                || action.contains("delete_all");

        if (!destructive) {
            return Optional.empty();
        }

        return Optional.of(new PolicyEvaluation(
                PolicyDecision.DENY,
                RiskLevel.CRITICAL,
                "Destructive infrastructure or bulk-data action is blocked.",
                List.of("DESTRUCTIVE_ACTION_DENY"),
                PolicyEngine.POLICY_VERSION
        ));
    }

    private String normalize(String value) {
        return value == null
                ? ""
                : value.trim().toLowerCase(Locale.ROOT).replace('-', '_');
    }
}
