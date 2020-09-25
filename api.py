from model import zip_handler, xml_parser, work_path, match_name, util, nlp_util, search_rank
from model import table2tsv
from model import issuedb
from model import url_repo
from model.util import print_run_time
import os
import logging
from billiard import Pool
import uuid
import redis
import ast

pp = util.PrintWarp()
r = redis.StrictRedis(host='127.0.0.1', password='mypass', port=6379, db=1, decode_responses=True)


# api使用顺序
# 1. zip2descript 解压源代码，提取描述文件
# 2. descript 生成描述文件，得到src app与 数据库每个app的总相似度，按照相似度降序排列. 用作 搜索 app 源列表选择的输入
# 3. query_issue 根据 已经排序过的app相似度降序列表 scan_output 搜索所有可能 issue，生成查询结果
# 4. sort_result_table 对结果进行排序
# 5. get_out 格式化输出， example line: key, recommend_url

def _single_scan_helper(arg):
    index, file_path, sample_ui_list, comp_func, weight_list, threshold = arg
    logger = logging.getLogger("StreamLogger")
    logger.debug(file_path)
    tmp_out = util.read_csv(file_path)
    tmp_out = nlp_util.process_xsv(tmp_out)

    if len(tmp_out) == 0:
        logger.debug(f"EMPTY {file_path}")
        score_distribution_list = []
    else:
        score_distribution_list = match_name.weight_compare_list(sample_ui_list, tmp_out, comp_func,
                                                                 weight_list)
    # score_distribution_list = util.get_col(score_distribution_list, 2)
    score = match_name.similar_index(score_distribution_list, threshold, col_index=2, rate=True)

    rt = (file_path, score, score_distribution_list)
    logger.debug(f"ADD {index} {file_path}")
    return rt


def _scan_match(sample_ui_list, path_list, comp_func, weight_list=None, threshold=0.6, pool_size=12):
    """
    :param sample_ui_list: output after process_csv()
    :param path_list: relative or absolute path list of csv files
    :param comp_func: compare function
    :param weight_list: ui weight mask
    :param threshold: threshold，超过一定的阈值才会被计算成相同组件
    :param pool_size: 并行池大小
    :return: best match path name
    """
    pool = Pool(processes=pool_size)

    arg_list = []
    for j in range(len(path_list)):
        arg_list.append((j + 1, path_list[j], sample_ui_list, comp_func, weight_list, threshold))
    score_list = pool.map(_single_scan_helper, arg_list)
    pool.close()
    pool.join()

    # return sorted path^score^score_distribution_list list
    return sorted(score_list, key=lambda k: k[1], reverse=True)


@print_run_time
def zip2descript(file_path, output_folder):
    """解压接口
    :param file_path: zip文件路径
    :param output_folder: 输出文件夹
    :return 解压输出目录
    """
    ext_path = zip_handler.extract(file_path)
    dep_path = xml_parser.get_descript(ext_path, output_folder)
    return dep_path


def except_list_build_helper():
    src_dir = work_path.in_project('./model/data/description')
    file_list = os.listdir(src_dir)
    file_list = [util.bare_name(f) for f in file_list]
    rt = []
    for i in range(len(file_list)):
        tmp = {}
        tmp['id'] = f'cf_{i + 1}'
        tmp['text'] = " ".join(file_list[i].split('_'))
        tmp['val'] = file_list[i]
        rt.append(tmp)
    return rt


@print_run_time
def descript(query_decp, except_files=None, pool_size=12):
    """
    生成描述文件
    ~1分钟得出结果
    :param query_decp: 描述文件矩阵
    example line: xml_file_name, class_name, element_name
    :param except_files: 排除文件关键词，接受字符串或字符串数组
    :param pool_size: 并行池大小
    :return: a tuple. 得到src app与 数据库每个app的总相似度，按照相似度降序排列. 用作 搜索 app
    """
    query_decp = nlp_util.process_xsv(query_decp)
    src_dir = work_path.in_project('./model/data/description')
    logger = logging.getLogger("StreamLogger")
    file_list = os.listdir(src_dir)
    file_list = [os.path.join(src_dir, f) for f in file_list]

    if except_files is not None:
        tmp = []
        rms = []
        if type(except_files) == str:
            for i in file_list:
                if except_files not in i:
                    tmp.append(i)
                else:
                    rms.append(i)
        elif type(except_files) == list or type(except_files) == set:
            except_files = set(except_files)
            for i in file_list:
                flag = False
                for j in except_files:
                    if j in i:
                        flag = True
                        break
                if not flag:
                    tmp.append(i)
                else:
                    rms.append(i)
        logger.debug(pp.pformat(rms))
    file_list = tmp
    logger.debug(pp.pformat(file_list))

    scan_output = _scan_match(query_decp, file_list, match_name.ngram_compare, [1, 0.5, 0.5], threshold=0.7,
                              pool_size=pool_size)
    # 得到src app与 数据库每个app的总相似度，按照相似度降序排列。
    # tuple(
    # str "参考APP描述文件名",
    # float "APP相似度",
    # list "参考APP的组件相似度" [(请求app组件, 参考app组件，组件相似度)]
    # )
    logger.debug(pp.pformat(util.get_col(scan_output, [0, 1])))
    return scan_output


