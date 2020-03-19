from os.path import join, dirname, abspath, relpath

_project_root = abspath(join(dirname(__file__), ".."))
UPLOAD_FOLDER = './uploads'
EXTRACT_TMP = './tmp/'


def in_project(relative_path_to_project_root):
    return abspath(join(_project_root, relative_path_to_project_root))


def get_upload():
    return in_project(UPLOAD_FOLDER)


def get_tmp():
    return in_project(EXTRACT_TMP)


def rela_path(path_a, path_b):
    return relpath(path_a, path_b)


if __name__ == '__main__':
    print(_project_root)
    print(in_project('model'))
