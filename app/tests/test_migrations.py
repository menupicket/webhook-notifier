import unittest

import alembic.config

from app.tests.utils import engine_sync, table_metadata


class MigrationsTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        # Drop the configured schema
        table_metadata().drop_all(engine_sync())

    def tearDown(self):
        # Re-create the schema for further tests
        table_metadata().create_all(engine_sync())
        super().tearDown()

    def test_migrations_upgrade_downgrade(self):
        alembic.config.main(argv=["stamp", "base"])
        alembic.config.main(argv=["upgrade", "head"])
        alembic.config.main(argv=["downgrade", "base"])
