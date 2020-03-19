from model import util, work_path
import os

dir = work_path.in_project("./model/data/description")
a = os.listdir(dir)
a = [os.path.join(dir, i) for i in a]

for i in a:
    b = util.read_csv(i)
    util.dump_tsv(i,b)
    # util.dump_csv(i.replace(".tsv", ".csv"), b)
