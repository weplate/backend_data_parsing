import pathlib

from backend.models import MealSelection, MealItem
from data.babson import v0
from data.babson.add_items import SCHOOL_ID, parse_meal_items
from data.babson.add_meals import add_meals

VERSION = 1
FILE_DIR = pathlib.Path(__file__).resolve().parent


def clean_old():
    MealSelection.objects.filter(school__id=SCHOOL_ID, version=VERSION).delete()


def setup():
    clean_old()
    print('Cleaned old data')

    items_by_id = {item.cafeteria_id: item for item in MealItem.objects.filter(version=v0.VERSION).all()}
    meal_item_tuples = []
    for parsed_item in parse_meal_items(VERSION)[0].values():
        if (key := parsed_item['cafeteria_id']) in items_by_id:
            meal_item_tuples.append((items_by_id[key], parsed_item['meal'], key))
    print(f'Prepared {len(meal_item_tuples)} items')
    add_meals(meal_item_tuples, FILE_DIR / 'MenuWorks_Week_at_a_0AA22C06-D72C-48B4-9498-F6FBC87E079F.xlsx', VERSION)
    print('Setup complete!')
