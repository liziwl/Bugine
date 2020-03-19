import sqlite3
import csv
from collections import namedtuple
import logging
from model import work_path

new_app_sql = """create table if not exists {} (
  title     VARCHAR(500),
  user      VARCHAR(100)    not null,
  id        int             not null        primary key on conflict replace,
  issue_num int             not null,
  comments  int,
  labels    VARCHAR(200),
  state     VARCHAR(50)     not null,
  created   int             not null,
  updated   int             not null,
  closed    int,
  body      VARCHAR(10000)
);"""

drop_app_sql = "DROP TABLE IF EXISTS {};"

datetime_cov = "strftime('%s','{}')"

insert_com_sql = """INSERT INTO {} (title,user,id,issue_num,comments,labels,state,created,updated,closed,body)
VALUES ('{}','{}',{},{},{},'{}','{}',###,###,###,'{}');""".replace("###", datetime_cov)

select_app_sql = """SELECT title,user,id,issue_num,comments,labels,state,
                 datetime(created,'unixepoch') as created,
                 datetime(updated,'unixepoch') as updated,
                 datetime(closed,'unixepoch') as closed,
                 body from {};"""


def get_header():
    return ["title", "requester", "id", "issue_num", "label", "comments", "state", "create day", "update day",
            "close day", "body"]


def retrieve_formatter(header, data):
    Row_db = namedtuple('Row_db', header)
    rt = []
    for it in data:
        rt.append(Row_db._make(it))
    return rt


def insert_table(cursor, tb_name, data):
    tmp_data = []
    tmp_data.append(tb_name)
    tmp_data.extend(data)
    exc_sql = insert_com_sql.format(*tmp_data)
    logger = logging.getLogger("StreamLogger")
    logger.debug(exc_sql)
    cursor.execute(exc_sql)


def create_table(cursor, tb_name):
    exc_sql = new_app_sql.format(tb_name)
    logger = logging.getLogger("StreamLogger")
    logger.info(exc_sql)
    cursor.execute(exc_sql)


def drop_table(cursor, tb_name):
    exc_sql = drop_app_sql.format(tb_name)
    logger = logging.getLogger("StreamLogger")
    logger.info(exc_sql)
    cursor.execute(exc_sql)


class ISSuedb:
    def __init__(self, filepath=work_path.in_project('issue.db')):
        logger = logging.getLogger("StreamLogger")
        logger.info("DB file location: %s" % filepath)
        self.conn = sqlite3.connect(filepath)
        self.cursor = self.conn.cursor()

    def _db_commit(self):
        self.conn.commit()

    def db_close(self):
        self.conn.close()

    def db_newtable(self, tb_name):
        create_table(self.cursor, tb_name)
        self._db_commit()

    def db_droptable(self, tb_name):
        drop_table(self.cursor, tb_name)
        self._db_commit()

    def db_insert_row(self, tb_name, data):
        insert_table(self.cursor, tb_name, data)
        self._db_commit()

    def db_retrieve(self, sql):
        logger = logging.getLogger("StreamLogger")
        logger.info(sql)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return rows

    def db_run(self, sql):
        logger = logging.getLogger("StreamLogger")
        logger.info(sql)
        self.cursor.execute(sql)
        self._db_commit()

    def dump_csv(self, tb_name):
        with open(tb_name + '.csv', "w", encoding="utf_8_sig", newline='') as app_review_file:
            f_csv = csv.writer(app_review_file)
            f_csv.writerow(get_header())
            self.cursor.execute(select_app_sql.format(tb_name))
            rows = self.cursor.fetchall()
            f_csv.writerows(rows)


if __name__ == '__main__':
    rdb = ISSuedb()
    rdb.db_newtable("nextcloud$android")
    # rdb.cursor.execute(select_app_sql.format("nextcloud$android"))
    # rows = rdb.cursor.fetchall()
    rows = rdb.db_retrieve(select_app_sql.format("nextcloud$android"))
    rdb.dump_csv("nextcloud$android")
    rdb.db_close()
