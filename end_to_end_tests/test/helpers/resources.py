from .resource_types import ResourceTypes
from .resource_status import ResourceStatus
from samtranslator.model.exceptions import (
    InvalidResourceException,
    ResourceNotFoundException,
    LogicalIdDoesNotFollowPatternException,
    ResourceAlreadyExistsException,
    EmptyParameterException,
)

import re


class Resources:
    """
    Represents a collection of Stack Resources - like Functions, APIs etc

    Methods
    -------
    :method __init__(self)
        creates a dictionary for adding stack resources
    :method created(self, logical_resource_id, resource_type)
        adds the given stack resource and updates the resource status to CREATE_COMPLETE
    :method updated(self, logical_resource_id)
        updates the resource status to UPDATE_COMPLETE for the given logical id
    :method add(self, logical_resource_id=None, resource_type=None, resource_status=None, stack_resource=None)
        creates and adds a Resource to the list of resources either using stack resource or
        when logical_resource_id, resource_type and resource_status are defined
    :method set_status(self, logical_resource_id, new_status)
        changes the status for the given resource
    :method remove(self, logical_resource_id)
        removes the given resource from resources
    :method get_changed_resources(self, expected_resources)
        returns the differences between expected resources and the current resources
    :method clean_logical_id_if_necessary(self, logical_id_to_clean, resource_type)
        validates and cleans up logical ids generated by SAM translator.
    :method def __eq__(self, other):
        compares equality of two objects of Resources type
    :method from_list(resources_list)
        adds resources from a list to resources attribute by creating a new Resources object
    """

    def __init__(self):
        """
        creates a dictionary for adding stack resources
        """
        self.resources = dict()
        self.LOGICAL_ID_WITH_HASH_PATTERN = "^(.+)([a-fA-F0-9]{10})$"

    def created(self, logical_resource_id, resource_type):
        """adds the given stack resource and updates the resource status to CREATE_COMPLETE

        :param str logical_resource_id: logical id of the stack resource
        :param ResourceTypes resource_type: type of the resource in ResourceTypes
        :return: returns the Resources object by adding the given resource to resources dictionary
        :rtype: Resources
        """
        return self.add(logical_resource_id, resource_type.value, ResourceStatus.CREATE_COMPLETE.value)

    def updated(self, logical_resource_id):
        """updates the resource status to UPDATE_COMPLETE for the given logical id

        :param str logical_resource_id: logical id of the stack resource
        :return: returns the Resources object by updating the status to UPDATE_COMPLETE
        :rtype: Resources
        """
        return self.set_status(logical_resource_id, ResourceStatus.UPDATE_COMPLETE.value)

    def add(self, logical_resource_id=None, resource_type=None, resource_status=None, stack_resource=None):
        """creates and adds a Resource to the list of resources either using stack resource or
        when logical_resource_id, resource_type and resource_status are defined

        :param str logical_resource_id: logical id of the stack resource
        :param str resource_type: CloudFormation resource type of the resource
        :param str resource_status: desired resource status for the resource
        :param Resource stack_resource: adds the given stack resource to the resources list
        :raise: InvalidResourceException if stack_resource is not None and if any of LogicalResourceId, ResourceType and
                ResourceStatus keys are empty
        :raise: EmptyParameterException if stack_resource is None and if any of logical_resource_id, resource_type and
                resource_status params are not defined
        :raise: ResourceAlreadyExistsException if there is already a resource with the given logical_resource_id
        :return: Resources object by adding the resource to list of resources
        :rtype: Resources
        """
        if stack_resource is not None:
            # LogicalID of ApiGateway::Deployment resource gets suffixed with SHA.
            # This suffix changes on every run of the test. To keep tests simple, we will validate and strip
            # out this suffix here. Tests can continue to access and verify the resource using the LogicalId
            # specified in the template
            if stack_resource.get("LogicalResourceId") is None:
                raise InvalidResourceException(
                    "", "LogicalResourceId should not be empty for stack resource {}".format(stack_resource)
                )
            if stack_resource.get("ResourceType") is None:
                raise InvalidResourceException(
                    stack_resource.get("LogicalResourceId"),
                    "ResourceType should not be empty for stack resource {}".format(stack_resource),
                )
            if stack_resource.get("ResourceStatus") is None:
                raise InvalidResourceException(
                    stack_resource.get("LogicalResourceId"),
                    "ResourceStatus should not be empty for stack resource {}".format(stack_resource),
                )
            logical_id = self.clean_logical_id_if_necessary(
                logical_id_to_clean=stack_resource.get("LogicalResourceId"),
                resource_type=stack_resource.get("ResourceType"),
            )
            return self.add(
                logical_resource_id=logical_id,
                resource_type=stack_resource.get("ResourceType"),
                resource_status=stack_resource.get("ResourceStatus"),
            )
        else:
            if logical_resource_id is None:
                raise EmptyParameterException("logical_resource_id")
            if resource_type is None:
                raise EmptyParameterException("resource_type")
            if resource_status is None:
                raise EmptyParameterException("resource_status")

            new_resource = Resource(logical_resource_id, resource_type, resource_status)
            if logical_resource_id in self.resources.keys():
                raise ResourceAlreadyExistsException(logical_resource_id)
            self.resources[logical_resource_id] = new_resource
            return self

    def set_status(self, logical_resource_id, new_status):
        """changes the status for the given resource

        :param str logical_resource_id: logical id of the stack resource
        :param str new_status: new status for the given resource
        :raise: ResourceNotFoundException if logical id is not found
        :return: Resources with the updated status for the given resource
        :rtype: Resources
        """
        resource = self.resources.get(logical_resource_id)

        if resource is None:
            raise ResourceNotFoundException("with logical ID {}".format(logical_resource_id))
        resource.status = new_status
        return self

    def remove(self, logical_resource_id):
        """removes the given resource from resources

        :param str logical_resource_id: logical id of the stack resource to be removed
        :raise: ResourceNotFoundException if logical id is not found
        """
        try:
            self.resources.pop(logical_resource_id)
        except KeyError:
            raise ResourceNotFoundException("with logical ID {}".format(logical_resource_id))

    def get_changed_resources(self, expected_resources):
        """returns the differences between expected resources and the current resources

        :param dict expected_resources: absolute template path for stack creation
        :return: differences between current resources and expected resources
        :rtype: dict
        """
        diff_resources = dict()
        for key in self.resources.keys():
            if key not in expected_resources.resources or not expected_resources.resources.get(
                key
            ) == self.resources.get(key):
                diff_resources[key] = self.resources.get(key)
            # remove the resource if its same in generated resources and expected resources
            expected_resources.resources.pop(key, None)

        if expected_resources.resources is not None:
            diff_resources.update(expected_resources.resources)

        return diff_resources

    def clean_logical_id_if_necessary(self, logical_id_to_clean, resource_type):
        """validates and cleans up logical ids generated by SAM translator.

        :param str logical_id_to_clean: logical id of the stack resource
        :param str resource_type: CloudFormation resource type of the resource
        :raise: LogicalIdDoesNotFollowPatternException if the logical id doesn't contain 10 hex characters in the end
        :return: cleaned logical id
        :rtype: str
        """
        if (
            ResourceTypes.APIGW_DEPLOYMENT.value == resource_type
            or ResourceTypes.LAMBDA_VERSION.value == resource_type
            or ResourceTypes.LAMBDA_LAYER_VERSION.value == resource_type
        ):
            if not re.match(self.LOGICAL_ID_WITH_HASH_PATTERN, logical_id_to_clean):
                raise LogicalIdDoesNotFollowPatternException(logical_id_to_clean, resource_type)
            return logical_id_to_clean[:-10]  # remove last 10 digits and return
        return logical_id_to_clean

    def __eq__(self, other):
        """compares equality of two objects of Resources type

        :param Resources other: Resources object that would be compared with self
        :return: returns True if both the objects are equal
        :rtype: bool
        """
        if not isinstance(other, Resources):
            return False
        if self.resources == other.resources:
            return True
        return False

    @staticmethod
    def from_list(resources_list):
        """adds resources from a list to resources attribute by creating a new Resources object

        :param dict resources_list: absolute template path for stack creation
        :return: resources object with list of stack resources in resources attribute
        :rtype: Resources
        """
        resources_from_list = Resources()
        for stack_resource in resources_list:
            resources_from_list.add(stack_resource=stack_resource)
        return resources_from_list


class Resource:
    """
    Stack resource object containing LogicalResourceId, ResourceStatus and ResourceType fields of CloudFormation StackResource

    Only these three fields are needed for comparing equality as rest of the fields are generated by CloudFormation dynamically

    Methods
    -------
    :method __init__(self, logical_id, resource_type, resource_status)
        creates a Resource object by setting the logical_id, resource_type and resource_status
    :method __eq__(self, other)

    """

    def __init__(self, logical_id, resource_type, resource_status):
        """creates a Resource object by setting the logical_id, resource_type and resource_status

        :param str logical_id: logical id of the stack resource
        :param str resource_type: CloudFormation resource type of the resource
        :param str resource_status: desired resource status for the resource
        """
        self.logical_id = logical_id
        self.resource_type = resource_type
        self.resource_status = resource_status

    def __eq__(self, other):
        """compares equality of two objects of Resource type

        :param Resource other: Resource object that would be compared with self
        :return: returns True if both the objects are equal
        :rtype: bool
        """
        if not isinstance(other, Resource):
            return False
        return (
            self.logical_id == other.logical_id
            and self.resource_type == other.resource_type
            and self.resource_status == other.resource_status
        )
