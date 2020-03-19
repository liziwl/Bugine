from model import issuedb as idb
import os
from model import util, work_path

__GENERATE__ = False
if __GENERATE__:
    SRC_DIR = 'tsv/'
    TEST_DIR = 'tsv_test/'

TSV_FILE = work_path.in_project('./model/conf/tab_url.tsv')
__data_tsv = util.read_tsv(TSV_FILE)


def generate_lookup_table():
    db_driver = idb.ISSuedb()
    output = db_driver.db_retrieve("select name from sqlite_master where type='table' order by name;")
    table_dict = {i[0].replace("$", "_"): i[0] for i in output}

    file_list = os.listdir(SRC_DIR)
    file_list = [os.path.join(SRC_DIR, f) for f in file_list]

    file_list_test = os.listdir(TEST_DIR)
    file_list_test = [os.path.join(TEST_DIR, f) for f in file_list_test]

    files = file_list + file_list_test
    files_dict = {i: False for i in files}

    reload = util.Reload(TSV_FILE)

    for item in table_dict:
        flag = False
        for f in files:
            if item in f:
                flag = True
                print("{}\t{}".format(table_dict[item], f))
                files_dict[f] = True
                break
        if not flag:
            print("{}\tNULL".format(table_dict[item]))

    for f in files_dict:
        if not files_dict[f]:
            print("NULL\t{}".format(f))

    db_driver.db_close()


def table2file(table_name):
    for i in range(len(__data_tsv)):
        if table_name == __data_tsv[i][0]:
            return __data_tsv[i][1]


def file2table(file_name):
    for i in range(len(__data_tsv)):
        if os.path.basename(file_name) == os.path.basename(__data_tsv[i][1]):
            return __data_tsv[i][0]


if __name__ == '__main__':
    # generate_lookup_table()
    print(table2file("duckduckgo$Android"))
    print(file2table("farmerbb_Notepad_master.tsv"))
