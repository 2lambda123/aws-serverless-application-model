from parameterized import parameterized

from integration.helpers.base_test import BaseTest


class TestApiWithDisableExecuteApiEndpoint(BaseTest):
    @parameterized.expand(
        [
            ("combination/api_with_disable_execute_api_endpoint_true", True),
            ("combination/api_with_disable_execute_api_endpoint_false", False),
        ]
    )
    def test_end_point_configuration(self, file_name, disable_value):
        self.create_and_verify_stack(file_name)

        stack_outputs = self.get_stack_outputs()
        rest_api_id = self.get_physical_id_by_type("AWS::ApiGateway::RestApi")
        apigw_client = self.client_provider.api_client

        response = apigw_client.get_rest_api(restApiId=rest_api_id)
        api_result = response["disableExecuteApiEndpoint"]
        self.assertEqual(api_result, disable_value)
