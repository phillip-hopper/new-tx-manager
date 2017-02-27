from __future__ import unicode_literals, print_function
import os
import shutil
import tempfile
import uuid
from unittest import TestCase

from mock import patch

from general_tools.file_utils import load_json_object, make_dir
from integration_tests.helpers import JsonObject

from lambda_handlers.client_webhook_handler import ClientWebhookHandler
from lambda_handlers.request_job_handler import RequestJobHandler
from lambda_handlers.start_job_handler import StartJobHandler


class TestBibleBundle(TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
    temp_dir = None

    # noinspection PyUnusedLocal
    @staticmethod
    def mock_s3_upload_file(source, key, cache_time=600):
        print('Mock uploading {}'.format(source), end=' ')
        target = os.path.join(TestBibleBundle.temp_dir, key)
        make_dir(os.path.dirname(target))
        shutil.copyfile(source, target)
        print('finished.')

    def setUp(self):
        TestBibleBundle.temp_dir = tempfile.mkdtemp(prefix='integrationTest_')

    def tearDown(self):
        if os.path.isdir(TestBibleBundle.temp_dir):
            shutil.rmtree(TestBibleBundle.temp_dir, ignore_errors=True)

    @patch('client.client_webhook.S3Handler.upload_file')
    def testPipeline(self, mock_s3_upload):

        mock_s3_upload.side_effect = self.mock_s3_upload_file

        # create test event variable
        event = {'vars': load_json_object(os.path.join(self.resources_dir, 'event_vars.json')),
                 'data': load_json_object(os.path.join(self.resources_dir, 'bible_bundle_payload.json'))}

        # create test context variable
        context = JsonObject({'aws_request_id': str(uuid.uuid4())[-10:]})

        ClientWebhookHandler().handle(event, context)

        RequestJobHandler().handle(event, context)

        StartJobHandler().handle(event, context)
