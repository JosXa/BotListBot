class Layouts:
    _LAYOUTS = {
        'categories': {
            'caption': '📚 Bots per Category',
            'next': 'single'
        },
        'single': {
            'caption': '📜 Single list of Bots',
            'next': 'categories'
        }
    }

    @staticmethod
    def choices():
        return list(Layouts._LAYOUTS.keys())

    @staticmethod
    def default():
        return Layouts.choices()[0]

    @staticmethod
    def get_caption(layout):
        try:
            return Layouts._LAYOUTS[layout]['caption']
        except:
            return Layouts.default()

    @staticmethod
    def get_next(layout):
        try:
            return Layouts._LAYOUTS[layout]['next']
        except:
            return Layouts.get_next(Layouts.default())