def _restore_mask(name):
    """连接符分隔开，重新变成数组"""
    tmp = list(filter(lambda item: item != "#", name.split("=")))
    for i in range(len(tmp)):
        tmp[i] = tmp[i].split("^")
    return tmp


def _filter_search_keys(weight_list, threshold=0.6, unique=True):
    """
    :param weight_list: output of weight_compare_list
    :param threshold: threshold
    :param unique: unique the keys
    :return: 3 dim list of target ui components
    """
    keys = []
    for res in weight_list:
        src, target, score = res
        if score < threshold:
            continue
        src, target = map(_restore_mask, [src, target])
        keys.append(target)
    if unique:
        unique_keys = util.StringHash(keys)
        return unique_keys.get_in_list()
    else:
        return keys


def _pre_calc(**kwargs):
    """
    提前计算部分数值加快查找
    :param kwargs: must need title_list, body_list, keys_sea
    :return: pre_calc dict
    """
    title_list = kwargs["title_list"]
    body_list = kwargs["body_list"]
    keys_sea = kwargs["keys_sea"]
    label_list = kwargs["label_list"]
    reply_list = kwargs["reply_list"]
    hot_k = nlp_util.get_hot_keys()
    c_label = nlp_util.get_concern_label()

    ess_keys = set()
    for r in keys_sea:
        for a_list in r:
            ess_keys = ess_keys.union(a_list)
    ess_keys = " ".join(list(ess_keys))
    ess_keys = nlp_util.stem_sentence(ess_keys)
    ess_keys = set(ess_keys)

    body_len = [nlp_util.word_count(b) for b in body_list]
    title_list, body_list = map(nlp_util.stem_corpus, [title_list, body_list])
    label_list = nlp_util.split_label(label_list)
    label_list = nlp_util.stem_corpus(label_list)

    hit_count_title = search_rank.get_key_sea_count_corpus(ess_keys, title_list, unique=True)
    hit_count_body = search_rank.get_key_sea_count_corpus(ess_keys, body_list, unique=True)
    hit_count_hot = search_rank.get_key_sea_count_corpus(hot_k, body_list, unique=False)
    hit_count_label = search_rank.get_key_sea_count_corpus(c_label, label_list, unique=False)

    return {
        "hit_count_title": hit_count_title,
        "hit_count_body": hit_count_body,
        "hit_count_hot": hit_count_hot,
        "hit_count_label": hit_count_label,
        "body_len": body_len,
        "stat": {
            "max-reply": max(reply_list),
            "max-body_len": max(body_len),
        },
    }


