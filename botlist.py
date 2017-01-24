from model import Category


def build():
    result = list()
    categories = Category.select()
    for cat in categories:
        cat_bots = list()
        for bot in :
            cat_bots.append(str(bot))
        result.append(cat_bots)

    return result
