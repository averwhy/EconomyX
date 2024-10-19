class db:
    user = "ecox"
    password = "poggersEcoDB777"

    def dsn(self):
        return f"postgres://{self.user}:{self.password}@127.0.0.1:39468/ecoxdb"
