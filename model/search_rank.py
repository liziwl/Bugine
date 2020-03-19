import copy
import logging
from model import util, work_path

CONF_JSON = util.load_json(work_path.in_project('./model/conf/rank_coef.json'))
SCORE_COEF = CONF_JSON["data"]
MAX_VAL = CONF_JSON["scale_max"]


def get_key_sea_count(all_key, text, unique=False):
    if type(text) != set:
        f_c = set(text) if unique else text
    count_dict = {}
    for k in all_key:
        count_dict[k] = 0
    for k in f_c:
        if k in all_key:
            count_dict[k] += 1
    count_dict["__corpus_len__"] = len(f_c)
    return copy.deepcopy(count_dict)


def get_key_sea_count_corpus(all_key, corpus, unique=False):
    key_count = []
    if type(all_key) != set:
        all_key = set(all_key)
    for c in corpus:
        key_count.append(get_key_sea_count(all_key, c, unique))
    return key_count


def map_value_range(list_range, mod, reversed=False):
    """
    map a range to another range by a function
    :param list: list of range
    :param mod: mode
    :param reversed: reverse map a list
    :return: mapped value
    """
    pass


def calc_overlap(key_dict, ess_keys):
    # ess_keys ensure all in key_dict
    key_len = key_dict["__corpus_len__"]
    if key_len == 0:
        return 0, False, None
    ess_keys = set(ess_keys)
    hit = 0
    all_hit = True
    out = []
    for k in ess_keys:
        if key_dict[k] > 0:
            hit += 1
            out.append(k)
        else:
            all_hit = False
    overlap = hit / min(len(ess_keys), key_len)
    if len(out) == 0:
        out = None
    return (overlap, all_hit, out)


def calc_exist(key_dict, scale_max):
    ct = 0
    for k in key_dict:
        if k != '__corpus_len__' and key_dict[k] > 0:
            ct += 1
    if ct > scale_max:
        return scale_max
    else:
        return ct


def hit_key_list(key_dict):
    out = []
    for k in key_dict:
        if k != '__corpus_len__' and key_dict[k] > 0:
            out.append(k)
    if len(out) == 0:
        return None
    else:
        return out


def sort_candidate_seq(corpus, ess_keys, pre_calc_vlaue):
    tmp = calc_candidate_seq(corpus, ess_keys, pre_calc_vlaue)
    tmp = sorted(tmp, reverse=True, key=lambda row: row[-1]["total"])
    return list(tmp)


def min_max_scale(min_v, max_v, value):
    if value < min_v:
        return 0
    elif value > max_v:
        return 1
    else:
        return (value - min_v) / (max_v - min_v)


