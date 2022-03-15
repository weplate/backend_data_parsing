import pathlib

from backend.models import MealSelection, MealItem, Ingredient, School
from data.babson.add_items import SCHOOL_ID, add_meal_items
from data.babson.add_meals import add_meals
from data.babson.common import ALLERGY_INGREDIENTS

VERSION = 0
FILE_DIR = pathlib.Path(__file__).resolve().parent


def clean_old():
    MealSelection.objects.filter(school__id=SCHOOL_ID, version=VERSION).delete()
    MealItem.objects.filter(school__id=SCHOOL_ID, version=VERSION).delete()
    Ingredient.objects.filter(school__id=SCHOOL_ID, version=VERSION).delete()


def add_ingredients():
    babson = School.objects.get(pk=SCHOOL_ID)
    objs = []
    for name in ALLERGY_INGREDIENTS:
        objs.append(Ingredient(name=name, school=babson, version=VERSION))
    objs = Ingredient.objects.bulk_create(objs)
    return {obj.name: obj for obj in objs}


def setup():
    clean_old()
    print('Cleaned old data')
    _ = add_ingredients()
    print(f'Added {len(_)} ingredients')
    meal_items = add_meal_items(VERSION)
    print(f'Added {len(meal_items)} meal items to DB')
    add_meals(meal_items, FILE_DIR / 'Menuworks_.xlsx', VERSION)
    print('Setup complete!')
