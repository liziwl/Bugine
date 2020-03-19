import csv
import copy
from ngram import NGram
import os
import numpy as np
from model import util

# import matplotlib.pyplot as plt
# import spacy

pp = util.PrintWarp()


# 这边不需要移除停止词


def similar_index(score_list, threshold, col_index, rate=True):
    ct = 0
    for s in score_list:
        if s[col_index] >= threshold:
            ct += 1
    if rate:
        return ct / len(score_list)
    else:
        return ct


def weight_compare_list(source_wl, target_wl, comp_func, weight_list=None):
    """
    wl is words list like -- [[["drawer", "header"], ["ImageView"], ["drawer", "current", "account"]],...].
    :param source_wl: 3 dim list as source
    :param target_wl: 3 dim list as target
    :param comp_func: can be ngram_compare, jaccard_compare, dice_compare
    :param weight_list: weight each col in 2rd list
    :return: each row in source_wl (best effort) search matching target row in target_wl. [(_w1, _w2, _score),...]
    """
    if weight_list is None:
        raise Exception("No weight")
    weight = np.array(weight_list)
    out = []
    for w1 in source_wl:
        score_max = -1
        for w2 in target_wl:

            # compare each word by the sequence
            _score_list = []
            zipped = zip(w1, w2)
            for z_w1_w2 in zipped:
                _score_list.append(comp_func(*z_w1_w2))

            # mask the word with "#" if its weight is zero
            _w1 = ""
            _w2 = ""
            zipped = zip(w1, w2, weight_list)
            for z in zipped:
                tmp_w1, tmp_w2, w = z
                _w1 += "^".join(tmp_w1) if w != 0 else "#"
                _w1 += "="
                _w2 += "^".join(tmp_w2) if w != 0 else "#"
                _w2 += "="
            _w1 = _w1[:-1] if _w1[-1] else ""
            _w2 = _w2[:-1] if _w2[-1] else ""

            _score = np.sum(np.array(_score_list) * weight)
            # print('W1:{};\tW2:{};\tScore:{}'.format(_w1, _w2, _score))

            if _score > score_max:
                score_max = _score
                tuple_max = (_w1, _w2, _score)
        if score_max > 0:
            out.append(copy.deepcopy(tuple_max))
            # print('W1:{};\tW2:{};\tScore:{}'.format(*tuple_max))
    return sorted(out, key=lambda k: k[-1], reverse=True)


def ngram_compare(source_wl, target_wl):
    _w1, _w2 = " ".join(source_wl).lower(), " ".join(target_wl).lower()
    return NGram.compare(_w1, _w2)


def jaccard_compare(source_wl, target_wl):
    src = set(source_wl)
    tgt = set(target_wl)
    return 1.0 * len(src & tgt) / len(src | tgt)


def dice_compare(source_wl, target_wl):
    src = set(source_wl)
    tgt = set(target_wl)
    return 1.0 * len(src & tgt) / min(len(src), len(tgt))


def test():
    # import search_rank
    # import matplotlib.pyplot as plt
    # import numpy as np
    #
    # bins = np.linspace(0, 1, 100)
    # plt.hist(util.get_col(list_score, 2), bins, density=True, histtype='step', cumulative=-1, label='Empirical')
    # plt.show()

    path = "tsv/"
    filelist = os.listdir(path)
    filelist.sort(key=lambda x: x.lower())
    out_dict = dict()

    count = 0
    for file in filelist:
        count += 1
        full_path = os.path.join(path, file)
        print(full_path)
        tmp_out = util.read_tsv(full_path)
        out_dict[file] = nlp_util.process_tsv(tmp_out)

    print("file count", count)

    count = 0
    score_distribute_list = []
    for i in range(len(filelist)):
        i_file = filelist[i]
        for j in range(len(filelist)):
            if i == j:
                print("Ignore same file", i_file)
                continue
            count += 1
            j_file = filelist[j]
            name = "{}^{}".format(i_file, j_file)
            if len(out_dict[i_file]) == 0 or len(out_dict[j_file]) == 0:
                print("EMPTY", name)
                list_score = []
                continue
            else:
                list_score = weight_compare_list(
                    out_dict[i_file], out_dict[j_file], ngram_compare)
            score_col = util.get_col(list_score, 2)

            score_distribute_list.append((name, copy.deepcopy(score_col)))
            print("ADD", count, name)

    util.save_json(score_distribute_list, "score_distribute_list.json")
    # plt_li = util.load_json("score_distribute_list.json")


if __name__ == "__main__":
    from model import nlp_util
    reload = util.Reload()

    next_list = []
    with open("tsv/hakr_AnExplorer_master.tsv", 'r', encoding='utf8') as next_f:
        # with open("tsv/nextcloud_android_master.tsv", 'r', encoding='utf8') as next_f:
        tsvreader = csv.reader(next_f, delimiter="\t")
        for line in tsvreader:
            next_list.append(line)

    own_list = []
    # with open("tsv/owncloud_android_master.tsv", 'r', encoding='utf8') as own_f:
    with open("tsv/tasks_tasks_master.tsv", 'r', encoding='utf8') as own_f:
        tsvreader = csv.reader(own_f, delimiter="\t")
        for line in tsvreader:
            own_list.append(line)

    next_list, own_list = map(nlp_util.process_tsv, [next_list, own_list])
    list_score = weight_compare_list(
        own_list, next_list, ngram_compare, [0.5, 0.5, 1])
    print("len:", len(list_score))
    pp.pprint(list_score)
    import map_issue

    a = map_issue.filter_search_keys(list_score, threshold=0.6)
    print("0" * 50)
    pp.pprint(a)

    # test()
