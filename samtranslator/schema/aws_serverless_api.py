from typing import Optional, Any, Dict, Union, List

from typing_extensions import Literal

from samtranslator.schema.common import PassThrough, BaseModel, SamIntrinsicable


class ResourcePolicy(BaseModel):
    AwsAccountBlacklist: Optional[List[Union[str, Dict[str, Any]]]]
    AwsAccountWhitelist: Optional[List[Union[str, Dict[str, Any]]]]
    CustomStatements: Optional[List[Union[str, Dict[str, Any]]]]
    IntrinsicVpcBlacklist: Optional[List[Union[str, Dict[str, Any]]]]
    IntrinsicVpcWhitelist: Optional[List[Union[str, Dict[str, Any]]]]
    IntrinsicVpceBlacklist: Optional[List[Union[str, Dict[str, Any]]]]
    IntrinsicVpceWhitelist: Optional[List[Union[str, Dict[str, Any]]]]
    IpRangeBlacklist: Optional[List[Union[str, Dict[str, Any]]]]
    IpRangeWhitelist: Optional[List[Union[str, Dict[str, Any]]]]
    SourceVpcBlacklist: Optional[List[Union[str, Dict[str, Any]]]]
    SourceVpcWhitelist: Optional[List[Union[str, Dict[str, Any]]]]


class CognitoAuthorizerIdentity(BaseModel):
    Header: Optional[str]
    ReauthorizeEvery: Optional[SamIntrinsicable[int]]
    ValidationExpression: Optional[str]


class CognitoAuthorizer(BaseModel):
    AuthorizationScopes: Optional[List[str]]
    Identity: Optional[CognitoAuthorizerIdentity]
    UserPoolArn: SamIntrinsicable[str]


class LambdaTokenAuthorizerIdentity(BaseModel):
    ReauthorizeEvery: Optional[SamIntrinsicable[int]]
    ValidationExpression: Optional[str]
    Header: Optional[
        str
    ]  # TODO: This doesn't exist in docs: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-property-api-lambdatokenauthorizationidentity.html


class LambdaRequestAuthorizerIdentity(BaseModel):
    Context: Optional[List[str]]
    Headers: Optional[List[str]]
    QueryStrings: Optional[List[str]]
    ReauthorizeEvery: Optional[SamIntrinsicable[int]]
    StageVariables: Optional[List[str]]


class LambdaTokenAuthorizer(BaseModel):
    AuthorizationScopes: Optional[List[str]]
    FunctionArn: SamIntrinsicable[str]
    FunctionInvokeRole: Optional[str]
    FunctionPayloadType: Optional[Literal["TOKEN"]]
    Identity: Optional[LambdaTokenAuthorizerIdentity]


class LambdaRequestAuthorizer(BaseModel):
    AuthorizationScopes: Optional[List[str]]
    FunctionArn: SamIntrinsicable[str]
    FunctionInvokeRole: Optional[str]
    FunctionPayloadType: Optional[Literal["REQUEST"]]
    Identity: Optional[LambdaRequestAuthorizerIdentity]


class UsagePlan(BaseModel):
    CreateUsagePlan: SamIntrinsicable[Literal["PER_API", "SHARED", "NONE"]]
    Description: Optional[PassThrough]
    Quota: Optional[PassThrough]
    Tags: Optional[PassThrough]
    Throttle: Optional[PassThrough]
    UsagePlanName: Optional[PassThrough]


class Auth(BaseModel):
    AddDefaultAuthorizerToCorsPreflight: Optional[bool]
    ApiKeyRequired: Optional[bool]
    Authorizers: Optional[
        Dict[
            str,
            Union[
                CognitoAuthorizer,
                LambdaTokenAuthorizer,
                LambdaRequestAuthorizer,
            ],
        ]
    ]
    DefaultAuthorizer: Optional[str]
    InvokeRole: Optional[str]
    ResourcePolicy: Optional[ResourcePolicy]
    UsagePlan: Optional[UsagePlan]


class Cors(BaseModel):
    AllowCredentials: Optional[bool]
    AllowHeaders: Optional[str]
    AllowMethods: Optional[str]
    AllowOrigin: str
    MaxAge: Optional[str]


class Route53(BaseModel):
    DistributionDomainName: Optional[PassThrough]
    EvaluateTargetHealth: Optional[PassThrough]
    HostedZoneId: Optional[PassThrough]
    HostedZoneName: Optional[PassThrough]
    IpV6: Optional[bool]


