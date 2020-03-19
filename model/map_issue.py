import os
import random
import issuedb
import match_name
import util
import nlp_util
import search_rank
import table2tsv
import url_repo
import eval_test
import logging

pp = util.PrintWarp()

SRC_DIR = "tsv/"
TEST_DIR = "tsv_test/"


def select_item(a_list):
    print("-" * 50)
    length = len(a_list)
    for i in range(length):
        print("{}\t{}".format(i + 1, a_list[i]))
    while True:
        try:
            sele = int(input("Select number:"))
            print(sele)
            if sele not in range(1, length + 1):
                raise Exception("Not in range.")
            else:
                break
        except Exception as e:
            pass
    return sele - 1


def select_dir(path):
    filelist = os.listdir(path)
    filelist.sort(key=lambda x: x.lower())
    i = select_item(filelist)
    rt_path = os.path.join(path, filelist[i])
    return rt_path


def scan_match(sample_ui_list, path_list, comp_func, weight_list=None, threshold=0.6):
    """
    :param sample_ui_list: output after process_tsv()
    :param path_list: relative or absolute path list of tsv files
    :param comp_func: compare function
    :param weight_list: ui weight mask
    :param threshold: threshold，超过一定的阈值才会被计算成相同组件
    :return: best match path name
    """
    logger = logging.getLogger("StreamLogger")
    out_dict = dict()
    for path in path_list:
        logger.debug(path)
        tmp_out = util.read_tsv(path)
        tmp_out = nlp_util.process_tsv(tmp_out)
        out_dict[os.path.basename(path)] = tmp_out

    count = 0
    score_list = []
    for j in range(len(path_list)):
        count += 1
        j_file = os.path.basename(path_list[j])
        name = path_list[j]
        if len(out_dict[j_file]) == 0:
            logger.debug(f"EMPTY {name}")
            score_distribution_list = []
            continue
        else:
            score_distribution_list = match_name.weight_compare_list(sample_ui_list, out_dict[j_file], comp_func,
                                                                     weight_list)
        # score_distribution_list = util.get_col(score_distribution_list, 2)
        score = match_name.similar_index(score_distribution_list, threshold, col_index=2, rate=True)

        score_list.append((name, score, score_distribution_list))
        logger.debug(f"ADD {count} {name}")
    # return sorted path^score^score_distribution_list list
    return sorted(score_list, key=lambda k: k[1], reverse=True)


def restore_mask(name):
    """连接符分隔开，重新变成数组"""
    tmp = list(filter(lambda item: item != "#", name.split("=")))
    for i in range(len(tmp)):
        tmp[i] = tmp[i].split("^")
    return tmp


def filter_search_keys(weight_list, threshold=0.6, unique=True):
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
        src, target = map(restore_mask, [src, target])
        keys.append(target)
    if unique:
        unique_keys = util.StringHash(keys)
        return unique_keys.get_in_list()
    else:
        return keys


# def print_corpus(text, top=3):
#     for i in range(top):
#         pp.pprint(text[i][0][:4])
#         pp.pprint(text[i][1])


# def print_result(text, top, just_head=False, unique=True):
#     if not unique:
#         for i in range(top):
#             if not just_head:
#                 print(text[i][0])

#             pp.pprint(text[i][1][0][:4])

#             if not just_head:
#                 pp.pprint(text[i][1][1])
#     else:
#         uni = set()
#         for i in range(top):
#             inum = text[i][1][0][0]
#             if inum not in uni:
#                 uni.add(inum)
#                 if not just_head:
#                     print(text[i][0])

#                 pp.pprint(text[i][1][0][:4])

#                 if not just_head:
#                     pp.pprint(text[i][1][1])
#             else:
#                 print("Duplicated", inum)


def pre_calc(**kwargs):
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


def get_issue_set(data):
    """获取独一的 issue id 集合"""
    issue_set = set()
    for d in data:
        issue_set.add(d[1][0][0])
    return issue_set


def format_result(ess_keys, result, top):
    """临时tsv导出，格式化"""
    out = []
    for i in range(top):
        tmp = []
        tmp.append("^".join(ess_keys))  # keys
        tmp.append(i + 1)  # rank
        tmp.append(result[i][0][0])  # issue id
        tmp.append(result[i][0][3])  # issue name
        tmp.append(result[i][1]['total'])
        tmp.append(result[i][1]['body_len']['val'])
        tmp.append(result[i][1]['closed']['val'])
        tmp.append(result[i][1]['commit_id']['val'])
        tmp.append(result[i][1]['hit_body_all']['val'])
        tmp.append(result[i][1]['hit_body_num']['val'])
        tmp.append(result[i][1]['hit_hot_words']['val'])
        tmp.append(result[i][1]['hit_label']['val'])
        tmp.append(result[i][1]['hit_title_all']['val'])
        tmp.append(result[i][1]['hit_title_overlap']['val'])
        tmp.append(result[i][1]['reply_num']['val'])
        out.append(tmp)
    return out


