import os

import docker

from plasticome.config.celery_config import celery_app


@celery_app.task
def run_ecpred_container(absolute_mount_dir):
    """
    The function `run_ecpred_container` runs a Docker container with the image
    `blueevee/ecpred:latest` and mounts a directory to the container, then executes
    a command within the container and returns the path to the output file with the
    ec numbers predicted to the enzymes.

    :param absolute_mount_dir: The absolute path of the directory where the input
    file is located
    :return: The function `run_ecpred_container` returns a tuple containing two
    values. The first value is `output_file_path`, which is the path to the output
    file generated by the container. The second value is a boolean `False` if the
    container runs successfully, or a string containing an error message if an
    exception occurs during the container execution.
    """

    input_file = os.path.basename(absolute_mount_dir)
    local_mount_dir = os.path.dirname(absolute_mount_dir)
    docker_mount = os.path.basename(local_mount_dir)

    client = docker.from_env()

    container_params = {
        'image': 'blueevee/ecpred:latest',
        'volumes': {
            local_mount_dir: {'bind': f'/app/{docker_mount}', 'mode': 'rw'}
        },
        'working_dir': '/app',
        'command': [
            'spmap',
            f'./{docker_mount}/{input_file}',
            './',
            '/temp',
            f'./{docker_mount}/ec_pred_results.tsv',
        ],
        'remove': True,
    }
    try:
        client.containers.run(**container_params)
        return local_mount_dir, False
    except Exception as e:
        return False, f'[ECPRED STEP] - Unexpected error: {str(e)}'
