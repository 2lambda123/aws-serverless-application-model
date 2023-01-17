import json
from io import BytesIO
from time import sleep
from unittest.mock import call, patch, Mock

from botocore.exceptions import ClientError
from parameterized import parameterized, param
from unittest import TestCase
import os, sys

from samtranslator.feature_toggle.feature_toggle import (
    FeatureToggle,
    FeatureToggleLocalConfigProvider,
    FeatureToggleAppConfigConfigProvider,
)
from samtranslator.feature_toggle.dialup import ToggleDialup, SimpleAccountPercentileDialup, DisabledDialup

my_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, my_path + "/..")


class TestFeatureToggle(TestCase):
    @parameterized.expand(
        [
            param("feature-1", "beta", "default", "123456789123", False),
            param("feature-1", "beta", "us-west-2", "123456789123", True),
            param("feature-2", "beta", "us-west-2", "123456789123", False),  # because feature is missing
            param("feature-1", "beta", "ap-south-1", "123456789124", False),  # because default is used
            param("feature-1", "alpha", "us-east-1", "123456789123", False),  # non-exist stage
            param("feature-1", "beta", "us-east-1", "123456789100", True),
            param("feature-1", "beta", "us-east-1", "123456789123", False),
            # any None for stage, region and account_id should return False
            param("feature-1", None, None, None, False),
            param("feature-1", "beta", None, None, False),
            param("feature-1", "beta", "us-west-2", None, False),
            param("feature-1", "beta", None, "123456789123", False),
        ]
    )
    def test_feature_toggle_with_local_provider(self, feature_name, stage, region, account_id, expected):
        feature_toggle = FeatureToggle(
            FeatureToggleLocalConfigProvider(os.path.join(my_path, "input", "feature_toggle_config.json")),
            stage=stage,
            region=region,
            account_id=account_id,
        )
        self.assertEqual(feature_toggle.is_enabled(feature_name), expected)

    @parameterized.expand(
        [
            param("toggle", ToggleDialup),
            param("account-percentile", SimpleAccountPercentileDialup),
            param("something-else", DisabledDialup),
        ]
    )
    def test__get_dialup(self, dialup_type, expected_class):
        feature_toggle = FeatureToggle(
            FeatureToggleLocalConfigProvider(os.path.join(my_path, "input", "feature_toggle_config.json")),
            stage=None,
            region=None,
            account_id=None,
        )
        region_config = {"type": dialup_type}
        dialup = feature_toggle._get_dialup(region_config, "some-feature")
        self.assertIsInstance(dialup, expected_class)


