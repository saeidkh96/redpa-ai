package ai.redpa.policy.domain;

import java.util.Optional;

public interface PolicyRule {
    Optional<PolicyEvaluation> evaluate(PolicyRequest request);
}