def calc_candidate_seq(corpus, ess_keys, pre_calc_vlaue):
    """
    这里需要改进close / comment num 排序

    1. hit 数量排序， hit除总数排序，overlap排序
    2. 状态排序 status
    3. comment length
    4. body length
    5. “step” key words
    """
    score = []
    for i in range(len(corpus)):
        r = corpus[i]

        status = True if r.state == "closed" else False

        reply_num = r.comments  # FFFFFFFFFFFFFFFFFFFF
        body_len = pre_calc_vlaue["body_len"][i]  # FFFFFFFFFFFFFFFFFFFF

        hit_count_title = pre_calc_vlaue["hit_count_title"][i]
        hit_count_body = pre_calc_vlaue["hit_count_body"][i]
        hit_count_hot = pre_calc_vlaue["hit_count_hot"][i]
        hit_count_label = pre_calc_vlaue["hit_count_label"][i]
        commit_id = len("" if r.commit_id is None else r.commit_id.split("#"))
        commit_id = 0 if commit_id == 0 else 1

        t_over, t_all_hit, t_hit_key = calc_overlap(hit_count_title, ess_keys)
        b_over, b_all_hit, b_hit_key = calc_overlap(hit_count_body, ess_keys)

        the_score_detail = copy.deepcopy(SCORE_COEF)
        the_score_detail['hit_hot_words']['val'] = calc_exist(hit_count_hot, scale_max=MAX_VAL)
        the_score_detail['hit_hot_words']['explain'] = hit_key_list(hit_count_hot)
        the_score_detail['hit_label']['val'] = calc_exist(hit_count_label, scale_max=MAX_VAL)
        the_score_detail['hit_label']['explain'] = hit_key_list(hit_count_label)
        the_score_detail['hit_title_overlap']['val'] = t_over
        the_score_detail['hit_title_overlap']['explain'] = t_hit_key
        the_score_detail['hit_title_all']['val'] = t_all_hit
        the_score_detail['hit_body_num']['val'] = b_over
        the_score_detail['hit_body_num']['explain'] = b_hit_key
        the_score_detail['hit_body_all']['val'] = b_all_hit
        the_score_detail['closed']['val'] = status
        the_score_detail['reply_num']['val'] = min_max_scale(0, pre_calc_vlaue["stat"]["max-reply"],
                                                             reply_num)  # FFFFFFFFFFFFFFFFFFFF
        the_score_detail['commit_id']['val'] = commit_id
        the_score_detail['body_len']['val'] = min_max_scale(0, pre_calc_vlaue["stat"]["max-body_len"],
                                                            body_len)  # FFFFFFFFFFFFFFFFFFFF

        for i in the_score_detail:
            the_score_detail[i]["z_term"] = the_score_detail[i]["coef"] * the_score_detail[i]["val"]

        the_score_detail["total"] = sum([the_score_detail[i]["z_term"] for i in the_score_detail])
        score.append(the_score_detail)

    tmp = zip(corpus, score)
    return list(tmp)


if __name__ == '__main__':
    from model import nlp_util
    from model import issuedb

    reload = util.Reload()
    rdb = issuedb.ISSuedb()
    sql = """select issue_num, comments, state, title, body, commit_id from {} 
    where labels like '%bug%' or commit_id is not null order by length(body) desc"""

    # all_cor = []
    # std_tbs = url_repo.get_std_name_list(github=True)
    # for tb in std_tbs:
    #     output = rdb.db_retrieve(sql.format(tb))
    #     for i in range(len(output)):
    #         tmp = list(output[i])
    #         tmp.insert(0, tb)
    #         tmp = tuple(tmp)
    #         all_cor.append(tmp)
    #
    # # pp.pprint(all_cor)
    #
    # title_list = util.get_col(all_cor, 4)
    # title_list = process(title_list)
    #
    # keys = "upload files"
    # ess_keys = stem_sentence(keys)
    # counts = get_all_key_count(ess_keys, title_list, unique=True)
    #
    # body_list = util.get_col(all_cor, 5)
    # body_list = process(body_list)
    # step_keys = "reproduce steps"
    #
    # ess_step_keys = stem_sentence(step_keys)
    # step_counts = get_all_key_count(ess_step_keys, body_list)
    #
    # # pp.pprint(step_counts)
    #
    # print("-" * 50)
    # # pp.pprint(counts)
    # sort_candidate(all_cor, counts)

    # output = rdb.db_retrieve(sql.format("slapperwan$gha"))
    # output = rdb.db_retrieve(sql.format("kshksh$FastHub"))
    output = rdb.db_retrieve(sql.format("nextcloud$android"))

    # print(output)
    # title_list = util.get_col(output, 3)
    # title_list = nlp_util.stem_corpus(title_list)
    #
    # body_list = util.get_col(output, 4)
    # body_list = nlp_util.stem_corpus(body_list)

    keys = "toolbar"
    ess_keys = nlp_util.stem_sentence(keys)

    pp = util.PrintWarp()

    # counts_t = get_all_key_count(ess_keys, title_list, unique=True)
    # counts_b = get_all_key_count(ess_keys, body_list, unique=True)
    # print(counts)
    # pp.pprint(sort_candidate(output, counts_t, counts_b))

    tmp = sort_candidate_seq(output, ess_keys)
    print(tmp[0][0][:4])
    print(tmp[0][1])
    # pp.pprint(tmp)
