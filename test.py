from data_scripts import calories

today_maintainace=calories.get_maintainance()
if today_maintainace:
    print("Today's maintainace is, ",today_maintainace,"Kcal")