class Domain(BaseModel):
    BasePath: Optional[PassThrough]
    CertificateArn: PassThrough
    DomainName: PassThrough
    EndpointConfiguration: Optional[SamIntrinsicable[Literal["REGIONAL", "EDGE"]]]
    MutualTlsAuthentication: Optional[PassThrough]
    OwnershipVerificationCertificateArn: Optional[PassThrough]
    Route53: Optional[Route53]
    SecurityPolicy: Optional[PassThrough]


class DefinitionUri(BaseModel):
    Bucket: PassThrough
    Key: PassThrough
    Version: Optional[PassThrough]


class EndpointConfiguration(BaseModel):
    Type: Optional[PassThrough]
    VPCEndpointIds: Optional[PassThrough]


Name = Optional[PassThrough]
DefinitionUriType = Optional[Union[str, DefinitionUri]]
CacheClusterEnabled = Optional[PassThrough]
CacheClusterSize = Optional[PassThrough]
Variables = Optional[PassThrough]
EndpointConfigurationType = Optional[SamIntrinsicable[EndpointConfiguration]]
MethodSettings = Optional[PassThrough]
BinaryMediaTypes = Optional[PassThrough]
MinimumCompressionSize = Optional[PassThrough]
CorsType = Optional[SamIntrinsicable[Union[str, Cors]]]
GatewayResponses = Optional[Dict[str, Any]]
AccessLogSetting = Optional[PassThrough]
CanarySetting = Optional[PassThrough]
TracingEnabled = Optional[PassThrough]
OpenApiVersion = Optional[Union[float, str]]  # TODO: float doesn't exist in documentation


class Properties(BaseModel):
    AccessLogSetting: Optional[AccessLogSetting]
    ApiKeySourceType: Optional[PassThrough]
    Auth: Optional[Auth]
    BinaryMediaTypes: Optional[BinaryMediaTypes]
    CacheClusterEnabled: Optional[CacheClusterEnabled]
    CacheClusterSize: Optional[CacheClusterSize]
    CanarySetting: Optional[CanarySetting]
    Cors: Optional[CorsType]
    DefinitionBody: Optional[Dict[str, Any]]
    DefinitionUri: Optional[DefinitionUriType]
    Description: Optional[PassThrough]
    DisableExecuteApiEndpoint: Optional[PassThrough]
    Domain: Optional[Domain]
    EndpointConfiguration: Optional[EndpointConfigurationType]
    FailOnWarnings: Optional[PassThrough]
    GatewayResponses: Optional[GatewayResponses]
    MethodSettings: Optional[MethodSettings]
    MinimumCompressionSize: Optional[MinimumCompressionSize]
    Mode: Optional[PassThrough]
    Models: Optional[Dict[str, Any]]
    Name: Optional[Name]
    OpenApiVersion: Optional[OpenApiVersion]
    StageName: SamIntrinsicable[str]
    Tags: Optional[Dict[str, Any]]
    TracingEnabled: Optional[TracingEnabled]
    Variables: Optional[Variables]


class Globals(BaseModel):
    Auth: Optional[Auth]
    Name: Optional[Name]
    DefinitionUri: Optional[PassThrough]
    CacheClusterEnabled: Optional[CacheClusterEnabled]
    CacheClusterSize: Optional[CacheClusterSize]
    Variables: Optional[Variables]
    EndpointConfiguration: Optional[PassThrough]
    MethodSettings: Optional[MethodSettings]
    BinaryMediaTypes: Optional[BinaryMediaTypes]
    MinimumCompressionSize: Optional[MinimumCompressionSize]
    Cors: Optional[CorsType]
    GatewayResponses: Optional[GatewayResponses]
    AccessLogSetting: Optional[AccessLogSetting]
    CanarySetting: Optional[CanarySetting]
    TracingEnabled: Optional[TracingEnabled]
    OpenApiVersion: Optional[OpenApiVersion]
    Domain: Optional[Domain]


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::Api"]
    Properties: Properties
    Condition: Optional[PassThrough]
    DeletionPolicy: Optional[PassThrough]
    UpdatePolicy: Optional[PassThrough]
    UpdateReplacePolicy: Optional[PassThrough]
    DependsOn: Optional[PassThrough]
    Metadata: Optional[PassThrough]