# def old_main():
#     reload = util.Reload()

#     # src_path = select_dir(SRC_DIR)
#     # test_path = select_dir(TEST_DIR)
#     #
#     # print(src_path, test_path)
#     # src_out, test_out = map(util.read_tsv, [src_path, test_path])
#     # src_out, test_out = map(nlp_util.process_tsv, [src_out, test_out])

#     # list_score = match_name.weight_compare_list(src_out, test_out, match_name.ngram_compare, [0, 0.5, 1])
#     # list_score.sort(key=lambda k: k[2], reverse=True)
#     # pp.pprint(list_score)

#     # test code
#     src = "tsv/nextcloud_android_master.tsv"
#     # src = 'tsv/kshksh_FastHub_development.tsv'
#     # src = 'tsv/SimpleMobileTools_Simple_Gallery_master.tsv'
#     src_out = util.read_tsv(src)
#     src_out = nlp_util.process_tsv(src_out)

#     file_list = os.listdir(SRC_DIR)
#     file_list = [os.path.join(SRC_DIR, f) for f in file_list]
#     file_list.remove(src)
#     pp.pprint(
#         util.get_col(scan_match(src_out, file_list, match_name.ngram_compare, [0.5, 0.5, 1], threshold=0.7), [0, 1]))

#     test_f = "tsv/owncloud_android_master.tsv"
#     # test_f = "tsv/slapperwan_gha_master.tsv"
#     # test_f = "tsv/SimpleMobileTools_Simple_File_Manager_master.tsv"
#     best_out = util.read_tsv(test_f)
#     best_out = nlp_util.process_tsv(best_out)
#     score_list = match_name.weight_compare_list(src_out, best_out, match_name.ngram_compare, [0.5, 0.5, 1])
#     keys_sea = filter_search_keys(score_list, threshold=0.7)
#     # pp.pprint(keys_sea)
#     print("Similar keys length:", len(keys_sea))

#     rdb = issuedb.ISSuedb()
#     sql = """select issue_num, comments, state, title, body, commit_id, labels from {}
#                 order by length(body) desc"""
#     # remove constrain "where labels like '%bug%' or commit_id is not null"

#     tb_name = "owncloud$android"
#     tb_name = "slapperwan$gha"
#     tb_name = "SimpleMobileTools$Simple_File_Manager"
#     output = rdb.db_retrieve(sql.format(tb_name))

#     title_list = util.get_col(output, 3)
#     body_list = util.get_col(output, 4)
#     label_list = util.get_col(output, 6)
#     pre_calc_val = pre_calc(title_list=title_list, body_list=body_list, label_list=label_list, keys_sea=keys_sea)

#     pq = []
#     p_ex = []
#     tsv_list = []

#     for k in keys_sea:
#         keys = []
#         for i in k:
#             keys.append(" ".join(i))
#         keys = " ".join(keys)
#         ess_keys = nlp_util.stem_sentence(keys)

#         # counts_t = search_rank.get_all_key_count(ess_keys, title_list, unique=True)
#         # counts_b = search_rank.get_all_key_count(ess_keys, body_list, unique=True)
#         # print(counts)
#         print("+" * 50)
#         print(ess_keys)
#         tmp = search_rank.sort_candidate_seq(output, ess_keys, pre_calc_val)
#         print_corpus(tmp)
#         print("%" * 50)

#         # add tsv
#         tsv_list.extend(format_result(ess_keys, tmp, 10))

#         pq.extend([(ess_keys, tmp[i]) for i in range(3)])
#         p_ex.extend([(ess_keys, tmp[i]) for i in range(10)])

#     head = ['tag', 'rank', 'issue id', 'issue title', 'total', 'body_len', 'closed', 'commit_id', 'hit_body_all',
#             'hit_body_num', 'hit_hot_words', 'hit_label', 'hit_title_all', 'hit_title_overlap', 'reply_num']

#     tsv_name = util.drop_file_ext(src) + '-' + util.drop_file_ext(test_f)
#     util.dump_tsv('result/{}.tsv'.format(tsv_name), tsv_list, head)
#     util.save_json(util.load_json('conf/rank_coef.json'), 'result/{}.json'.format(tsv_name))

#     print("$" * 50)
#     pq.sort(key=lambda k: k[1][1]['total'], reverse=True)
#     print_result(pq, 200)
#     # count unique
#     tmp1 = pq[:200]
#     issue_set1 = get_issue_set(tmp1)
#     print("issue_set", len(issue_set1))
#     reload.close()

