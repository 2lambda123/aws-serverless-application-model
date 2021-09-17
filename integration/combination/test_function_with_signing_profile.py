from unittest.case import skipIf

from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


class TestDependsOn(BaseTest):
    @skipIf(current_region_does_not_support(["CodeSign"]), "CodeSign is not supported in this testing region")
    def test_function_with_signing_profile(self):
        self.create_and_verify_stack("combination/function_with_signing_profile")
