from django.db import connection


def query(sql, params=()):
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def one(sql, params=()):
    from .http import ApiError

    rows = query(sql, params)
    if not rows:
        raise ApiError(404, "El registro no existe.")
    return rows[0]


# Las tablas y columnas vienen de los módulos de la API, nunca de la solicitud.
def insert(table, data):
    columns = ", ".join(data)
    placeholders = ", ".join(["%s"] * len(data))
    with connection.cursor() as cursor:
        cursor.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", tuple(data.values()))
        return cursor.lastrowid


def update(table, record_id, data):
    if data:
        assignments = ", ".join(f"{column} = %s" for column in data)
        with connection.cursor() as cursor:
            cursor.execute(f"UPDATE {table} SET {assignments} WHERE id = %s", (*data.values(), record_id))
