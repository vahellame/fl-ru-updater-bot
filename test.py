import psycopg2

from contextlib import closing
from psycopg2.extras import RealDictCursor, Json
from config import POSTGRES_CONNECTION_PARAMS


def execute_sql(sql_query, connection_params):
    with closing(psycopg2.connect(cursor_factory=RealDictCursor,
                                  dbname=connection_params["dbname"],
                                  user=connection_params["user"],
                                  password=connection_params["password"],
                                  host=connection_params["host"],
                                  port=connection_params["port"],
                                  )) as conn:
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(sql_query)
            try:
                records = cursor.fetchall()
                result = []
                for record in records:
                    result.append(dict(record))
                return result
            except psycopg2.ProgrammingError:
                pass


user = {
    "id": 42,
    "telegram_id": 42,
    "project_types": {
        "/freelancers/razrabotka-sajtov": [
            "/freelancers/copywriter-razrabotka-sajtov/",
            "no_specialty"
        ]
    }
}
# execute_sql(f"INSERT into users (info) VALUES ({Json(d)})", POSTGRES_CONNECTION_PARAMS)

res = execute_sql("SELECT * FROM users", POSTGRES_CONNECTION_PARAMS)

5556