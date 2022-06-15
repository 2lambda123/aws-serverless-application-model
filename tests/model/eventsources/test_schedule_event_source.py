
# class SnsEventSource(TestCase):
#     def setUp(self):
#         self.logical_id = "ExampleCron"

#         self.schedule_event_source = Schedule(self.logical_id)
#         self.schedule_event_source.Schedule = "cron(1 2 3 4 ? *)"

#         self.function = Mock()
#         self.function.get_runtime_attr = Mock()
#         self.function.get_runtime_attr.return_value = "arn:aws:lambda:mock"
#         self.function.resource_attributes = {}
#         self.function.get_passthrough_resource_attributes = Mock()
#         self.function.get_passthrough_resource_attributes.return_value = {}

from unittest.mock import Mock, patch
from unittest import TestCase

from samtranslator.model.eventsources.push import Schedule
from samtranslator.model.lambda_ import LambdaFunction
from samtranslator.model.exceptions import InvalidEventException


class ScheduleEventSource(TestCase):
    def setUp(self):
        self.logical_id = "ScheduleEvent"
        self.schedule_event_source = Schedule(self.logical_id)
        self.schedule_event_source.Schedule = "rate(1 minute)"
        self.func = LambdaFunction("func")

    def test_to_cloudformation_returns_permission_and_schedule_resources(self):
        resources = self.schedule_event_source.to_cloudformation(function=self.function)
        self.assertEqual(len(resources), 2)
        self.assertEqual(resources[0].resource_type, "AWS::Events::Rule")
        self.assertEqual(resources[1].resource_type, "AWS::Lambda::Permission")

        schedule = resources[0]
        self.assertEqual(schedule.ScheduleExpression, "cron(1 2 3 4 ? *)")
        self.assertIsNone(schedule.State)

    def test_to_cloudformation_transforms_enabled_boolean_to_state(self):
        self.schedule_event_source.Enabled = True
        resources = self.schedule_event_source.to_cloudformation(function=self.function)
        schedule = resources[0]
        self.assertEqual(schedule.State, "ENABLED")

        self.schedule_event_source.Enabled = False
        resources = self.schedule_event_source.to_cloudformation(function=self.function)
        schedule = resources[0]
        self.assertEqual(schedule.State, "DISABLED")

    def test_to_cloudformation_passes_enabled_to_state(self):
        self.schedule_event_source.Enabled = {"Fn:If": [1, 2, 3]}
        resources = self.schedule_event_source.to_cloudformation(function=self.function)
        schedule = resources[0]
        self.assertEqual(schedule.State, {"Fn:If": [1, 2, 3]})

    def test_to_cloudformation_with_retry_policy(self):
        retry_policy = {"MaximumRetryAttempts": "10", "MaximumEventAgeInSeconds": "300"}
        self.schedule_event_source.RetryPolicy = retry_policy
        resources = self.schedule_event_source.to_cloudformation(function=self.func)
        self.assertEqual(len(resources), 2)
        event_rule = resources[0]
        self.assertEqual(event_rule.Targets[0]["RetryPolicy"], retry_policy)

    def test_to_cloudformation_with_dlq_arn_provided(self):
        dead_letter_config = {"Arn": "DeadLetterQueueArn"}
        self.schedule_event_source.DeadLetterConfig = dead_letter_config
        resources = self.schedule_event_source.to_cloudformation(function=self.func)
        self.assertEqual(len(resources), 2)
        event_rule = resources[0]
        self.assertEqual(event_rule.Targets[0]["DeadLetterConfig"], dead_letter_config)

    def test_to_cloudformation_invalid_both_dlq_arn_and_type_provided(self):
        dead_letter_config = {"Arn": "DeadLetterQueueArn", "Type": "SQS"}
        self.schedule_event_source.DeadLetterConfig = dead_letter_config
        with self.assertRaises(InvalidEventException):
            self.schedule_event_source.to_cloudformation(function=self.func)

    def test_to_cloudformation_invalid_dlq_type_provided(self):
        dead_letter_config = {"Type": "SNS", "QueueLogicalId": "MyDLQ"}
        self.schedule_event_source.DeadLetterConfig = dead_letter_config
        with self.assertRaises(InvalidEventException):
            self.schedule_event_source.to_cloudformation(function=self.func)

    def test_to_cloudformation_missing_dlq_type_or_arn(self):
        dead_letter_config = {"QueueLogicalId": "MyDLQ"}
        self.schedule_event_source.DeadLetterConfig = dead_letter_config
        with self.assertRaises(InvalidEventException):
            self.schedule_event_source.to_cloudformation(function=self.func)

    def test_to_cloudformation_with_dlq_generated(self):
        dead_letter_config = {"Type": "SQS"}
        dead_letter_config_translated = {"Arn": {"Fn::GetAtt": [self.logical_id + "Queue", "Arn"]}}
        self.schedule_event_source.DeadLetterConfig = dead_letter_config
        resources = self.schedule_event_source.to_cloudformation(function=self.func)
        self.assertEqual(len(resources), 4)
        event_rule = resources[0]
        self.assertEqual(event_rule.Targets[0]["DeadLetterConfig"], dead_letter_config_translated)

    def test_to_cloudformation_with_dlq_generated_with_custom_logical_id(self):
        dead_letter_config = {"Type": "SQS", "QueueLogicalId": "MyDLQ"}
        dead_letter_config_translated = {"Arn": {"Fn::GetAtt": ["MyDLQ", "Arn"]}}
        self.schedule_event_source.DeadLetterConfig = dead_letter_config
        resources = self.schedule_event_source.to_cloudformation(function=self.func)
        self.assertEqual(len(resources), 4)
        event_rule = resources[0]
        self.assertEqual(event_rule.Targets[0]["DeadLetterConfig"], dead_letter_config_translated)

    def test_to_cloudformation_with_dlq_generated_with_intrinsic_function_custom_logical_id_raises_exception(self):
        dead_letter_config = {"Type": "SQS", "QueueLogicalId": {"Fn::Sub": "MyDLQ${Env}"}}
        self.schedule_event_source.DeadLetterConfig = dead_letter_config
        with self.assertRaises(InvalidEventException):
            self.schedule_event_source.to_cloudformation(function=self.func)
