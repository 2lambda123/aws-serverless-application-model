from samtranslator.translator.arn_generator import ArnGenerator


def get_xray_managed_policy_name():  # type: ignore[no-untyped-def]
    # use previous (old) policy name for regular regions
    # for china and gov regions, use the newer policy name
    partition_name = ArnGenerator.get_partition_name()  # type: ignore[no-untyped-call]
    if partition_name == "aws":
        return "AWSXrayWriteOnlyAccess"
    return "AWSXRayDaemonWriteAccess"
