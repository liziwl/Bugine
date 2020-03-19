import fnmatch
import os
import xml.etree.ElementTree as ET
from collections import deque
from model import util
from model import core_util, work_path
import logging

# RES_DIR_KEY = 'src\\main\\res'
RES_DIR_KEY = os.path.join(*'src\\main\\res\\layout'.split("\\"))


def find_loc_res(walk_dir):
    logger = logging.getLogger("StreamLogger")
    logger.info(f"Find path end with {RES_DIR_KEY}")
    loc_res_dir = str()
    for r, d, files in os.walk(walk_dir):
        path = os.path.abspath(r)
        if os.path.isdir(path) and path.endswith(RES_DIR_KEY):
            loc_res_dir = path
            break
    tmp = loc_res_dir if loc_res_dir != "" else "NOTHING"
    logger.info(f"Found {tmp}")
    return loc_res_dir


def get_res_xml(loc_res_dir):
    logger = logging.getLogger("StreamLogger")
    xml_list = list()
    for r, d, files in os.walk(loc_res_dir):
        xml_files = fnmatch.filter(files, '*.xml')
        if len(xml_files) > 0:
            tmp_paths = [os.path.join(os.path.abspath(r), f) for f in xml_files]
            xml_list.extend(tmp_paths)
    logger.info(f"Found {len(xml_list)} xml files in {loc_res_dir}")
    return xml_list


def bfs_xml(xml_path_list, csv_path):
    """
    生成csv描述文件
    """
    data = []
    for xml_path in xml_path_list:
        tree = ET.parse(xml_path)
        queue = deque()
        queue.append(tree.getroot())
        file_name = util.drop_file_ext(xml_path)
        while len(queue) > 0:
            top = queue.popleft()
            for child in top:
                queue.append(child)
            for atr in top.attrib:
                if atr.endswith("id"):
                    # print(top.tag, atr, top.attrib[atr])
                    data.append((file_name, top.tag, top.attrib[atr].split("/")[-1]))
    util.dump_csv(csv_path, data)


def get_descript(repo_path, ext_path=work_path.get_tmp()):
    logger = logging.getLogger("StreamLogger")
    logger.info(f'Search descript in {repo_path}')
    loc_res_dir = find_loc_res(repo_path)
    xml_list = get_res_xml(loc_res_dir)
    save_file_path = os.path.join(ext_path, util.drop_file_ext(repo_path) + ".csv")
    bfs_xml(xml_list, save_file_path)
    return save_file_path


if __name__ == '__main__':
    logger = logging.getLogger("StreamLogger")

    path = work_path.get_tmp()
    file_list = os.listdir(path)

    repo_list = list()
    for file in file_list:
        tmp_path = os.path.join(os.path.abspath(path), file)
        repo_list.append(tmp_path)

    # logger.debug(repo_list)

    for repo in repo_list:
        logger.debug(repo)
        # loc_res_dir = find_loc_res(repo)
        # xml_list = get_res_xml(loc_res_dir)
        # bfs_xml(xml_list, os.path.join(work_path.get_tmp(), util.drop_file_ext(repo) + ".csv"))
        path = get_descript(repo)
