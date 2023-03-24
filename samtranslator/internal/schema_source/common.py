import json
import os
from functools import partial
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar, Union

import pydantic
from pydantic import Extra, Field

from samtranslator.model.types import PassThrough


# If using PassThrough as-is, pydantic will mark the field as not required:
#  - https://github.com/pydantic/pydantic/issues/990
#  - https://github.com/pydantic/pydantic/issues/1223
#
# That isn't what we want; we want it to specify any type, but still required.
# Using a class gets around it.
class PassThroughProp(pydantic.BaseModel):
    __root__: PassThrough


# Intrinsic resolvable by the SAM transform
T = TypeVar("T")
SamIntrinsicable = Union[Dict[str, Any], T]
SamIntrinsic = Dict[str, Any]

# TODO: Get rid of this in favor of proper types
Unknown = Optional[Any]

DictStrAny = Dict[str, Any]

LenientBaseModel = pydantic.BaseModel

_docdir = os.path.dirname(os.path.abspath(__file__))
_DOCS = json.loads(Path(_docdir, "sam-docs.json").read_bytes())


def get_prop(stem: str) -> Any:
    return partial(_get_prop, stem)


def passthrough_prop(sam_docs_stem: str, sam_docs_name: str, prop_path: List[str]) -> Any:
    """
    Specifies a pass-through field, where resource_type is the CloudFormation
    resource type, and path is a `#`-delimitated path to the property.
    """
    # need to change separator... sometimes contains dot
    prop_path = f"definitions#" + f"#properties#".join(prop_path)
    docs = _DOCS["properties"][sam_docs_stem][sam_docs_name]
    return Field(
        # We add a custom value to the schema containing the path to the pass-through
        # documentation; the dict containing the value is replaced in the final schema
        __samPassThrough={
            # To know at schema build-time where to find the property schema
            "schemaPath": prop_path,
            # Use SAM docs at the top-level pass-through; it can include useful SAM-specific information
            "markdownDescriptionOverride": docs,
        },
    )


def _get_prop(stem: str, name: str) -> Any:
    docs = _DOCS["properties"][stem][name]
    return Field(
        title=name,
        description=docs,
        # https://code.visualstudio.com/docs/languages/json#_use-rich-formatting-in-hovers
        markdownDescription=docs,
    )


# By default strict: https://pydantic-docs.helpmanual.io/usage/model_config/#change-behaviour-globally
class BaseModel(LenientBaseModel):
    class Config:
        extra = Extra.forbid

    def __getattribute__(self, __name: str) -> Any:
        """Overloading get attribute operation to allow access PassThroughProp without using __root__"""
        attr_value = super().__getattribute__(__name)
        if isinstance(attr_value, PassThroughProp):
            # See docstring of PassThroughProp
            return attr_value.__root__
        return attr_value


# https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-ref.html
class Ref(BaseModel):
    Ref: str


class ResourceAttributes(BaseModel):
    DependsOn: Optional[PassThroughProp]
    DeletionPolicy: Optional[PassThroughProp]
    Metadata: Optional[PassThroughProp]
    UpdateReplacePolicy: Optional[PassThroughProp]
    Condition: Optional[PassThroughProp]
