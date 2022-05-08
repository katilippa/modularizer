import psycopg2


class DatabaseConnection:
    def __init__(self, database: str, user: str = "postgres", host: str = "127.0.0.1", port: str = "5432") -> None:
        self.database = database
        self.user = user
        self.host = host
        self.port = port
        self.connection = psycopg2.connect(database=database, user=user, host=host, port=port)
        # TODO handle connection failure
        print("Successful database connection: " + str(self))
        self.cursor = self.connection.cursor()

    def __del__(self) -> None:
        self.cursor.close()
        self.connection.close()

    def __str__(self) -> str:
        return "database=" + self.database + ", user=" + self.user + ", host=" + self.host + ", port=" + self.port