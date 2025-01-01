import ufiles
import os

ufiles_client = ufiles.UFiles(
    ufiles_base_url="https://media.pixiee.io/v1/f",
    usso_base_url="https://sso.pixiee.io",
    api_key=os.getenv("PTOKEN"),
)


def upload_file(file_path, file_name):
    uploaded_file = ufiles_client.upload_file(file_path, filename=file_name)

    return uploaded_file.url
