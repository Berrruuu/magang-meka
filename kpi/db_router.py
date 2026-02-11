class CarfixRouter:
    USER_MODELS = {'user', 'companyuser'}

    def db_for_read(self, model, **hints):
        if model._meta.model_name in self.USER_MODELS:
            return 'carfix_user'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.model_name in self.USER_MODELS:
            return 'carfix_user'
        return 'default'
