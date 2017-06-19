from playhouse.migrate import *

import appglobals
import const

migrator = SqliteMigrator(appglobals.db)

if __name__ == '__main__':
    migrate(
        migrator.add_column('user', 'favorites_layout', CharField(choices=const.Layouts.choices, default=const.Layouts.default))
    )
