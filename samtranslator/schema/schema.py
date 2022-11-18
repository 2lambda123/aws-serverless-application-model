from __future__ import annotations

from enum import Enum
from typing_extensions import Literal
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel as LenientBaseModel
from pydantic import Extra, Field, constr

Unknown = Optional[Any]


# By default strict
# https://pydantic-docs.helpmanual.io/usage/model_config/#change-behaviour-globally
class BaseModel(LenientBaseModel):
    class Config:
        extra = Extra.forbid


class ResourceReference(BaseModel):
    Id: Optional[str]
    Arn: Unknown
    Name: Unknown
    Qualifier: Unknown
    QueueUrl: Unknown
    ResourceId: Unknown
    RoleName: Unknown
    Type: Unknown


class ConnectorProperties(BaseModel):
    Source: ResourceReference
    Destination: ResourceReference
    Permissions: List[Literal["Read", "Write"]]


class AwsServerlessConnector(BaseModel):
    Type: Literal["AWS::Serverless::Connector"]
    Properties: ConnectorProperties


class FunctionProperties(BaseModel):
    Architectures: Unknown
    AssumeRolePolicyDocument: Unknown
    AutoPublishAlias: Unknown
    AutoPublishCodeSha256: Unknown
    CodeSigningConfigArn: Unknown
    CodeUri: Unknown
    DeadLetterQueue: Unknown
    DeploymentPreference: Unknown
    Description: Unknown
    Environment: Unknown
    EphemeralStorage: Unknown
    EventInvokeConfig: Unknown
    Events: Unknown
    FileSystemConfigs: Unknown
    FunctionName: Unknown
    FunctionUrlConfig: Unknown
    Handler: Unknown
    ImageConfig: Unknown
    ImageUri: Unknown
    InlineCode: Unknown
    KmsKeyArn: Unknown
    Layers: Unknown
    MemorySize: Unknown
    PackageType: Unknown
    PermissionsBoundary: Unknown
    Policies: Unknown
    ProvisionedConcurrencyConfig: Unknown
    ReservedConcurrentExecutions: Unknown
    Role: Unknown
    Runtime: Unknown
    Tags: Unknown
    Timeout: Unknown
    Tracing: Unknown
    VersionDescription: Unknown
    VpcConfig: Unknown


class AwsServerlessFunction(BaseModel):
    Type: Literal["AWS::Serverless::Function"]
    Properties: FunctionProperties
    Condition: Unknown
    DependsOn: Unknown


class SimpleTableProperties(BaseModel):
    PrimaryKey: Unknown
    ProvisionedThroughput: Unknown
    SSESpecification: Unknown
    TableName: Unknown
    Tags: Unknown


class AwsServerlessSimpleTable(BaseModel):
    Type: Literal["AWS::Serverless::SimpleTable"]
    Properties: Optional[SimpleTableProperties]


class StateMachineProperties(BaseModel):
    Definition: Unknown
    DefinitionSubstitutions: Unknown
    DefinitionUri: Unknown
    Events: Unknown
    Logging: Unknown
    Name: Unknown
    PermissionsBoundary: Unknown
    Policies: Unknown
    Role: Unknown
    Tags: Unknown
    Tracing: Unknown
    Type: Unknown


class AwsServerlessStateMachine(BaseModel):
    Type: Literal["AWS::Serverless::StateMachine"]
    Properties: StateMachineProperties


class LayerVersionProperties(BaseModel):
    CompatibleArchitectures: Unknown
    CompatibleRuntimes: Unknown
    ContentUri: Unknown
    Description: Unknown
    LayerName: Unknown
    LicenseInfo: Unknown
    RetentionPolicy: Unknown


class AwsServerlessLayerVersion(BaseModel):
    Type: Literal["AWS::Serverless::LayerVersion"]
    Properties: LayerVersionProperties
    Condition: Unknown


class ApiProperties(BaseModel):
    AccessLogSetting: Unknown
    ApiKeySourceType: Unknown
    Auth: Unknown
    BinaryMediaTypes: Unknown
    CacheClusterEnabled: Unknown
    CacheClusterSize: Unknown
    CanarySetting: Unknown
    Cors: Unknown
    DefinitionBody: Unknown
    DefinitionUri: Unknown
    Description: Unknown
    DisableExecuteApiEndpoint: Unknown
    Domain: Unknown
    EndpointConfiguration: Unknown
    FailOnWarnings: Unknown
    GatewayResponses: Unknown
    MethodSettings: Unknown
    MinimumCompressionSize: Unknown
    Mode: Unknown
    Models: Unknown
    Name: Unknown
    OpenApiVersion: Unknown
    StageName: Unknown
    Tags: Unknown
    TracingEnabled: Unknown
    Variables: Unknown


class AwsServerlessApi(BaseModel):
    Type: Literal["AWS::Serverless::Api"]
    Properties: ApiProperties
    Condition: Unknown


class HttpApiProperties(BaseModel):
    AccessLogSettings: Unknown
    Auth: Unknown
    CorsConfiguration: Unknown
    DefaultRouteSettings: Unknown
    DefinitionBody: Unknown
    DefinitionUri: Unknown
    Description: Unknown
    DisableExecuteApiEndpoint: Unknown
    Domain: Unknown
    FailOnWarnings: Unknown
    RouteSettings: Unknown
    StageName: Unknown
    StageVariables: Unknown
    Tags: Unknown


class AwsServerlessHttpApi(BaseModel):
    Type: Literal["AWS::Serverless::HttpApi"]
    Properties: Optional[HttpApiProperties]


class ApplicationProperties(BaseModel):
    Location: Unknown
    NotificationARNs: Unknown
    Parameters: Unknown
    Tags: Unknown
    TimeoutInMinutes: Unknown


class AwsServerlessApplication(BaseModel):
    Type: Literal["AWS::Serverless::Application"]
    Properties: ApplicationProperties
    Condition: Unknown


# Match anything not containing Serverless
class AnyCfnResource(LenientBaseModel):
    Type: constr(regex=r"^((?!::Serverless::).)*$")  # type: ignore


class Model(LenientBaseModel):
    Resources: Dict[
        str,
        Union[
            AwsServerlessConnector,
            AwsServerlessFunction,
            AwsServerlessSimpleTable,
            AwsServerlessStateMachine,
            AwsServerlessLayerVersion,
            AwsServerlessApi,
            AwsServerlessHttpApi,
            AnyCfnResource,
            AwsServerlessApplication,
        ],
    ]


if __name__ == "__main__":
    print(Model.schema_json(indent=2))
