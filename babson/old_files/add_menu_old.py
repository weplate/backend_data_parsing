import pandas as pd
import numpy as np
import re
import json
from dateutil.parser import parse

OUT_FILE_PATH = 'menu_items.json'
SCHOOL_ID = 10
MLTYPE_CONST1 = ['Breakfast', 'Lunch', 'Dinner']


def clean_table(dfc):
    for key in dfc.keys():
        if dfc[key].isna().all() == True:
            dfc.drop(key, axis=1, inplace=True)
    return dfc


def meal(z):
    if "Breakfast" in z:
        return "7:30 am", "breakfast"
    elif "Lunch" in z:
        if "FLAME" in z:
            return "2:30 pm", "afterlunch"
        elif '500 DEGREES' in z:
            return "2:30 pm", "afterlunch"
        elif 'CARVED AND CRAFTED' in z:
            return "2:30 pm", "afterlunch"
        else:
            return "11:00 am", "lunch"
    elif "Dinner" in z:
        return "4:30 pm", "dinner"


def weekly_menu_dict(dfm, dfd, row_begin, row_end, pk_begin):
    if row_begin == 0:
        dfmw = dfm.loc[row_begin:row_end - 1, :].reset_index(drop=True)
        week_num = int(str(list(dfmw.keys())[-1]).strip('Week'))
        dfmw_keys = dfm.iloc[0]
        dfmw.drop(0, inplace=True)
    else:
        dfmw = dfm.loc[row_begin:row_end - 1, :]
        week_num = int(dfmw.loc[row_begin, list(dfmw.keys())[-1]].strip('Week'))
        dfmw_keys = dfm.iloc[row_begin + 1]
        dfmw.drop([row_begin, row_begin + 1], inplace=True)

    dfmw.columns = dfmw_keys
    dfmw.drop(dfmw_keys[-1], axis=1, inplace=True)
    dfmw = dfmw.reset_index(drop=True)

    endl = []
    for i in range(len(dfmw)):
        if 'end' in list(dfmw.iloc[i]):
            endl.append(i)
    dfmw.drop(endl, axis=0, inplace=True)
    dfmw = dfmw.reset_index(drop=True)

    first_key = list(dfmw_keys)[0]
    meal_ind = [list(dfmw.loc[dfmw[first_key].str.contains(ml, na=False)].index)
                for ml in MLTYPE_CONST1]
    meal_ind = sorted([t for tt in meal_ind for t in tt])

    MEAL_TYPES = []
    for i in range(len(meal_ind)):
        mt = dfmw.loc[meal_ind[i], first_key]
        if i < len(meal_ind) - 1:
            [MEAL_TYPES.append(mt) for ii in range(meal_ind[i + 1] - meal_ind[i])]
        else:
            [MEAL_TYPES.append(mt) for ii in range(len(dfmw) - 1 - meal_ind[i])]
            MEAL_TYPES.append(mt)
    dfmw['Meal_Types'] = MEAL_TYPES
    dfmw['Meal_Time'], dfmw['Meal'] = zip(*dfmw['Meal_Types'].apply(lambda z: meal(z)))

    DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    days_d = dict(zip(DAYS, list(dfmw.keys())))

    days_d['Week'] = week_num

    MENU_WEEKLY = []
    pk_val = pk_begin
    for d in DAYS:
        for meal_key, df_t in dfmw.groupby('Meal'):
            food = {'model': 'backend.MealSelection', 'pk': str(pk_val)}
            fields = {}
            f = []
            df_t = df_t.reset_index(drop=True)
            fields['group'] = meal_key
            s = re.sub(r"[\([{})\]]", '', days_d[d].strip('d')) + ' ' + df_t.loc[0, 'Meal_Time']
            tt = parse(s)
            fields['timestamp'] = tt.strftime("%Y-%m-%d %H:%M:%SZ")
            fields['name'] = meal_key.title() + " on " + d + ', ' + tt.strftime("%B %d, %Y")
            fields['school'] = SCHOOL_ID
            for index, row in df_t.iterrows():
                try:
                    dish = float(row[days_d[d]])
                    f.append(row[days_d[d]])
                except:
                    pass
            f = [x for x in f if str(x) != 'nan']
            q = [int(dfd.loc[dfd['cafeteria_id'] == x, 'pk'].values[0])
                 for x in f if not dfd.loc[dfd['cafeteria_id'] == x, 'pk'].empty]

            fields['items'] = q
            food['fields'] = fields
            MENU_WEEKLY.append(food)
            pk_val += 1
    return MENU_WEEKLY, dfmw


def main():
    #dfd = pd.read_csv(r'Nutrition_Table_W9-11_2022.csv', converters={'cafeteria_id': lambda x: str(x)})
    dfd = pd.read_csv(r'master_nutrition\nutrition_table.csv', converters={'cafeteria_id': lambda x: str(x)})
    #dfm = pd.read_excel(r'menu\MenuWorks_Week_at_a_0AA22C06-D72C-48B4-9498-F6FBC87E079F.xlsx', skiprows=11)
    dfm = pd.read_excel(r'menu\MenuWorks_W11_2022.xlsx', skiprows=11)
   
    dfm = clean_table(dfm)

    k = str(list(dfm.keys())[0])
    split_row = [0]
    for i in range(len(dfm)):
        if 'TRIM' in str(dfm.loc[int(i), k]):
            split_row.append(i)

    MENU = []
    pk_begin = 1000
    for mm in range(len(split_row) - 1):
        menuw1, dfmw1 = weekly_menu_dict(dfm, dfd, split_row[mm], split_row[mm + 1], pk_begin)
        pk_begin = pk_begin + len(menuw1) - 1
        MENU.extend(menuw1)
    with open(OUT_FILE_PATH, 'w') as out_file:
        json.dump(MENU, out_file, sort_keys=False)
    out_file.close()


if __name__ == '__main__':
    main()
