package ai.redpa.policy.domain;

import java.util.List;

public record PolicyEvaluation(
        PolicyDecision decision,
        RiskLevel risk,
        String reason,
        List<String> matchedRules,
        String policyVersion
) {
}
