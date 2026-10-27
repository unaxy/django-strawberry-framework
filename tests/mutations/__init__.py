"""Package tests for the mutations subsystem (DjangoMutation + generated inputs).

Mirror-package convention (spec-036): one test
module per mutation source module, so the package internal mechanics stay under
``tests/mutations/`` while live GraphQL behavior is earned through the fakeshop
``test_query`` suite.
"""
