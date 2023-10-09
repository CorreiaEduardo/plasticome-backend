import os

import docker

from plasticome.config.celery_config import celery_app


@celery_app.task
def run_dbcan_container(absolute_mount_dir):
    """
    The function `run_dbcan_container` runs a Docker container with the dbcan
    image and parameters to analyze genome proteins, and returns the output folder path and an error message
    if any.

    :param absolute_mount_dir: The absolute path of the directory where the input
    file is located
    :return: The function `run_dbcan_container` returns a tuple containing the
    `output_folder` and a boolean value indicating whether the execution was
    successful. If the execution is successful, the boolean value is `False`. If
    there is an error, the boolean value is `True` and the error message is
    returned as a string.
    """

    input_file = os.path.basename(absolute_mount_dir)
    local_mount_dir = os.path.dirname(absolute_mount_dir)
    docker_mount = os.path.basename(local_mount_dir)

    output_folder_name = f'{input_file.split(".")[0]}_results'
    output_folder = os.path.join(local_mount_dir, output_folder_name)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    client = docker.from_env()

    container_params = {
        'image': 'haidyi/run_dbcan:latest',
        'volumes': {
            local_mount_dir: {'bind': f'/app/{docker_mount}', 'mode': 'rw'}
        },
        'working_dir': '/app',
        'command': [
            f'./{docker_mount}/{input_file}',
            'protein',
            '--out_dir',
            f'./{docker_mount}/{output_folder_name}',
        ],
        'remove': True,
    }
    try:
        client.containers.run(**container_params)
        return output_folder, False
    except Exception as e:
        return False, f'[DBCAN STEP] - Unexpected error: {e}'
