package ai.redpa.policy.api;

import ai.redpa.policy.application.PolicyEngine;
import ai.redpa.policy.domain.PolicyEvaluation;
import ai.redpa.policy.domain.PolicyRequest;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/policies")
public class PolicyController {
    private final PolicyEngine policyEngine;

    public PolicyController(PolicyEngine policyEngine) {
        this.policyEngine = policyEngine;
    }

    @PostMapping("/evaluate")
    public PolicyEvaluation evaluate(@RequestBody PolicyRequest request) {
        return policyEngine.evaluate(request);
    }
}
