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
@Order(20)
public class ExternalSideEffectRule implements PolicyRule {
    private static final Set<String> REVIEW_ACTIONS = Set.of(
            "send_email",
            "send_message",
            "transfer_money",
            "process_payment",
            "approve_invoice",
            "issue_refund",
            "create_calendar_event",
            "create_github_issue",
            "create_issue",
            "purchase_product",
            "write_file",
            "update_record",
            "insert_record"
    );

    @Override
    public Optional<PolicyEvaluation> evaluate(PolicyRequest request) {
        String action = normalize(request.action());

        if (!REVIEW_ACTIONS.contains(action)) {
            return Optional.empty();
        }

        return Optional.of(new PolicyEvaluation(
                PolicyDecision.REVIEW,
                RiskLevel.HIGH,
                "External side effects require explicit human approval.",
                List.of("EXTERNAL_SIDE_EFFECT_REVIEW"),
                PolicyEngine.POLICY_VERSION
        ));
    }

    private String normalize(String value) {
        return value == null
                ? ""
                : value.trim().toLowerCase(Locale.ROOT).replace('-', '_');
    }
}