#     reload = util.Reload(postfix="test")
#     print("@" * 50)
#     p_ex.sort(key=lambda k: k[1][1]['total'], reverse=True)
#     print_result(p_ex, 500)
#     # count unique
#     tmp2 = p_ex[:500]
#     issue_set2 = get_issue_set(tmp2)
#     print("issue_set", len(issue_set2))

#     print("issue_set1-issue_set2", issue_set1 - issue_set2)
#     print("issue_set2-issue_set1", issue_set2 - issue_set1)
#     print("issue_set2^issue_set1", issue_set2 ^ issue_set1)

#     reload.close()


# MAIN------------------------------------------------------------------------
logger = logging.getLogger("StreamLogger")
logger.setLevel(logging.INFO)

lt = [
    'Camera-Roll-Android-App-master',
    'PocketHub-master',
    'SimpleMobileTools_Simple_File_Manager_master',
    'zapp-master',
]

for nam in lt:
    # reload = util.Reload()
    _item = f"data/test_f/{nam}.tsv"

    # test code
    # src = "tsv/nextcloud_android_master.tsv"
    # src = select_dir(SRC_DIR)
    src = _item
    src_out = util.read_tsv(src)
    src_out = nlp_util.process_tsv(src_out)

    file_list = os.listdir(SRC_DIR)
    file_list = [os.path.join(SRC_DIR, f) for f in file_list]
    if src in file_list:
        file_list.remove(src)
    # file_list = ['tsv/owncloud_android_master.tsv'] # one test

    scan_output = scan_match(src_out, file_list, match_name.ngram_compare, [1, 0.5, 0.5], threshold=0.7)
    # 得到src app与数据库每个app的总相似度
    logger.debug(pp.pformat(util.get_col(scan_output, [0, 1])))

    rdb = issuedb.ISSuedb()
    sql = """select issue_num, comments, state, title, body, commit_id, labels from {}
                    order by length(body) desc"""
    # remove constrain "where labels like '%bug%' or commit_id is not null"

    overall_table = {}
    # 所有相关app和item
    # for i in range(len(scan_output)):
    for i in range(4):
        one_dict = {}
        app = scan_output[i][0]
        one_dict['sim'] = scan_output[i][1]

        tab_name = table2tsv.file2table(app)
        one_dict['data'] = []
        one_dict['keys'] = []

        score_list = scan_output[i][2]
        keys_sea = filter_search_keys(score_list, threshold=0.7)
        logger.debug(tab_name, "similar keys length:", len(keys_sea))

        output = rdb.db_retrieve(sql.format(tab_name))
        head = ["issue_num", "comments", "state", "title", "body", "commit_id", "labels"]
        f_output = issuedb.retrieve_formatter(head, output)

        title_list = util.get_col(output, head.index('title'))
        body_list = util.get_col(output, head.index('body'))
        label_list = util.get_col(output, head.index('labels'))
        reply_list = util.get_col(output, head.index('issue_num'))
        pre_calc_val = pre_calc(title_list=title_list, body_list=body_list, label_list=label_list,
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

    # 总排序
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
            logger.debug("app_sim", app_sim)
            # 这里需要对 j_score 做 normalize
            over_sort.append((app_name, j, app_com_score))

    over_sort.sort(key=lambda row: row[-1], reverse=True)

    # 调出记录
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

    tsv_header = ['tgt', 'url', "relevant", "reproducible-aBug", ]
    os.makedirs("label", exist_ok=True)
    util.dump_tsv("label/" + util.drop_file_ext(src) + "6.tsv", tsv_data, tsv_header)
    util.dump_csv("label/" + util.drop_file_ext(src) + "6.csv", tsv_data, tsv_header)
    random.shuffle(tsv_data)
    util.dump_tsv("label/" + util.drop_file_ext(src) + "6_shuffled.tsv", tsv_data, tsv_header)
    util.dump_csv("label/" + util.drop_file_ext(src) + "6_shuffled.csv", tsv_data, tsv_header)

    out = util.read_csv(f"merge/Ziqiang_{nam}_merged.csv", encoding='utf-8-sig')
    logger.info(nam)
    re_ct = eval_test.topk(out)

    merge_a = f"label/{nam}6.csv"
    merge_b = f'data/Ziqiang_{nam}_shuffled.csv'

    logger.info("update")
    out = eval_test.merge_csv_file(merge_a, merge_b)
    re_ct = eval_test.topk(out)
    util.dump_csv("tmp/test.csv", out, encoding='utf-8-sig')
