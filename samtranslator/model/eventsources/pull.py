from samtranslator.model import ResourceMacro, PropertyType
from samtranslator.model.lambda_ import LambdaEventSourceMapping
from samtranslator.model.types import is_type, is_str
from samtranslator.translator.arn_generator import ArnGenerator


class PullEventSource(ResourceMacro):
    """Base class for pull event sources for SAM Functions.

    The pull events are the streams--Kinesis and DynamoDB Streams. Both of these correspond to an EventSourceMapping in
    Lambda, and require that the execution role be given to Kinesis or DynamoDB Streams, respectively.

    :cvar str policy_arn: The ARN of the AWS managed role policy corresponding to this pull event source
    """
    resource_type = None
    property_types = {
        'Stream': PropertyType(True, is_str()),
        'BatchSize': PropertyType(False, is_type(int)),
        'StartingPosition': PropertyType(True, is_str())
    }

    def get_policy_arn(self):
        raise NotImplementedError("Subclass must implement this method")

    def to_cloudformation(self, **kwargs):
        """Returns the Lambda EventSourceMapping to which this pull event corresponds. Adds the appropriate managed
        policy to the function's execution role, if such a role is provided.

        :param dict kwargs: a dict containing the execution role generated for the function
        :returns: a list of vanilla CloudFormation Resources, to which this pull event expands
        :rtype: list
        """
        function = kwargs.get('function')

        if not function:
            raise TypeError("Missing required keyword argument: function")

        resources = []

        lambda_eventsourcemapping = LambdaEventSourceMapping(self.logical_id)
        resources.append(lambda_eventsourcemapping)

        try:
            # Name will not be available for Alias resources
            function_name_or_arn = function.get_runtime_attr("name")
        except NotImplementedError:
            function_name_or_arn = function.get_runtime_attr("arn")

        lambda_eventsourcemapping.FunctionName = function_name_or_arn
        lambda_eventsourcemapping.EventSourceArn = self.Stream
        lambda_eventsourcemapping.StartingPosition = self.StartingPosition
        lambda_eventsourcemapping.BatchSize = self.BatchSize

        if 'role' in kwargs:
            self._link_policy(kwargs['role'])

        return resources

    def _link_policy(self, role):
        """If this source triggers a Lambda function whose execution role is auto-generated by SAM, add the
        appropriate managed policy to this Role.

        :param model.iam.IAMROle role: the execution role generated for the function
        """
        policy_arn = self.get_policy_arn()
        if role is not None and policy_arn not in role.ManagedPolicyArns:
            role.ManagedPolicyArns.append(policy_arn)


class Kinesis(PullEventSource):
    """Kinesis event source."""
    resource_type = 'Kinesis'

    def get_policy_arn(self):
        return ArnGenerator.generate_aws_managed_policy_arn('service-role/AWSLambdaKinesisExecutionRole')


class DynamoDB(PullEventSource):
    """DynamoDB Streams event source."""
    resource_type = 'DynamoDB'

    def get_policy_arn(self):
        return ArnGenerator.generate_aws_managed_policy_arn('service-role/AWSLambdaDynamoDBExecutionRole')
