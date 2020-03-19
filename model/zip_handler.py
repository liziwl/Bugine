from shutil import unpack_archive
import os
import fnmatch
from model import core_util,work_path
import logging


def extract(compressed_file, path_to_extract=work_path.get_tmp()):
    logger = logging.getLogger("StreamLogger")
    logger.info(f"extract {compressed_file} to {path_to_extract}")
    base_name = os.path.splitext(os.path.basename(compressed_file))[0]
    ex_dir = os.path.join(path_to_extract, base_name)
    os.makedirs(ex_dir, exist_ok=True)
    unpack_archive(compressed_file, ex_dir)
    return os.path.abspath(ex_dir)


def unpack_dir(dir_path):
    logger = logging.getLogger("StreamLogger")
    logger.info(f"extract all compressed file in {dir_path}")
    exten = set(['zip'])
    ext_files = os.listdir(dir_path)
    tmp = []
    for ext in exten:
        real_files = fnmatch.filter(ext_files, '*.' + ext)
        if len(real_files) > 0:
            tmp_paths = [os.path.join(os.path.abspath(dir_path), f) for f in real_files]
            tmp.extend(tmp_paths)
    ext_files = tmp

    for e in ext_files:
        path = extract(e)
        # print(path)

if __name__ == '__main__':
    unpack_dir('../uploads')