@print_run_time
def query_issue(scan_output, max_depth=4):
    """
    根据 已经排序过的app相似度降序列表 scan_output 搜索所有可能 issue
    ~1分钟得出结果
    :param scan_output: 格式参考 descript（）函数的输出
    :param max_depth: 限制搜索深度，取最相似的前几个
    :return: 所有查询
    """
    # TODO 查询的 key 哪里出来的？
    logger = logging.getLogger("StreamLogger")
    rdb = issuedb.ISSuedb()
    sql = """select issue_num, comments, state, title, body, commit_id, labels from {}
                    order by length(body) desc"""
    overall_table = {}
    # 所有相关app和item
    for i in range(min(len(scan_output), max_depth)):
        one_dict = {}
        app = scan_output[i][0]
        one_dict['sim'] = scan_output[i][1]

        tab_name = table2tsv.file2table(app)
        one_dict['data'] = []
        one_dict['keys'] = []

        score_list = scan_output[i][2]
        keys_sea = _filter_search_keys(score_list, threshold=0.7)
        logger.debug(f"{app}\t{tab_name}\tsimilar keys length: {len(keys_sea)}")

        output = rdb.db_retrieve(sql.format(tab_name))
        head = ["issue_num", "comments", "state", "title", "body", "commit_id", "labels"]
        f_output = issuedb.retrieve_formatter(head, output)

        title_list = util.get_col(output, head.index('title'))
        body_list = util.get_col(output, head.index('body'))
        label_list = util.get_col(output, head.index('labels'))
        reply_list = util.get_col(output, head.index('issue_num'))
        pre_calc_val = _pre_calc(title_list=title_list,
                                 body_list=body_list,
                                 label_list=label_list,
                                 reply_list=reply_list,
                                 keys_sea=keys_sea)

        for k in keys_sea:
            keys = []
            for i in k:
                keys.append(" ".join(i))
            keys = " ".join(keys)
            ess_keys = nlp_util.stem_sentence(keys)

            tmp = search_rank.sort_candidate_seq(f_output, ess_keys, pre_calc_val)
            leng = min(3, len(tmp))
            one_dict['keys'].extend([ess_keys] * leng)
            one_dict['data'].extend(tmp[:leng])
        overall_table[tab_name] = one_dict
        logger.debug(pp.pformat(overall_table))
        logger.debug("#" * 50)
    return overall_table


@print_run_time
def sort_result_table(overall_table):
    """对结果进行排序
    ~1秒得出结果
    :param overall_table: sort_result_table（）的返回
    :return: 返回排序后的issue，example line：项目名，issue id，排序分数
    """
    logger = logging.getLogger("StreamLogger")
    over_sort = []
    for app_name in overall_table:
        app_sim_weight = search_rank.CONF_JSON['app_sim_w']
        app_sim = overall_table[app_name]['sim']
        data = overall_table[app_name]['data']
        for j in range(len(data)):
            j_score = data[j][1]['total']
            # j_score 可以重新计算 item的相似度加权重
            one_detail = data[j][1]
            logger.debug(one_detail)
            # 为调试
            app_com_score = app_sim_weight * app_sim + j_score
            logger.debug(f"app_sim: {app_sim}")
            # 这里需要对 j_score 做 normalize
            over_sort.append((app_name, j, app_com_score))

    over_sort.sort(key=lambda row: row[-1], reverse=True)
    return over_sort


@print_run_time
def get_out(over_sort, overall_table):
    """
    格式化输出， example line: key, recommend_url
    ~1秒得出结果
    :param over_sort: sort_result_table（）的返回
    :param overall_table: query_issue（）的返回
    :return: 格式化数据
    """
    logger = logging.getLogger("StreamLogger")
    logger.debug("@" * 50)
    cout = 0
    uni_set = set()
    tsv_data = []
    for i in range(len(over_sort)):
        if cout >= 100:
            break
        app_name, index, app_com_score = over_sort[i]
        iss_id = overall_table[app_name]['data'][index][0][0]
        if iss_id in uni_set:
            continue
        cout += 1
        uni_set.add(iss_id)
        f_key = "^".join(overall_table[app_name]['keys'][index])
        logger.debug((cout, app_name, app_com_score, f_key))
        logger.debug(pp.pformat(overall_table[app_name]['data'][index]))
        url = url_repo.tb_name2url(app_name) + "/issues/" + str(overall_table[app_name]['data'][index][0].issue_num)
        tsv_data.append((f_key, url))
    return tsv_data


def uuid_valid(uuid_str):
    try:
        uuid.UUID(hex=uuid_str)
        return True
    except ValueError as e:
        return False


def csv_uuid_exist(uuid_str, check_dir):
    files = os.listdir(check_dir)
    for f in files:
        if util.just_uuid(f) == uuid_str:
            return os.path.join(check_dir, f)
    return None


def format_ban_files(a_dict):
    rt = []
    for k in a_dict.keys():
        if k.startswith("cf_"):
            rt.append(a_dict[k])
    return rt


def save_job_meta(key, val):
    if not isinstance(val, str):
        val = val.__repr__()
    r.set(key, val)


def get_job_meta(key):
    return ast.literal_eval(r.get(key))


def valid_key(key):
    return r.exists(key)


if __name__ == '__main__':
    pass
    # test = util.read_csv("model/data/description/owncloud_android_master.csv")
    # scan_output = descript(test, except_files="owncloud_android", pool_size=12)
    # overall_table = query_issue(scan_output, max_depth=3)
    # overall_sort = sort_result_table(overall_table)
    # out = get_out(overall_sort, overall_table)
