import psycopg2


class DatabaseConnection:
    def __init__(self, database: str, user: str = "postgres", host: str = "127.0.0.1", port: str = "5432") -> None:
        self.database = database
        self.user = user
        self.host = host
        self.port = port
        self.connection = psycopg2.connect(database=database, user=user, host=host, port=port)
        self.cursor = self.connection.cursor()

    def __del__(self) -> None:
        if self.cursor is not None:
            self.cursor.close()
        if self.connection is not None:
            self.connection.close()

    def __str__(self) -> str:
        return "database=" + self.database + ", user=" + self.user + ", host=" + self.host + ", port=" + self.port