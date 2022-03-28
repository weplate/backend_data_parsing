import pandas as pd
import numpy as np
import re
import json
from dateutil.parser import parse

OUT_FILE_PATH = 'menu_items.json'
MENU_PRIOR_UPDATED = 'master_menu/menu_backup.csv'
MENU_LATEST = 'master_menu/menu.csv'

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


def weekly_menu_dict(dfm, dfd, row_begin, row_end):
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
    
    meals, timestamps, groups, names, weeknums, meals_recipe_num = [[] for i in range(6)]
    days_d['Week'] = week_num

    for d in DAYS:
        for meal_key, df_t in dfmw.groupby('Meal'):
            f = []
            df_t = df_t.reset_index(drop=True)
            s = re.sub(r"[\([{})\]]", '', days_d[d].strip('d')) + ' ' + df_t.loc[0, 'Meal_Time']
            tt = parse(s)
            timestamps.append(tt.strftime("%Y-%m-%d %H:%M:%SZ"))
            groups.append(meal_key)
            names.append(meal_key.title() + " on " + d + ', ' + tt.strftime("%B %d, %Y"))
            weeknums.append(week_num)
            for index, row in df_t.iterrows():
                try:
                    dish = float(row[days_d[d]])
                    f.append(row[days_d[d]])
                except:
                    pass
            f = [x for x in f if str(x) != 'nan']
            q = [int(dfd.loc[dfd['cafeteria_id'] == x, 'pk'].values[0])
                 for x in f if not dfd.loc[dfd['cafeteria_id'] == x, 'pk'].empty]
            meals.append(q)
            meals_recipe_num.append(f)
   
    MENU_WEEKLY = pd.DataFrame()
    MENU_WEEKLY['group'] = groups
    MENU_WEEKLY['timestamp'] = timestamps
    MENU_WEEKLY['name'] = names
    MENU_WEEKLY['items'] = meals
    MENU_WEEKLY['week_num'] = weeknums
    MENU_WEEKLY['items_recipe_num'] = meals_recipe_num

    MENU_WEEKLY['items'] = MENU_WEEKLY['items'].apply(lambda x: list(map(int, x)))
    MENU_WEEKLY.drop(MENU_WEEKLY[MENU_WEEKLY['items_recipe_num'].str.len() == 0].index, inplace=True)
    return MENU_WEEKLY, dfmw

def parse_fixture(d, out_filename):
    results = d.to_dict(orient='index')
    json_list=[]
    for r in range(len(results)):
        data = {'model': 'backend.MealSelection', 'pk': {}, 'fields': {}}
        f = results[r]
        data['pk'] = f['pk']
        for e in ['pk', 'week_num','items_recipe_num']:
            f.pop(e)
        f['school'] = SCHOOL_ID
        data['fields'] = f
        json_list.append(data)

    with open(out_filename, 'w') as out_file:
        json.dump(json_list, out_file, sort_keys=False)
    out_file.close()    

def main():
    dfd = pd.read_csv(r'master_nutrition\nutrition_table.csv', converters={'cafeteria_id': lambda x: str(x)})
    #dfm = pd.read_excel(r'menu\MenuWorks_W9-12_2022.xlsx', skiprows=11)
    dfm = pd.read_excel(r'menu\MenuWorks_W11-13_2022.xlsx', skiprows=11)

    dfm = clean_table(dfm)

    k = str(list(dfm.keys())[0])
    split_row = [0]
    for i in range(len(dfm)):
        if 'TRIM' in str(dfm.loc[int(i), k]):
            split_row.append(i)

    MENU = pd.DataFrame()
    df_master = pd.DataFrame()
    try:
        df_master = pd.read_csv(MENU_LATEST)
        df_master.to_csv(MENU_PRIOR_UPDATED,index=False) #save a backup of one version older
        df_master.drop(['pk'], axis=1, inplace=True)
        df_master['items'] = df_master['items'].apply(lambda x: eval(x))
    except:
        pass

    for mm in range(len(split_row)):
        if mm == (len(split_row)-1):
            menuw1, dfmw1 = weekly_menu_dict(dfm, dfd, split_row[mm], len(dfm))
        else:
            menuw1, dfmw1 = weekly_menu_dict(dfm, dfd, split_row[mm], split_row[mm + 1])
        MENU = pd.concat([MENU, menuw1]).reset_index(drop=True)
        

    df_master = pd.concat([df_master, MENU]).reset_index(drop=True)
    df_master.drop_duplicates(subset=['name'], keep='last',inplace=True, ignore_index=True)
    df_master ['pk'] = range(1000, 1000 + len(df_master))
    df_master.to_csv(MENU_LATEST, index=False)
    parse_fixture(df_master , OUT_FILE_PATH)    

if __name__ == '__main__':
    main()