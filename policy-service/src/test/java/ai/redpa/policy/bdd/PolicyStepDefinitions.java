package ai.redpa.policy.bdd;

import ai.redpa.policy.application.PolicyEngine;
import ai.redpa.policy.domain.PolicyDecision;
import ai.redpa.policy.domain.PolicyEvaluation;
import ai.redpa.policy.domain.PolicyRequest;
import ai.redpa.policy.infrastructure.rules.DestructiveActionRule;
import ai.redpa.policy.infrastructure.rules.ExternalSideEffectRule;
import ai.redpa.policy.infrastructure.rules.ReadOnlyActionRule;
import io.cucumber.java.en.Given;
import io.cucumber.java.en.Then;
import io.cucumber.java.en.When;

import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

public class PolicyStepDefinitions {
    private String action;
    private PolicyEvaluation evaluation;

    private final PolicyEngine engine = new PolicyEngine(List.of(
            new DestructiveActionRule(),
            new ExternalSideEffectRule(),
            new ReadOnlyActionRule()
    ));

    @Given("an agent requests action {string}")
    public void anAgentRequestsAction(String requestedAction) {
        this.action = requestedAction;
    }

    @When("the policy engine evaluates the action")
    public void thePolicyEngineEvaluatesTheAction() {
        evaluation = engine.evaluate(
                new PolicyRequest(
                        action,
                        "tool",
                        Map.of(),
                        "bdd-agent",
                        "bdd-user",
                        "bdd-workflow",
                        Map.of()
                )
        );
    }

    @Then("the decision is {string}")
    public void theDecisionIs(String expected) {
        assertThat(evaluation.decision())
                .isEqualTo(PolicyDecision.valueOf(expected));
    }

    @Then("the risk is {string}")
    public void theRiskIs(String expected) {
        assertThat(evaluation.risk().name())
                .isEqualTo(expected);
    }
}
