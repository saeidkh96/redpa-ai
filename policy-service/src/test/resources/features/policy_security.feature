Feature: RedPA policy security boundaries

  Scenario: A read-only Docker action is allowed
    Given a policy action "list_containers"
    When the policy is evaluated
    Then the decision is "ALLOW"
    And the risk is "LOW"

  Scenario: An external side effect requires review
    Given a policy action "send_email"
    When the policy is evaluated
    Then the decision is "REVIEW"
    And the risk is "HIGH"

  Scenario: A destructive database action is denied
    Given a policy action "drop_database"
    When the policy is evaluated
    Then the decision is "DENY"
    And the risk is "CRITICAL"

  Scenario: An unknown action fails safely into review
    Given a policy action "unknown_phase13_action"
    When the policy is evaluated
    Then the decision is "REVIEW"
    And the risk is "MEDIUM"