class TestFeatureToggleAppConfig(TestCase):
    def setUp(self):
        self.content_stream_mock = Mock()
        self.content_stream_mock.read.return_value = b"""
        {
            "feature-1": {
                "beta": {
                    "us-west-2": {"type": "toggle", "enabled": true},
                    "us-east-1": {"type": "account-percentile", "enabled-%": 10},
                    "default": {"type": "toggle", "enabled": false},
                    "123456789123": {
                        "us-west-2": {"type": "toggle", "enabled": true},
                        "default": {"type": "toggle", "enabled": false}
                    }
                },
                "gamma": {
                    "default": {"type": "toggle", "enabled": false},
                    "123456789123": {
                        "us-east-1": {"type": "toggle", "enabled": false},
                        "default": {"type": "toggle", "enabled": false}
                    }
                },
                "prod": {"default": {"type": "toggle", "enabled": false}}
            }
        }
        """
        self.app_config_data_mock = Mock()
        self.app_config_data_mock.start_configuration_session.return_value = {
            "InitialConfigurationToken": "init-token",
        }
        self.app_config_data_mock.get_latest_configuration.return_value = {
            "NextPollConfigurationToken": "next-token",
            "NextPollIntervalInSeconds": 597,
            "Configuration": self.content_stream_mock,
        }

    @parameterized.expand(
        [
            param("feature-1", "beta", "default", "123456789123", False),
            param("feature-1", "beta", "us-west-2", "123456789123", True),
            param("feature-2", "beta", "us-west-2", "123456789123", False),  # because feature is missing
            param("feature-1", "beta", "ap-south-1", "123456789124", False),  # because default is used
            param("feature-1", "alpha", "us-east-1", "123456789123", False),  # non-exist stage
            param("feature-1", "beta", "us-east-1", "123456789100", True),
            param("feature-1", "beta", "us-east-1", "123456789123", False),
            # any None for stage, region and account_id returns False
            param("feature-1", None, None, None, False),
            param("feature-1", "beta", None, None, False),
            param("feature-1", "beta", "us-west-2", None, False),
            param("feature-1", "beta", None, "123456789123", False),
        ]
    )
    @patch("samtranslator.feature_toggle.feature_toggle.boto3")
    @patch("samtranslator.feature_toggle.feature_toggle.Config")
    def test_feature_toggle_with_appconfig_provider(
        self, feature_name, stage, region, account_id, expected, config_mock, boto3_mock
    ):
        boto3_mock.client.return_value = self.app_config_data_mock
        config_object_mock = Mock()
        config_mock.return_value = config_object_mock
        feature_toggle_config_provider = FeatureToggleAppConfigConfigProvider(
            "test_app_id", "test_env_id", "test_conf_id"
        )
        feature_toggle = FeatureToggle(
            feature_toggle_config_provider, stage=stage, region=region, account_id=account_id
        )
        boto3_mock.client.assert_called_once_with("appconfigdata", config=config_object_mock)
        self.assertEqual(feature_toggle.is_enabled(feature_name), expected)

    @parameterized.expand(
        [
            param("feature-1", "beta", "default", "123456789123", False),
            param("feature-1", "beta", "us-west-2", "123456789123", True),
            param("feature-2", "beta", "us-west-2", "123456789123", False),  # because feature is missing
            param("feature-1", "beta", "ap-south-1", "123456789124", False),  # because default is used
            param("feature-1", "alpha", "us-east-1", "123456789123", False),  # non-exist stage
            param("feature-1", "beta", "us-east-1", "123456789100", True),
            param("feature-1", "beta", "us-east-1", "123456789123", False),
            # any None for stage, region and account_id returns False
            param("feature-1", None, None, None, False),
            param("feature-1", "beta", None, None, False),
            param("feature-1", "beta", "us-west-2", None, False),
            param("feature-1", "beta", None, "123456789123", False),
        ]
    )
    @patch("samtranslator.feature_toggle.feature_toggle.boto3")
    def test_feature_toggle_with_appconfig_provider_and_app_config_client(
        self, feature_name, stage, region, account_id, expected, boto3_mock
    ):
        feature_toggle_config_provider = FeatureToggleAppConfigConfigProvider(
            "test_app_id", "test_env_id", "test_conf_id", self.app_config_data_mock
        )
        feature_toggle = FeatureToggle(
            feature_toggle_config_provider, stage=stage, region=region, account_id=account_id
        )
        boto3_mock.client.assert_not_called()
        self.assertEqual(feature_toggle.is_enabled(feature_name), expected)


