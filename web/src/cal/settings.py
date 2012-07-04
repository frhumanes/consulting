# -*- encoding: utf-8 -*-

from datetime import datetime, date, time

START_TIME = time(8, 0, 0)
END_TIME = time(20, 0, 0)

TOTAL_HOURS = datetime.combine(date.today(), END_TIME) - \
    datetime.combine(date.today(), START_TIME)
