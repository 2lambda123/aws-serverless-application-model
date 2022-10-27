from samtranslator.metrics.method_decorator import cw_timer
from samtranslator.plugins import BasePlugin
from samtranslator.model.resource_policies import ResourcePolicies, PolicyTypes
from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.policy_template_processor.exceptions import InsufficientParameterValues, InvalidParameterValues
from samtranslator.model.intrinsics import is_intrinsic_if, is_intrinsic_no_value


class PolicyTemplatesForResourcePlugin(BasePlugin):
    """
    Use this plugin to allow the usage of Policy Templates in `Policies` section of AWS::Serverless::Function or
    AWS::Serverless::StateMachine resource.
    This plugin runs a `before_transform_resource` hook and converts policy templates into regular policy statements
    for the core SAM translator to take care of.
    """

    _plugin_name = ""
    SUPPORTED_RESOURCE_TYPE = {"AWS::Serverless::Function", "AWS::Serverless::StateMachine"}

    def __init__(self, policy_template_processor):  # type: ignore[no-untyped-def]
        """
        Initialize the plugin.

        :param policy_template_processor: Instance of the PolicyTemplateProcessor that knows how to convert policy
            template to a statement
        """

        # Plugin name is the class name for easy disambiguation
        _plugin_name = PolicyTemplatesForResourcePlugin.__name__
        super(PolicyTemplatesForResourcePlugin, self).__init__(_plugin_name)  # type: ignore[no-untyped-call]

        self._policy_template_processor = policy_template_processor

    @cw_timer(prefix="Plugin-PolicyTemplates")  # type: ignore[no-untyped-call]
    def on_before_transform_resource(self, logical_id, resource_type, resource_properties):  # type: ignore[no-untyped-def]
        """
        Hook method that gets called before "each" SAM resource gets processed

        :param string logical_id: Logical ID of the resource being processed
        :param string resource_type: Type of the resource being processed
        :param dict resource_properties: Properties of the resource
        :return: Nothing
        """

        if not self._is_supported(resource_type):  # type: ignore[no-untyped-call]
            return

        function_policies = ResourcePolicies(resource_properties, self._policy_template_processor)  # type: ignore[no-untyped-call]

        if len(function_policies) == 0:
            # No policies to process
            return

        result = []
        for policy_entry in function_policies.get():  # type: ignore[no-untyped-call]

            if policy_entry.type is not PolicyTypes.POLICY_TEMPLATE:
                # If we don't know the type, skip processing and pass to result as is.
                result.append(policy_entry.data)
                continue

            if is_intrinsic_if(policy_entry.data):
                # If policy is an intrinsic if, we need to process each sub-statement separately
                processed_intrinsic_if = self._process_intrinsic_if_policy_template(logical_id, policy_entry)  # type: ignore[no-untyped-call]
                result.append(processed_intrinsic_if)
                continue

            converted_policy = self._process_policy_template(logical_id, policy_entry.data)  # type: ignore[no-untyped-call]
            result.append(converted_policy)

        # Save the modified policies list to the input
        resource_properties[ResourcePolicies.POLICIES_PROPERTY_NAME] = result

    def _process_intrinsic_if_policy_template(self, logical_id, policy_entry):  # type: ignore[no-untyped-def]
        intrinsic_if = policy_entry.data
        then_statement = intrinsic_if["Fn::If"][1]
        else_statement = intrinsic_if["Fn::If"][2]

        processed_then_statement = (
            then_statement
            if is_intrinsic_no_value(then_statement)
            else self._process_policy_template(logical_id, then_statement)  # type: ignore[no-untyped-call]
        )

        processed_else_statement = (
            else_statement
            if is_intrinsic_no_value(else_statement)
            else self._process_policy_template(logical_id, else_statement)  # type: ignore[no-untyped-call]
        )

        processed_intrinsic_if = {
            "Fn::If": [policy_entry.data["Fn::If"][0], processed_then_statement, processed_else_statement]
        }

        return processed_intrinsic_if

    def _process_policy_template(self, logical_id, template_data):  # type: ignore[no-untyped-def]

        # We are processing policy templates. We know they have a particular structure:
        # {"templateName": { parameter_values_dict }}
        template_name = list(template_data.keys())[0]
        template_parameters = list(template_data.values())[0]
        try:

            # 'convert' will return a list of policy statements
            return self._policy_template_processor.convert(template_name, template_parameters)

        except InsufficientParameterValues as ex:
            # Exception's message will give lot of specific details
            raise InvalidResourceException(logical_id, str(ex))  # type: ignore[no-untyped-call]
        except InvalidParameterValues:
            raise InvalidResourceException(  # type: ignore[no-untyped-call]
                logical_id, "Must specify valid parameter values for policy template '{}'".format(template_name)
            )

    def _is_supported(self, resource_type):  # type: ignore[no-untyped-def]
        """
        Is this resource supported by this plugin?

        :param string resource_type: Type of the resource
        :return: True, if this plugin supports this resource. False otherwise
        """
        return resource_type in self.SUPPORTED_RESOURCE_TYPE
