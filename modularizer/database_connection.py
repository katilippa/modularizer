import psycopg2


class DatabaseConnection:
    def __init__(self, connection: dict) -> None:
        self.database = connection["database"]
        self.user = connection["user"]
        self.host = connection["host"]
        self.port = connection["port"]
        if 'password' in connection.keys():
            self.connection = psycopg2.connect(database=connection["database"],  user=connection["user"],
                                               password=connection['password'], host=connection["host"],
                                               port=connection["port"])
        else:
            self.connection = psycopg2.connect(database=connection["database"],  user=connection["user"],
                                               host=connection["host"], port=connection["port"])
        self.cursor = self.connection.cursor()

    def __str__(self) -> str:
        return "database=" + self.database + ", user=" + self.user + ", host=" + self.host + ", port=" + self.port