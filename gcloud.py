import os
from google.cloud import storage
from naimai.constants.paths import path_produced


class gcloud_data:
    def __init__(self, bucket_name="naima_bucket2", path_service_key_gcloud='service_key_gcloud.json',
                 prefix='data_fields/'):
        self.bucket_name = bucket_name
        self.storage_client = None
        self.bucket = None
        self.prefix = prefix

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = path_service_key_gcloud
        try:
            self.get_client()
            self.get_bucket()
        except:
            print('No storage client found! Give the correct path of service key gcloud file.')

    def get_client(self):
        self.storage_client = storage.Client()

    def get_bucket(self):
        if self.storage_client:
            self.bucket = self.storage_client.get_bucket(self.bucket_name)
        else:
            print('Need storage client!')

    def upload(self, path_from, path_to):
        blob = self.bucket.blob(path_to)
        blob.upload_from_filename(path_from)

    def upload_search_model(self, field: str, path_drive: str):
        '''
        upload search model folder from drive to bucket
        '''
        path_drive2 = os.path.join(path_drive, 'search_model')
        path_gcloud = os.path.join(self.prefix, field, 'search_model')

        files = os.listdir(path_drive2)
        path_drive_pooling = ''
        # upload files
        for f in files:
            path = os.path.join(path_drive2, f)
            if os.path.isfile(path):
                path_file_gcloud = os.path.join(path_gcloud,f)
                self.upload(path, path_file_gcloud)
            elif os.path.isdir(path):
                path_drive_pooling = os.path.join(path, 'config.json')

        # upload pooling folder
        path_gcloud_pooling = os.path.join(path_gcloud, '1_Pooling', 'config.json')
        self.upload(path_drive_pooling, path_gcloud_pooling)

    def upload_papers(self, field: str, path_drive: str):
        '''
        upload papers sqlite data from drive to bucket
        '''
        path_drive2 = os.path.join(path_drive, 'all_papers_sqlite')
        path_gcloud = os.path.join(self.prefix, field, 'all_papers_sqlite')
        self.upload(path_drive2, path_gcloud)

    def upload_index(self, field: str, path_drive: str):
        '''
        upload field index from drive to bucket
        '''
        path_drive2 = os.path.join(path_drive, 'encodings.index')
        path_gcloud = os.path.join(self.prefix, field, 'encodings.index')
        self.upload(path_drive2, path_gcloud)

    def upload_field(self, field: str):
        '''
        upload field from drive to bucket
        '''
        path_drive_field = os.path.join(path_produced, field)
        print('>> Uploading papers..')
        self.upload_papers(field, path_drive_field)
        print('>> Uploading index..')
        self.upload_index(field, path_drive_field)
        print('>> Uploading search model..')
        self.upload_search_model(field, path_drive_field)
        print('>> Done !')

    def get_index(self, field: str):
        '''
        get index from gcloud
        :param field:
        :return:
        '''
        path_index = os.path.join(self.prefix, field, 'encodings.index') # same path in gcloud and locally
        blobs = self.bucket.list_blobs(prefix=path_index)

        if not os.path.exists(path_index): #if already downloaded locally..
            for blob in blobs:
                blob.download_to_filename(path_index)

    def get_papers(self, field: str):
        '''
        get papers sqlite from gcloud
        :param field:
        :return:
        '''
        path_papers = os.path.join(self.prefix, field, 'all_papers_sqlite') # same path in gcloud and locally
        blobs = self.bucket.list_blobs(prefix=path_papers)

        if not os.path.exists(path_papers): #if already downloaded locally..
            for blob in blobs:
                blob.download_to_filename(path_papers)

    def get_search_model(self, field: str):
        '''
        get search model from gcloud
        :param field:
        :return:
        '''
        path_smodel = os.path.join(self.prefix, field, 'search_model') # same path in gcloud and locally
        blobs = self.bucket.list_blobs(prefix=path_smodel)

        if not os.path.exists(path_smodel): #if already downloaded locally..
            for blob in blobs:
                blob.download_to_filename(path_smodel)
