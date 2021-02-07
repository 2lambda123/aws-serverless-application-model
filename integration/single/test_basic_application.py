from integration.helpers.base_test import BaseTest


class TestBasicApplication(BaseTest):
    """
    Basic AWS::Serverless::Application tests
    """

    def test_basic_application_s3_location(self):
        """
        Creates an application with its properties defined as a template
        file in a S3 bucket
        """
        self.create_and_verify_stack("basic_application_s3_location")

        nested_stack_resource = self.get_stack_nested_stack_resources()
        tables = self.get_stack_resources("AWS::DynamoDB::Table", nested_stack_resource)

        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0]["LogicalResourceId"], "MyTable")

    def test_basic_application_sar_location(self):
        """
        Creates an application with a lamda function
        """
        self.create_and_verify_stack("basic_application_sar_location")

        nested_stack_resource = self.get_stack_nested_stack_resources()
        functions = self.get_stack_resources("AWS::Lambda::Function", nested_stack_resource)

        self.assertEqual(len(functions), 1)
        self.assertEqual(functions[0]["LogicalResourceId"], "helloworldpython")

    def test_basic_application_sar_location_with_intrinsics(self):
        """
        Creates an application with a lambda function with intrinsics
        """
        expected_function_name = "helloworldpython" if self.get_region() == "us-east-1" else "helloworldpython3"
        self.create_and_verify_stack("basic_application_sar_location_with_intrinsics")

        nested_stack_resource = self.get_stack_nested_stack_resources()
        functions = self.get_stack_resources("AWS::Lambda::Function", nested_stack_resource)

        self.assertEqual(len(functions), 1)
        self.assertEqual(functions[0]["LogicalResourceId"], expected_function_name)

    def test_basic_application_sar_with_event(self):
        """
        Creates an application with a lambda function with intrinsics
        """
        self.create_and_verify_stack("basic_application_sar_with_event")

        nested_stack_resource = self.get_stack_nested_stack_resources()
        functions = self.get_stack_resources("AWS::Lambda::Function", nested_stack_resource)

        bucket_id = self.get_physical_id_by_logical_id("Images")
        config = self.client_provider.s3_client.get_bucket_notification_configuration(
            Bucket=bucket_id
        )
        
        self.assertRegexpMatches(config['LambdaFunctionConfigurations'][0]['LambdaFunctionArn'], functions[0]['PhysicalResourceId'])

    def test_basic_stack_with_event(self):
        """
        Creates an application with a lambda function with intrinsics
        """
        self.create_and_verify_stack("basic_stack_with_event")

        nested_stack_resource = self.get_stack_nested_stack_resources()
        functions = self.get_stack_resources("AWS::Lambda::Function", nested_stack_resource)

        bucket_id = self.get_physical_id_by_logical_id("Images")
        config = self.client_provider.s3_client.get_bucket_notification_configuration(
            Bucket=bucket_id
        )
        
        self.assertRegexpMatches(config['LambdaFunctionConfigurations'][0]['LambdaFunctionArn'], functions[0]['PhysicalResourceId'])
