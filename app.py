#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  AuroraMysqlStack,
  KinesisDataStreamStack,
  DMSAuroraMysqlToKinesisStack,
  GlueJobRoleStack,
  GlueStreamDataSchemaStack,
  GlueStreamingJobStack,
  DataLakePermissionsStack
)

APP_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

vpc_stack = VpcStack(app, 'TransactionalDataLakeVpc', env=APP_ENV)

aurora_mysql_stack = AuroraMysqlStack(app, 'AuroraMysqlAsDMSDataSource',
  vpc_stack.vpc
)
aurora_mysql_stack.add_dependency(vpc_stack)

kds_stack = KinesisDataStreamStack(app, 'DMSTargetKinesisDataStream')
kds_stack.add_dependency(aurora_mysql_stack)

dms_stack = DMSAuroraMysqlToKinesisStack(app, 'DMSTaskAuroraMysqlToKinesis',
  vpc_stack.vpc,
  aurora_mysql_stack.sg_mysql_client,
  kds_stack.kinesis_stream.stream_arn
)
dms_stack.add_dependency(kds_stack)

glue_job_role = GlueJobRoleStack(app, 'GlueStreamingCDCtoIcebergJobRole')
glue_job_role.add_dependency(kds_stack)

glue_stream_schema = GlueStreamDataSchemaStack(app, 'GlueTableSchemaOnKinesisStream',
  kds_stack.kinesis_stream
)
glue_stream_schema.add_dependency(glue_job_role)

grant_lake_formation_permissions = DataLakePermissionsStack(app, 'GrantLFPermissionsOnGlueJobRole',
  glue_job_role.glue_job_role
)
grant_lake_formation_permissions.add_dependency(glue_job_role)
grant_lake_formation_permissions.add_dependency(glue_stream_schema)

glue_streaming_job = GlueStreamingJobStack(app, 'GlueStreamingCDCtoIceberg',
  glue_job_role.glue_job_role
)
glue_streaming_job.add_dependency(grant_lake_formation_permissions)

app.synth()
