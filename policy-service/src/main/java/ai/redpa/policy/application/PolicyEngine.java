package ai.redpa.policy.application;

import ai.redpa.policy.domain.PolicyDecision;
import ai.redpa.policy.domain.PolicyEvaluation;
import ai.redpa.policy.domain.PolicyRequest;
import ai.redpa.policy.domain.PolicyRule;
import ai.redpa.policy.domain.RiskLevel;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class PolicyEngine {
    public static final String POLICY_VERSION = "13.3.0";

    private final List<PolicyRule> rules;

    public PolicyEngine(List<PolicyRule> rules) {
        this.rules = rules;
    }

    public PolicyEvaluation evaluate(PolicyRequest request) {
        if (request.action() == null || request.action().isBlank()) {
            return new PolicyEvaluation(
                    PolicyDecision.DENY,
                    RiskLevel.HIGH,
                    "An action name is required.",
                    List.of("ACTION_REQUIRED"),
                    POLICY_VERSION
            );
        }

        return rules.stream()
                .map(rule -> rule.evaluate(request))
                .filter(optional -> optional.isPresent())
                .map(optional -> optional.get())
                .findFirst()
                .orElseGet(() -> new PolicyEvaluation(
                        PolicyDecision.REVIEW,
                        RiskLevel.MEDIUM,
                        "Unknown actions require human review by default.",
                        List.of("UNKNOWN_ACTION_REQUIRES_REVIEW"),
                        POLICY_VERSION
                ));
    }
}