class TestFeatureToggleAppConfigConfigProvider(TestCase):
    @patch("samtranslator.feature_toggle.feature_toggle.boto3")
    def test_feature_toggle_with_exception(self, boto3_mock):
        boto3_mock.client.raiseError.side_effect = Exception()
        feature_toggle_config_provider = FeatureToggleAppConfigConfigProvider(
            "test_app_id", "test_env_id", "test_conf_id"
        )
        self.assertEqual(feature_toggle_config_provider.config, {})

    @patch("samtranslator.feature_toggle.feature_toggle.boto3.client")
    def test_ignoring_empty_response(self, client_mock):
        """AppConfig gives empty response when client is already up-to-date."""
        appconfigdata_mock = client_mock.return_value = Mock()
        appconfigdata_mock.start_configuration_session.return_value = {
            "InitialConfigurationToken": "init-token",
        }
        appconfigdata_mock.get_latest_configuration.side_effect = [
            {
                "NextPollConfigurationToken": "next-token-1",
                "NextPollIntervalInSeconds": -1,  # force to refresh
                "Configuration": BytesIO(json.dumps({"hello": "world"}).encode("utf-8")),
            },
            {
                "NextPollConfigurationToken": "next-token-2",
                "NextPollIntervalInSeconds": -1,  # force to refresh
                "Configuration": BytesIO(b""),
            },
        ]
        feature_toggle_config_provider = FeatureToggleAppConfigConfigProvider(
            "test_app_id",
            "test_env_id",
            "test_conf_id",
        )
        self.assertEqual(feature_toggle_config_provider.config, {"hello": "world"})

        # Make sure it calls get_latest_configuration twice and ignore empty response indeed happened.
        self.assertEqual(appconfigdata_mock.get_latest_configuration.call_count, 2)
        appconfigdata_mock.get_latest_configuration.assert_has_calls(
            [call(ConfigurationToken="init-token"), call(ConfigurationToken="next-token-1")]
        )

    @patch("samtranslator.feature_toggle.feature_toggle.boto3.client")
    def test_reset_session_when_get_latest_configuration_failed(self, client_mock):
        """AppConfig gives empty response when client is already up-to-date."""
        appconfigdata_mock = client_mock.return_value = Mock()
        appconfigdata_mock.start_configuration_session.side_effect = [
            {
                "InitialConfigurationToken": "init-token-1",
            },
            {
                "InitialConfigurationToken": "init-token-2",
            },
        ]
        appconfigdata_mock.get_latest_configuration.side_effect = [
            ClientError({}, "GetLatestConfiguration"),
            {
                "NextPollConfigurationToken": "next-token-1",
                "NextPollIntervalInSeconds": -1,  # force to refresh
                "Configuration": BytesIO(json.dumps({"hello": "world"}).encode("utf-8")),
            },
            {
                "NextPollConfigurationToken": "next-token-2",
                "NextPollIntervalInSeconds": -1,  # force to refresh
                "Configuration": BytesIO(json.dumps({"hello": "world"}).encode("utf-8")),
            },
        ]
        feature_toggle_config_provider = FeatureToggleAppConfigConfigProvider(
            "test_app_id",
            "test_env_id",
            "test_conf_id",
        )
        self.assertEqual(feature_toggle_config_provider.config, {"hello": "world"})

        # Make sure it calls get_latest_configuration twice and ignore empty response indeed happened.
        self.assertEqual(appconfigdata_mock.get_latest_configuration.call_count, 3)
        appconfigdata_mock.get_latest_configuration.assert_has_calls(
            [
                call(ConfigurationToken="init-token-1"),
                call(ConfigurationToken="init-token-2"),
                call(ConfigurationToken="next-token-1"),
            ]
        )

    @patch("samtranslator.feature_toggle.feature_toggle.boto3.client")
    def test_only_refresh_when_past_due(self, client_mock):
        """AppConfig gives empty response when client is already up-to-date."""
        appconfigdata_mock = client_mock.return_value = Mock()
        appconfigdata_mock.start_configuration_session.return_value = {
            "InitialConfigurationToken": "init-token",
        }
        appconfigdata_mock.get_latest_configuration.side_effect = [
            {
                "NextPollConfigurationToken": "next-token-1",
                "NextPollIntervalInSeconds": 5,  # force to refresh
                "Configuration": BytesIO(json.dumps({"hello": "world"}).encode("utf-8")),
            },
            {
                "NextPollConfigurationToken": "next-token-2",
                "NextPollIntervalInSeconds": 500,  # force to refresh
                "Configuration": BytesIO(json.dumps({"hello": "world??"}).encode("utf-8")),
            },
        ]
        feature_toggle_config_provider = FeatureToggleAppConfigConfigProvider(
            "test_app_id",
            "test_env_id",
            "test_conf_id",
        )
        self.assertEqual(feature_toggle_config_provider.config, {"hello": "world"})  # initial fetch
        self.assertEqual(feature_toggle_config_provider.config, {"hello": "world"})  # refresh should be skipped
        sleep(6)  # now it is due for another refresh
        self.assertEqual(feature_toggle_config_provider.config, {"hello": "world??"})

        # Make sure it calls get_latest_configuration twice and ignore empty response indeed happened.
        self.assertEqual(appconfigdata_mock.get_latest_configuration.call_count, 2)
        appconfigdata_mock.get_latest_configuration.assert_has_calls(
            [
                call(ConfigurationToken="init-token"),
                call(ConfigurationToken="next-token-1"),
            ]
        )
