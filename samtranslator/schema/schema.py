from __future__ import annotations

import argparse
import json
from pathlib import Path

import pydantic

from typing import Any, Dict, Type, Optional, Union


from samtranslator.schema.common import BaseModel, LenientBaseModel
from samtranslator.schema import (
    aws_serverless_simpletable,
    aws_serverless_application,
    aws_serverless_connector,
    aws_serverless_function,
    aws_serverless_statemachine,
    aws_serverless_layerversion,
    aws_serverless_api,
    aws_serverless_httpapi,
    any_cfn_resource,
)


class Globals(BaseModel):
    Function: Optional[aws_serverless_function.Globals]
    Api: Optional[aws_serverless_api.Globals]
    HttpApi: Optional[aws_serverless_httpapi.Globals]
    SimpleTable: Optional[aws_serverless_simpletable.Globals]


Resources = Union[
    aws_serverless_connector.Resource,
    aws_serverless_function.Resource,
    aws_serverless_simpletable.Resource,
    aws_serverless_statemachine.Resource,
    aws_serverless_layerversion.Resource,
    aws_serverless_api.Resource,
    aws_serverless_httpapi.Resource,
    aws_serverless_application.Resource,
]


class _ModelWithoutResources(LenientBaseModel):
    Globals: Optional[Globals]


class Model(_ModelWithoutResources):
    Resources: Dict[
        str,
        Union[
            Resources,
            any_cfn_resource.Resource,
        ],
    ]


class ModelFoo(_ModelWithoutResources):
    Resources: Dict[str, Resources]


def extend_with_cfn_schema(sam_schema: Dict[str, Any], cfn_schema: Dict[str, Any]) -> None:
    # TODO: Ensure not overwriting
    sam_schema["definitions"].update(cfn_schema["definitions"])

    cfn_props = cfn_schema["properties"]
    sam_schema["properties"]["Resources"]["additionalProperties"]["anyOf"].extend(
        cfn_props["Resources"]["patternProperties"]["^[a-zA-Z0-9]+$"]["anyOf"]
    )


def get_schema(model: Type[pydantic.BaseModel]) -> Dict[str, Any]:
    obj = Model.schema()

    # http://json-schema.org/understanding-json-schema/reference/schema.html#schema
    # https://github.com/pydantic/pydantic/issues/1478
    # Validated in https://github.com/aws/serverless-application-model/blob/5c82f5d2ae95adabc9827398fba8ccfc3dbe101a/tests/schema/test_validate_schema.py#L91
    obj["$schema"] = "http://json-schema.org/draft-04/schema#"

    return obj


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sam-schema", type=Path, required=True)
    parser.add_argument("--cfn-schema", type=Path, required=True)
    parser.add_argument("--unified-schema", type=Path, required=True)
    args = parser.parse_args()

    obj = get_schema(Model)

    def json_dumps(obj: Any) -> str:
        return json.dumps(obj, indent=2, sort_keys=True) + "\n"

    args.sam_schema.write_text(json_dumps(obj))

    cfn_schema = json.loads(args.cfn_schema.read_text())

    obj = get_schema(ModelFoo)
    extend_with_cfn_schema(obj, cfn_schema)

    args.unified_schema.write_text(json_dumps(obj))


if __name__ == "__main__":
    main()
