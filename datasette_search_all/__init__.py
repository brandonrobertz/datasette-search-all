import json
import os

from datasette import hookimpl
from datasette.utils.asgi import Response

from .utils import get_searchable_tables, has_searchable_tables


@hookimpl
def menu_links(datasette, actor):
    async def inner():
        if not await datasette.permission_allowed(
            actor, "search-all", default=False
        ):
            return
        if await has_searchable_tables(datasette, use_inspect=True):
            return [
                {"href": datasette.urls.path("/-/search"), "label": "Search all tables"}
            ]

    return inner


async def search_all(datasette, request):
    if not await datasette.permission_allowed(
        request.actor, "search-all", default=False
    ):
        return

    filter_db = request.args.get("db") or ""
    searchable_tables = list(await get_searchable_tables(datasette))
    searchable_dbs = set()
    tables = []
    for database, table in searchable_tables:
        if database not in searchable_dbs:
            searchable_dbs.add(database)
        if filter_db and database != filter_db:
            continue
        url_json = datasette.urls.table(database, table, format="json")
        tables.append({
            "database": database,
            "table": table,
            "url": datasette.urls.table(database, table),
            "url_json": url_json,
        })

    # Look for and load a columns list so we can select which
    # FTS columns to search, grouped by type as provided by
    # the enable_fts_columns.py script
    datasette_path = os.path.split(datasette.files[0])[0]
    labeled_cols_path = os.path.join(datasette_path, "labeled-cols.json")
    labeled_cols = None
    if os.path.exists(labeled_cols_path):
        with open(labeled_cols_path, "r") as f:
            labeled_cols = json.load(f)

    return Response.html(
        await datasette.render_template(
            "search_all.html",
            {
                "q": request.args.get("q") or "",
                "raw": request.args.get("raw") or "",
                "db": filter_db,
                "labeled_cols": labeled_cols,
                "searchable_dbs": sorted(list(searchable_dbs)),
                "searchable_tables": tables,
                "searchable_tables_json": json.dumps(tables, indent=4),
            },
        )
    )


@hookimpl
def extra_template_vars(template, datasette, request):
    if template != "index.html":
        return

    # Add list of searchable tables
    async def inner():
        searchable_tables = list(await get_searchable_tables(
            datasette, use_inspect=True
        ))
        return {"searchable_tables": searchable_tables}

    return inner


@hookimpl
def register_routes():
    return [
        ("/-/search", search_all),
    ]
