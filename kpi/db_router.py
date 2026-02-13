class CarfixRouter:

    def db_for_read(self, model, **hints):
        if model._meta.model_name == 'user':
            return 'carfix_user'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.model_name == 'user':
            return 'carfix_user'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if model_name == 'user':
            return db == 'carfix_user'
        return db == 'default'