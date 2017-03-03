from __future__ import unicode_literals, print_function
import os
import shutil
import tempfile
import uuid
from unittest import TestCase

from gogs_client.entities import GogsUser
from mock import patch

from general_tools.file_utils import load_json_object, make_dir, read_file, unzip
from integration_tests.helpers import JsonObject, dict_to_dynamodb_record

from lambda_handlers.client_webhook_handler import ClientWebhookHandler
from lambda_handlers.request_job_handler import RequestJobHandler
from lambda_handlers.start_job_handler import StartJobHandler


class TestBibleBundle(TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources')
    temp_dir = None

    @staticmethod
    def mock_download_repo(source, target_dir):
        print('Mock downloading {}'.format(source))
        print('Unzipping to {}...'.format(target_dir), end=' ')
        if 'ulb' in source:
            unzip(os.path.join(TestBibleBundle.resources_dir, 'bible_bundle_master.zip'), target_dir)
        print('finished.')

    # noinspection PyUnusedLocal
    @staticmethod
    def mock_s3_upload_file(source, key, cache_time=600):
        print('Mock uploading {}'.format(source), end=' ')
        target = os.path.join(TestBibleBundle.temp_dir, key)
        make_dir(os.path.dirname(target))
        shutil.copyfile(source, target)
        print('finished.')

    # noinspection PyUnusedLocal
    @staticmethod
    def mock_requests_post(url, json=None, headers=None):
        print('Mock posting {}'.format(url))

        if url == 'unit_test_api_url/tx/job':

            handler = RequestJobHandler()

            context = JsonObject({'aws_request_id': 'BR-549'})
            event = {
                'data': json,
                'vars': load_json_object(os.path.join(TestBibleBundle.resources_dir, 'request_job_event_vars.json'))
            }

            handler.handle(event, context)

            response = {
                'status_code': 200,
                'text': read_file(os.path.join(TestBibleBundle.resources_dir, 'bible_job_resp.json'))
            }
            return JsonObject(response)

    @staticmethod
    def mock_s3_get_objects(prefix=None, suffix=None):
        print('Mock get objects: {}, {}'.format(prefix, suffix))

        if prefix == 'u/Door43-Catalog/ne-ulb/ed87f2c2fc':
            return []

    @staticmethod
    def mock_get_gogs_user(user_token=None):
        print('Mock get gogs user {}'.format(user_token))

        return GogsUser(1, 'unit_test', 'Unit Test', 'unit_test@unit_test.com', '')

    @staticmethod
    def mock_db_insert_item(job_data):
        event = {'Records': [dict_to_dynamodb_record('INSERT', job_data)]}
        context = None
        StartJobHandler().handle(event, context)

    @staticmethod
    def mock_db_get_item(query_data):
        pass

    def setUp(self):
        TestBibleBundle.temp_dir = tempfile.mkdtemp(prefix='integrationTest_')

    def tearDown(self):
        if os.path.isdir(TestBibleBundle.temp_dir):
            shutil.rmtree(TestBibleBundle.temp_dir, ignore_errors=True)

    # DynamoDBHandler
    @patch('manager.manager.DynamoDBHandler.get_item')
    @patch('manager.manager.DynamoDBHandler.insert_item')
    @patch('manager.manager.TxManager.get_user')
    @patch('requests.post')
    @patch('client.client_webhook.ClientWebhook.download_repo')
    @patch('client.client_webhook.S3Handler.get_objects')
    @patch('client.client_webhook.S3Handler.upload_file')
    def testPipeline(self, mock_s3_upload, mock_s3_get_objects, mock_download_repo, mock_post, mock_get_user,
                     mock_insert_item, mock_get_item):

        mock_s3_upload.side_effect = self.mock_s3_upload_file
        mock_s3_get_objects.side_effect = self.mock_s3_get_objects
        mock_download_repo.side_effect = self.mock_download_repo
        mock_post.side_effect = self.mock_requests_post
        mock_get_user.side_effect = self.mock_get_gogs_user
        mock_insert_item.side_effect = self.mock_db_insert_item
        mock_get_item.side_effect = self.mock_db_get_item

        # create test event variable
        event = {'vars': load_json_object(os.path.join(self.resources_dir, 'client_webhook_event_vars.json')),
                 'data': load_json_object(os.path.join(self.resources_dir, 'bible_bundle_payload.json'))}

        # create test context variable
        context = JsonObject({'aws_request_id': str(uuid.uuid4())[-10:]})

        ClientWebhookHandler().handle(event, context)
