

test1_threshold = 28.905
bacma = []
bacma.append([28.91])
bacma.append([28.91,28.90])
bacma.append([28.91,28.90,28.89])
bacma.append([28.91,28.90,28.89,28.88])
bacma.append([28.91,28.90,28.89,28.88,28.87])
bacma.append([28.91,28.90,28.89,28.88,28.87,28.86])


#is_pivot function to check if there is A shaped pivot in the list, each leg consists of N points
def is_pivot(list, leg):
    """check if there is A shaped pivot in the list, each leg consists of N points"""
    try:
        if len(list) < leg*2+1:
            return False
        else:
            if list[-leg-1] < list[-leg] and list[-leg] > list[-leg+1] and list[-leg-1] > list[-leg-2] and list[-leg] > list[-leg+2]:
                return True
            else:
                return False
    except IndexError:
        return False



def crossed_up(threshold, list):
    """check if threshold has crossed up last thresholdue in list"""
    try:
        if threshold < list[-1] and threshold >= list[-2]:
            return True
        else:
            return False
    except IndexError:
        return False
    
def crossed_down(threshold, list):
    """check if threshold has crossed down last thresholdue in list"""
    try:
        if threshold > list[-1] and threshold <= list[-2]:
            return True
        else:
            return False
    except IndexError:
        return False

def crossed(threshold, list):
    """check if threshold has crossed last thresholdue in list"""
    if crossed_down(threshold, list) or crossed_up(threshold, list):
        return True
    else:
        return False

for i in bacma:
    print(i)
    print(f"threshold crossed down {i}", threshold_crossed_down(test1_threshold, i))
    print(f"threshold crossed up {i}", threshold_crossed_up(test1_threshold, i))




