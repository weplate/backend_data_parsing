import pandas as pd
import numpy as np
import re
import json

OUT_FILE_PATH = 'meal_items.json'
SCHOOL_ID = 10


def clean_nutrition_table_tail(dfc):
    remove_row = []
    for key in dfc.keys():
        if dfc[key].isna().all() == True:
            dfc.drop(key, axis=1, inplace=True)

    for index, row in dfc.iterrows():
        roll = dfc.index[index]
        if dfc.loc[roll].isnull().all() == True:
            remove_row.append(roll)
    # print(remove_row)
    dfc.drop(range(min(remove_row), len(dfc)), inplace=True)
    return dfc


def clean_nutrient1(z):
    null = None
    if z == '-':
        return null
    elif len(z.split()) > 1:
        z = [float(ss) for ss in z.split() if ss.isdigit()]
        return z[0]
    else:
        z = z.strip('+')
        return float(z)


def clean_category(z):
    null = None
    if z == '-':
        return null
    else:
        return z.lower()


bad_units = set()


def clean_portion(z):
    null = None
    if m := re.search(rf'[cx]up', z):
        return eval(z.strip('[cx]up')) * 236.588
    elif m := re.search(rf'pint', z):
        return eval(z.strip('pint')) * 473
    elif m := re.search(rf'tbsp', z):
        return eval(z.strip('tbsp')) * 14.7866
    elif m := re.search(rf'tsp', z):
        return eval(z.strip('tsp')) * 4.92892
    elif m := re.search(rf'floz', z):
        return eval(z.strip('floz')) * 29.5735
    elif m := re.search(rf'oz', z):
        return eval(z.strip('oz')) * 29.5735
    else:
        bad_units.add(z)
        return null


def nutrition_fact_table(df, df1):
    df = clean_nutrition_table_tail(df)
    df.drop(['Magnesium (mg)', 'Weight (oz)', 'Calories from Fat'], axis=1, inplace=True)

    k = list(df.keys())
    k.remove('Recipe Name')
    rows_nan = np.array(df[k].isnull().all(axis=1))
    section_rows = list(np.where(rows_nan == True)[0])
    MEAL_TYPES = []
    for i in range(len(section_rows)):
        mt = df.loc[section_rows[i], 'Recipe Name']
        if i < len(section_rows) - 1:
            [MEAL_TYPES.append(mt) for ii in range(section_rows[i + 1] - section_rows[i])]
        else:
            [MEAL_TYPES.append(mt) for ii in range(len(df) - 1 - section_rows[i])]
            MEAL_TYPES.append(mt)
    df['station'] = MEAL_TYPES
    df.drop(section_rows, axis=0, inplace=True)
    df['Recipe Number'] = df['Recipe Number'].astype(str)

    keys = {i: re.sub(' ', '_', i.lower()).split('_(')[0] for i in list(df.keys())}
    keys['Recipe Name'] = 'name'
    keys['Recipe Number'] = 'cafeteria_id'
    keys['Portion Size'] = 'portion_volume'
    keys['Weight (g)'] = 'portion_size'
    keys['Dietary Fiber (g)'] = 'fiber'
    keys['Total Carb (g)'] = 'carbohydrate'
    keys['Total Sugars (g)'] = 'sugar'
    df = df.rename(columns=keys)

    df1 = clean_nutrition_table_tail(df1)
    df1.drop('Weight (oz)', axis=1, inplace=True)
    df1['Recipe Number'] = df1['Recipe Number'].astype(str)

    keys1 = {i: re.sub(' ', '_', i.lower()).split('_(')[0] for i in list(df1.keys())}
    keys1['Recipe Name'] = 'name'
    keys1['Recipe Number'] = 'cafeteria_id'
    keys1['Portion Size'] = 'portion_volume'
    keys1['Weight (g)'] = 'portion_size'
    df1 = df1.rename(columns=keys1)

    df_all = pd.merge(df, df1, on=['cafeteria_id', 'portion_size'], how='left',
                      suffixes=('', '_y')).drop(['name_y', 'portion_volume_y'], axis=1)

    df_all.drop_duplicates(inplace=True)
    df_all = df_all.reset_index(drop=True)
    df_all['category'] = df_all['category'].fillna('-')
    df_all['category'] = df_all['category'].apply(lambda z: clean_category(z))

    df_all['vitamin_c'] = df_all['vitamin_c'].apply(lambda z: clean_nutrient1(str(z)))
    df_all['vitamin_d'] = df_all['vitamin_d'].apply(lambda z: clean_nutrient1(str(z)))
    df_all['vitamin_a'] = df_all['vitamin_a'].apply(lambda z: clean_nutrient1(str(z)))
    df_all['calcium'] = df_all['calcium'].apply(lambda z: clean_nutrient1(str(z)))
    df_all['potassium'] = df_all['potassium'].apply(lambda z: clean_nutrient1(str(z)))

    df_all['iron'] = df_all['iron'].apply(lambda z: clean_nutrient1(str(z)))
    df_all['cholesterol'] = df_all['cholesterol'].apply(lambda z: clean_nutrient1(str(z)))
    df_all['fiber'] = df_all['fiber'].apply(lambda z: clean_nutrient1(str(z)))
    df_all['protein'] = df_all['protein'].apply(lambda z: clean_nutrient1(str(z)))
    df_all['sugar'] = df_all['sugar'].apply(lambda z: clean_nutrient1(str(z)))
    df_all['carbohydrate'] = df_all['carbohydrate'].apply(lambda z: clean_nutrient1(str(z)))

    df_all['portion_volume'] = df_all['portion_volume'].apply(lambda z: clean_portion(z))
    df_all['portion_size'] = df_all['portion_size'].apply(lambda z: float(z.strip('g')))

    df_all['station'] = df_all['station'].apply(lambda z: z.split('-')[1].strip())

    df_all = df_all.replace({np.nan: None})

    return df, df1, df_all


def parse_fixture(d, out_filename):
    result = d.to_dict(orient='index')
    json_list = []

    for r in range(len(result)):
        data = {'model': 'backend.MealItem', 'pk': {}, 'field': {}}
        f = result[r]
        data['pk'] = f['pk']
        f.pop('pk')
        data['field'] = f
        json_list.append(data)

    with open(out_filename, 'w') as out_file:
        json.dump(json_list, out_file, sort_keys=False)
    out_file.close()


def main():
    df = pd.read_excel(r'nutrition/MenuWorks_FDA_Menu_Main_W9-11_2022.xlsx', skiprows=11,
                       converters={'Recipe Number': lambda x: str(x)})
    dfa = pd.read_excel(r'nutrition/MenuWorks_FDA_Menu_Alt_W9-11_2022.xlsx', skiprows=11,
                        converters={'Recipe Number': lambda x: str(x)})

    df, dfa, df_combine = nutrition_fact_table(df, dfa)
    df_combine['pk'] = range(1000, 1000 + len(df_combine))
    df_combine['school'] = [SCHOOL_ID for ii in range(len(df_combine))]
    df_combine.to_csv('Nutrition_Table_W9-11_2022.csv')
    parse_fixture(df_combine, OUT_FILE_PATH)


if __name__ == '__main__':
    main()
