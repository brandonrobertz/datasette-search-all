async def iterate_searchable_tables(datasette, use_inspect=False):
    if not datasette.inspect_data or not use_inspect:
        for db_name, database in datasette.databases.items():
            hidden_tables = set(await database.hidden_table_names())
            for table in await database.table_names():
                if table in hidden_tables:
                    continue
                fts_table = await database.fts_table(table)
                if fts_table:
                    yield (db_name, table)
    else:
        for db_name, database in datasette.inspect_data.items():
            for table_name, _ in database.get("tables", {}).items():
                if not table_name.endswith("_fts"):
                    continue
                yield (db_name, table_name[:-4])


async def has_searchable_tables(datasette, use_inspect=None):
    # Return True on the first table we find
    async for _ in iterate_searchable_tables(datasette, use_inspect=use_inspect):
        return True
    return False


async def get_searchable_tables(datasette, use_inspect=None):
    tables = []
    async for table in iterate_searchable_tables(datasette, use_inspect=use_inspect):
        tables.append(table)
    return tables
