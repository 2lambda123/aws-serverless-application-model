#!/usr/bin/env python
"""JSON file formatter (without prettier)."""
import os
import sys
from textwrap import dedent

my_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, my_path + "/..")

import re
from io import StringIO
from typing import Any, Dict, Type

# We use ruamel.yaml for parsing yaml files because it can preserve comments
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from bin._file_formatter import FileFormatter

yaml = YAML()
# We have pyyaml (5.4) to parse our yamls in this repo,
# and pyyaml uses Yaml 1.1
yaml.version = (1, 1)  # type: ignore


class YAMLFormatter(FileFormatter):
    @staticmethod
    def description() -> str:
        return "YAML file formatter"

    def format(self, input_str: str) -> str:
        """Opinionated format YAML file."""
        if self.args.add_test_metadata:
            # Since formatting integration test templates cause failure,
            # temporary workaround to add test metadata to integration test templates
            if "SamTransformTest" in input_str:
                return input_str
            return input_str + "\nMetadata:\n  SamTransformTest: true\n\n"

        obj = yaml.load(input_str)
        out_stream = StringIO()
        yaml.dump(
            obj,
            stream=out_stream,
        )
        # ruamel.yaml tends to add 2 empty lines at the bottom of the dump
        return re.sub(r"\n+$", "\n", out_stream.getvalue())

    @staticmethod
    def _add_test_metadata(obj: Dict[str, Any]) -> None:
        metadata = obj.get("Metadata", {})
        if not metadata:
            metadata = obj["Metadata"] = {}
        sam_transform_test_value = metadata.get("SamTransformTest")
        if sam_transform_test_value is not None and sam_transform_test_value is not True:
            raise ValueError(f"Unexpected Metadata.SamTransformTest value {sam_transform_test_value}")
        metadata["SamTransformTest"] = True

    @staticmethod
    def decode_exception() -> Type[Exception]:
        return YAMLError

    @staticmethod
    def file_extension() -> str:
        return ".yaml"

    @classmethod
    def config_additional_args(cls) -> None:
        cls.arg_parser.add_argument(
            "--add-test-metadata",
            action="store_true",
            help=dedent(
                """\
                Add the testing metadata to yaml file if it doesn't exist:
                "Metadata: SamTransformTest: true" """
            ),
        )


if __name__ == "__main__":
    YAMLFormatter.main()
