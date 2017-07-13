from playhouse.migrate import *

import appglobals
import components.favorites
import layouts
import const

migrator = SqliteMigrator(appglobals.db)

if __name__ == '__main__':
    migrate(
        migrator.add_column('user', 'favorites_layout', CharField(choices=layouts.Layouts.choices(), default=layouts.Layouts.default()))
    )
