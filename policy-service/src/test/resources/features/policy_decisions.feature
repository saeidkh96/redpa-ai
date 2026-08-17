
Feature: Enterprise policy decisions
  As the RedPA execution platform
  I want risky actions to be classified before execution
  So that safe reads can continue and side effects remain controlled

  Scenario: Read-only Docker inspection is allowed
    Given an agent requests action "list_containers"
    When the policy engine evaluates the action
    Then the decision is "ALLOW"
    And the risk is "LOW"

  Scenario: Sending email requires human review
    Given an agent requests action "send_email"
    When the policy engine evaluates the action
    Then the decision is "REVIEW"
    And the risk is "HIGH"

  Scenario: Destructive database operation is denied
    Given an agent requests action "drop_database"
    When the policy engine evaluates the action
    Then the decision is "DENY"
    And the risk is "CRITICAL"

  Scenario: Unknown action fails closed to review
    Given an agent requests action "mystery_external_action"
    When the policy engine evaluates the action
    Then the decision is "REVIEW"
    And the risk is "MEDIUM"
