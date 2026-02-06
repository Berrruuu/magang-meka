class UserRouter:
    def db_for_read(self, model, **hints):
        if model._meta.db_table == 'users':
            return 'carfix_user'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.db_table == 'users':
            return 'carfix_user'
        return None
