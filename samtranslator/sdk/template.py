from samtranslator.sdk.resource import SamResource

"""
Classes representing SAM template and resources.
"""


class SamTemplate(object):
    """
    Class representing the SAM template
    """

    def __init__(self, template_dict):  # type: ignore[no-untyped-def]
        """
        Initialize with a template dictionary, that contains "Resources" dictionary

        :param dict template_dict: Template Dictionary
        """
        self.template_dict = template_dict
        self.resources = template_dict["Resources"]

    def iterate(self, resource_types=None):  # type: ignore[no-untyped-def]
        """
        Iterate over all resources within the SAM template, optionally filtering by type

        :param dict resource_types: Optional types to filter the resources by
        :yields (string, SamResource): Tuple containing LogicalId and the resource
        """
        if resource_types is None:
            resource_types = {}
        for logicalId, resource_dict in self.resources.items():

            resource = SamResource(resource_dict)  # type: ignore[no-untyped-call]
            needs_filter = resource.valid()  # type: ignore[no-untyped-call]
            if resource_types:
                needs_filter = needs_filter and resource.type in resource_types

            if needs_filter:
                yield logicalId, resource

    def set(self, logicalId, resource):  # type: ignore[no-untyped-def]
        """
        Adds the resource to dictionary with given logical Id. It will overwrite, if the logicalId is already used.

        :param string logicalId: Logical Id to set to
        :param SamResource or dict resource: The actual resource data
        """

        resource_dict = resource
        if isinstance(resource, SamResource):
            resource_dict = resource.to_dict()  # type: ignore[no-untyped-call]

        self.resources[logicalId] = resource_dict

    def get(self, logicalId):  # type: ignore[no-untyped-def]
        """
        Gets the resource at the given logicalId if present

        :param string logicalId: Id of the resource
        :return SamResource: Resource, if available at the Id. None, otherwise
        """
        if logicalId not in self.resources:
            return None

        return SamResource(self.resources.get(logicalId))  # type: ignore[no-untyped-call]

    def delete(self, logicalId):  # type: ignore[no-untyped-def]
        """
        Deletes a resource at the given ID

        :param string logicalId: Resource to delete
        """

        if logicalId in self.resources:
            del self.resources[logicalId]

    def to_dict(self):  # type: ignore[no-untyped-def]
        """
        Returns the template as a dictionary

        :return dict: SAM template as a dictionary
        """
        self.template_dict["Resource"] = self.resources
        return self.template_dict
