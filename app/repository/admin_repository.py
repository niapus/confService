from app.models.admin import Admin

class AdminRepository():
    def get_admin_count(self, session):
        return session.query(Admin).count()

    def get_admin_by_login(self, login, session):
        return session.query(Admin).filter_by(login=login).first()

    def save_all(self, admins, session):
        session.add_all(admins)