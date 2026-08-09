package ai.redpa.policy;

import ai.redpa.policy.application.PolicyEngine;
import ai.redpa.policy.domain.PolicyDecision;
import ai.redpa.policy.domain.PolicyRequest;
import ai.redpa.policy.infrastructure.rules.DestructiveActionRule;
import ai.redpa.policy.infrastructure.rules.ExternalSideEffectRule;
import ai.redpa.policy.infrastructure.rules.ReadOnlyActionRule;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

class PolicyEngineTest {
    private final PolicyEngine engine = new PolicyEngine(List.of(
            new DestructiveActionRule(),
            new ExternalSideEffectRule(),
            new ReadOnlyActionRule()
    ));

    private PolicyRequest request(String action) {
        return new PolicyRequest(
                action,
                "tool",
                Map.of(),
                "tool-agent",
                "user-1",
                "workflow-1",
                Map.of()
        );
    }

    @Test
    void allowsReadOnlyAction() {
        assertThat(engine.evaluate(request("list_containers")).decision())
                .isEqualTo(PolicyDecision.ALLOW);
    }

    @Test
    void requiresReviewForExternalSideEffect() {
        assertThat(engine.evaluate(request("send_email")).decision())
                .isEqualTo(PolicyDecision.REVIEW);
    }

    @Test
    void deniesDestructiveAction() {
        assertThat(engine.evaluate(request("drop_database")).decision())
                .isEqualTo(PolicyDecision.DENY);
    }

    @Test
    void unknownActionFailsClosedToReview() {
        assertThat(engine.evaluate(request("unclassified_action")).decision())
                .isEqualTo(PolicyDecision.REVIEW);
    }
}
