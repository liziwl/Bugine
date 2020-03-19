from celery import Celery
from celery.result import AsyncResult
from model import util
from api import descript, query_issue, sort_result_table, get_out

brokers = 'redis://127.0.0.1:6379/2'
backend = 'redis://127.0.0.1:6379/3'

cel_app = Celery('tasks', broker=brokers, backend=backend)
cel_app.conf.timezone = 'Asia/Shanghai'
cel_app.conf.enable_utc = True


@cel_app.task
def iss_query(csv_path, except_file_list, pool_size=12):
    data = util.read_csv(csv_path)
    scan_output = descript(data, except_files=except_file_list, pool_size=pool_size)
    overall_table = query_issue(scan_output, max_depth=3)
    overall_sort = sort_result_table(overall_table)
    out = get_out(overall_sort, overall_table)
    return out


def job_ready_byid(id):
    res = AsyncResult(id, app=cel_app)
    return res.ready()


def job_get_byid(id):
    res = AsyncResult(id, app=cel_app)
    data = res.get()
    f_data = []
    for i in range(len(data)):
        tmp = [i+1, ]
        tmp.extend(data[i])
        f_data.append(tmp)
    return {
        'data': f_data,
        'date_done': res.date_done + "+00:00"
    }
