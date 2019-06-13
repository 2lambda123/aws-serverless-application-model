# Help resolve intrinsic functions

from samtranslator.intrinsics.actions import Action, SubAction, RefAction, \
    GetAttAction, IfAction

# All intrinsics are supported by default
DEFAULT_SUPPORTED_INTRINSICS = {action.intrinsic_name: action() for action in
                                [RefAction, SubAction, GetAttAction, IfAction]}


class IntrinsicsResolver(object):

    def __init__(self, parameters,
                 supported_intrinsics=DEFAULT_SUPPORTED_INTRINSICS,
                 conditions={}):
        """
        Instantiate the resolver
        :param dict parameters: Map of parameter names to their values
        :param dict conditions: Map of condition names to their values
        :param dict supported_intrinsics: Dictionary of intrinsic functions this class supports along with the
            Action class that can process this intrinsic
        :raises TypeError: If parameters or the supported_intrinsics arguments are invalid
        """

        if parameters is None or not isinstance(parameters, dict):
            raise TypeError("parameters must be a valid dictionary")

        if conditions is None or not isinstance(conditions, dict):
            raise TypeError("parameters must be a valid dictionary")

        if not isinstance(supported_intrinsics, dict) \
                or not all([isinstance(value, Action) for value in supported_intrinsics.values()]):
            raise TypeError("supported_intrinsics argument must be intrinsic names to corresponding Action classes")

        self.supported_intrinsics = supported_intrinsics
        self.parameters = parameters
        self.conditions = conditions

    def resolve_parameter_refs(self, input):
        """
        Resolves references to parameters within the given dictionary recursively. Other intrinsic functions such as
        !GetAtt, !Sub or !Ref to non-parameters will be left untouched.

        Result is a dictionary where parameter values are inlined. Don't pass this dictionary directly into
        transform's output because it changes the template structure by inlining parameter values.

        :param input: Any primitive type (dict, array, string etc) whose values might contain intrinsic functions
        :return: A copy of a dictionary with parameter references replaced by actual value.
        """
        return self._traverse(input, self.parameters, self._try_resolve_parameter_refs)

    def resolve_condition_refs(self, input):
        """
        Resolves references to parameters within the given dictionary recursively. Other intrinsic functions such as
        !GetAtt, !Sub or !Ref to non-parameters will be left untouched.

        Result is a dictionary where parameter values are inlined. Don't pass this dictionary directly into
        transform's output because it changes the template structure by inlining parameter values.

        :param input: Any primitive type (dict, array, string etc) whose values might contain intrinsic functions
        :return: A copy of a dictionary with parameter references replaced by actual value.
        """
        return self._traverse(input, self.conditions, self._try_resolve_condition_refs)

    def resolve_sam_resource_refs(self, input, supported_resource_refs):
        """
        Customers can provide a reference to a "derived" SAM resource such as Alias of a Function or Stage of an API
        resource. This method recursively walks the tree, converting all derived references to the real resource name,
        if it is present.

        Example:
            {"Ref": "MyFunction.Alias"} -> {"Ref": "MyFunctionAliasLive"}

        This method does not attempt to validate a reference. If it is invalid or non-resolvable, it skips the
        occurrence and continues with the rest. It is recommended that you have an external process that detects and
        surfaces invalid references.

        For first call, it is recommended that `template` is the entire CFN template in order to handle
        references in Mapping or Output sections.

        :param dict input: CFN template that needs resolution. This method will modify the input
            directly resolving references. In subsequent recursions, this will be a fragment of the CFN template.
        :param SupportedResourceReferences supported_resource_refs: Object that contains information about the resource
            references supported in this SAM template, along with the value they should resolve to.
        :return list errors: List of dictionary containing information about invalid reference. Empty list otherwise
        """
        return self._traverse(input, supported_resource_refs, self._try_resolve_sam_resource_refs)

    def resolve_sam_resource_id_refs(self, input, supported_resource_id_refs):
        """
        Some SAM resources have their logical ids mutated from the original id that the customer writes in the
        template. This method recursively walks the tree and updates these logical ids from the old value
        to the new value that is generated by SAM.

        Example:
            {"Ref": "MyLayer"} -> {"Ref": "MyLayerABC123"}

        This method does not attempt to validate a reference. If it is invalid or non-resolvable, it skips the
        occurrence and continues with the rest. It is recommended that you have an external process that detects and
        surfaces invalid references.

        For first call, it is recommended that `template` is the entire CFN template in order to handle
        references in Mapping or Output sections.

        :param dict input: CFN template that needs resolution. This method will modify the input
            directly resolving references. In subsequent recursions, this will be a fragment of the CFN template.
        :param dict supported_resource_id_refs: Dictionary that maps old logical ids to new ones.
        :return list errors: List of dictionary containing information about invalid reference. Empty list otherwise
        """
        return self._traverse(input, supported_resource_id_refs, self._try_resolve_sam_resource_id_refs)

    def _traverse(self, input, resolution_data, resolver_method):
        """
        Driver method that performs the actual traversal of input and calls the appropriate `resolver_method` when
        to perform the resolution.

        :param input: Any primitive type  (dict, array, string etc) whose value might contain an intrinsic function
        :param resolution_data: Data that will help with resolution. For example, when resolving parameter references,
            this object will contain a dictionary of parameter names and their values.
        :param resolver_method: Method that will be called to actually resolve an intrinsic function. This method
            is called with the parameters `(input, resolution_data)`.
        :return: Modified `input` with intrinsics resolved
        """

        # There is data to help with resolution. Skip the traversal altogether
        if len(resolution_data) == 0:
            return input

        #
        # Traversal Algorithm:
        #
        # Imagine the input dictionary/list as a tree. We are doing a Pre-Order tree traversal here where we first
        # process the root node before going to its children. Dict and Lists are the only two iterable nodes.
        # Everything else is a leaf node.
        #
        # We do a Pre-Order traversal to handle the case where `input` contains intrinsic function as its only child
        # ie. input = {"Ref": "foo}.
        #
        # We will try to resolve the intrinsics if we can, otherwise return the original input. In some cases, resolving
        # an intrinsic will result in a terminal state ie. {"Ref": "foo"} could resolve to a string "bar". In other
        # cases, resolving intrinsics is only partial and we might need to continue traversing the tree (ex: Fn::Sub)
        # to handle nested intrinsics. All of these cases lend well towards a Pre-Order traversal where we try and
        # process the intrinsic, which results in a modified sub-tree to traverse.
        #

        input = resolver_method(input, resolution_data)

        if isinstance(input, dict):
            return self._traverse_dict(input, resolution_data, resolver_method)
        elif isinstance(input, list):
            return self._traverse_list(input, resolution_data, resolver_method)
        else:
            # We can iterate only over dict or list types. Primitive types are terminals
            return input

    def _traverse_dict(self, input_dict, resolution_data, resolver_method):
        """
        Traverse a dictionary to resolve intrinsic functions on every value

        :param input_dict: Input dictionary to traverse
        :param resolution_data: Data that the `resolver_method` needs to operate
        :param resolver_method: Method that can actually resolve an intrinsic function, if it detects one
        :return: Modified dictionary with values resolved
        """
        for key, value in input_dict.items():
            input_dict[key] = self._traverse(value, resolution_data, resolver_method)

        return input_dict

    def _traverse_list(self, input_list, resolution_data, resolver_method):
        """
        Traverse a list to resolve intrinsic functions on every element

        :param input_list: List of input
        :param resolution_data: Data that the `resolver_method` needs to operate
        :param resolver_method: Method that can actually resolve an intrinsic function, if it detects one
        :return: Modified list with intrinsic functions resolved
        """
        for index, value in enumerate(input_list):
            input_list[index] = self._traverse(value, resolution_data, resolver_method)

        return input_list

    def _try_resolve_parameter_refs(self, input, parameters):
        """
        Try to resolve parameter references on the given input object. The object could be of any type.
        If the input is not in the format used by intrinsics (ie. dictionary with one key), input is returned
        unmodified. If the single key in dictionary is one of the supported intrinsic function types,
        go ahead and try to resolve it.

        :param input: Input object to resolve
        :param parameters: Parameter values used to for ref substitution
        :return:
        """
        if not self._is_intrinsic_dict(input):
            return input

        function_type = list(input.keys())[0]
        return self.supported_intrinsics[function_type].resolve_parameter_refs(input, parameters)

    def _try_resolve_condition_refs(self, input, conditions):
        """
        Try to resolve conditions references on the given input object. The object could be of any type.
        If the input is not in the format used by intrinsics (ie. dictionary with one key), input is returned
        unmodified. If the single key in dictionary is one of the supported intrinsic function types,
        go ahead and try to resolve it.

        :param input: Input object to resolve
        :param parameters: Condition values used to for ref substitution
        :return:
        """
        if not self._is_intrinsic_dict(input):
            return input

        function_type = list(input.keys())[0]
        return self.supported_intrinsics[function_type].resolve_condition_refs(input, conditions)

    def _try_resolve_sam_resource_refs(self, input, supported_resource_refs):
        """
        Try to resolve SAM resource references on the given template. If the given object looks like one of the
        supported intrinsics, it calls the appropriate resolution on it. If not, this method returns the original input
        unmodified.

        :param dict input: Dictionary that may represent an intrinsic function
        :param SupportedResourceReferences supported_resource_refs: Object containing information about available
            resource references and the values they resolve to.
        :return: Modified input dictionary with references resolved
        """
        if not self._is_intrinsic_dict(input):
            return input

        function_type = list(input.keys())[0]
        return self.supported_intrinsics[function_type].resolve_resource_refs(input, supported_resource_refs)

    def _try_resolve_sam_resource_id_refs(self, input, supported_resource_id_refs):
        """
        Try to resolve SAM resource id references on the given template. If the given object looks like one of the
        supported intrinsics, it calls the appropriate resolution on it. If not, this method returns the original input
        unmodified.

        :param dict input: Dictionary that may represent an intrinsic function
        :param dict supported_resource_id_refs: Dictionary that maps old logical ids to new ones.
        :return: Modified input dictionary with id references resolved
        """
        if not self._is_intrinsic_dict(input):
            return input

        function_type = list(input.keys())[0]
        return self.supported_intrinsics[function_type].resolve_resource_id_refs(input, supported_resource_id_refs)

    def _is_intrinsic_dict(self, input):
        """
        Can the input represent an intrinsic function in it?

        :param input: Object to be checked
        :return: True, if the input contains a supported intrinsic function.  False otherwise
        """
        # All intrinsic functions are dictionaries with just one key
        return isinstance(input, dict) \
            and len(input) == 1 \
            and list(input.keys())[0] in self.supported_intrinsics
