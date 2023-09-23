def isfalling_optimized(pole: list, pocet: int = None):
    if pocet is None: pocet = len(pole)
    if len(pole)<pocet: return False

    # Prepare the list - all same consecutive values in the list are considered as one value.
    new_pole = []
    current_value = pole[0]
    for i in range(1, len(pole)):
        if pole[i] == current_value:
            continue
        else:
            new_pole.append(current_value)
            current_value = pole[i]
    new_pole.append(current_value)

    new_pole = new_pole[-pocet:]
    print(new_pole)
    # Perform the current calculation on this list.
    res = all(i > j for i, j in zip(new_pole, new_pole[1:]))
    return res

def isfalling_optimizedgpt(pole: list, pocet: int = None):
    if pocet is None:
        pocet = len(pole)
    if len(pole) < pocet:
        return False

    # Prepare the list - all same consecutive values in the list are considered as one value.
    new_pole = [pole[0]]
    for i in range(1, len(pole)):
        if pole[i] != pole[i - 1]:
            new_pole.append(pole[i])

    if len(new_pole) < pocet:
        return False
    
    new_pole = new_pole[-pocet:]
    print(new_pole)


    # Perform the current calculation on this list.
    res = all(i > j for i, j in zip(new_pole, new_pole[1:]))
    return res

pole = [8,2,8,1,4,4,4,3,3,3,2,1]
print(isfalling_optimizedgpt(pole,5))