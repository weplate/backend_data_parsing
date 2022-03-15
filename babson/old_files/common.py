import datetime

MEAL_TIMES = (
    ('breakfast', datetime.time(hour=7, minute=30)),
    ('lunch', datetime.time(hour=11)),
    ('afterlunch', datetime.time(hour=14, minute=30)),
    ('dinner', datetime.time(hour=16, minute=30)),
)
MEAL_TIMES_DICT = dict(MEAL_TIMES)
MEAL_KEYS = tuple(map(lambda x: x[0], MEAL_TIMES))
MEAL_SELECTION_COLS = [0, 1, 4, 5, 6, 7, 10]
ALLERGY_INGREDIENTS = ['peanuts', 'tree_nuts', 'eggs', 'soy', 'wheat', 'fish', 'shellfish', 'corn', 'gelatin']