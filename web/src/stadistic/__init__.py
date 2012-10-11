class StadisticRouter(object):
    """A router to control all database operations on models in
    the stadistic application"""

    def db_for_read(self, model, **hints):
        "Point all operations on myapp models to 'other'"
        if model._meta.app_label == 'stadistic':
            return 'nonrel'
        return 'default'

    def db_for_write(self, model, **hints):
        "Point all operations on stadistic models to 'other'"
        if model._meta.app_label == 'stadistic':
            return 'nonrel'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        "Deny any relation if a model in stadistic is involved"
        if obj1._meta.app_label == 'stadistic' or obj2._meta.app_label == 'stadistic':
            return True
        return True

    def allow_syncdb(self, db, model):
        "Make sure the stadistic app only appears on the 'nonrel' db"
        if db == 'nonrel':
            return model._meta.app_label == 'stadistic'
        elif model._meta.app_label == 'stadistic':
            return False
        return True