from samtranslator.model import PropertyType, Resource
from samtranslator.model.intrinsics import fnGetAtt, ref
from samtranslator.model.types import is_type, dict_of, list_of, is_str, one_of


class DynamoDBTable(Resource):
    resource_type = 'AWS::DynamoDB::Table'
    property_types = {
        'AttributeDefinitions': PropertyType(True, list_of(is_type(dict))),
        'GlobalSecondaryIndexes': PropertyType(False, list_of(is_type(dict))),
        'KeySchema': PropertyType(False, list_of(is_type(dict))),
        'LocalSecondaryIndexes': PropertyType(False, list_of(is_type(dict))),
        'ProvisionedThroughput': PropertyType(True, dict_of(is_str(), one_of(is_type(int), is_type(dict)))),
        'StreamSpecification': PropertyType(False, is_type(dict)),
        'TableName': PropertyType(False, one_of(is_str(), is_type(dict))),
        'Tags': PropertyType(False, list_of(is_type(dict)))
    }

    runtime_attrs = {
        "name": lambda self: ref(self.logical_id),
        "arn": lambda self: fnGetAtt(self.logical_id, "Arn"),
        "stream_arn": lambda self: fnGetAtt(self.logical_id, "StreamArn")
    }
