package ai.redpa.policy.domain;

import java.util.Map;

public record PolicyRequest(
        String action,
        String resource,
        Map<String, Object> arguments,
        String agentId,
        String userId,
        String workflowId,
        Map<String, Object> metadata
) {
}
