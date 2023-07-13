from v2realbot.utils.utils import isfalling, isrising

test1_threshold = 28.905
bacma = []
bacma.append([28.91])
bacma.append([28.91,28.90])
bacma.append([28.91,28.90,28.89])
bacma.append([28.91,28.90,28.89,28.88])
bacma.append([28.91,28.90,28.89,28.88,28.87])
bacma.append([28.91,28.90,28.89,28.88,28.87,28.86])


pole = [1,2,3,2,1,2,3,4,5,6,2,1]

#is_pivot function to check if there is A(V) shaped pivot in the list, each leg consists of N points
#middle point is the shared one [1,2,3,2,1] - one leg is [1,2,3] second leg is [3,2,1]
def is_pivot(stock_prices_list, leg_number, type: str = "A"):
    if len(stock_prices_list) < (2 * leg_number)-1:
        print("Not enough values in the list")
        return False
    
    left_leg = stock_prices_list[-2*leg_number+1:-leg_number+1]
    print(left_leg)
    right_leg = stock_prices_list[-leg_number:]
    print(right_leg)
    
    if type == "A":
        if isrising(left_leg) and isfalling(right_leg):
            return True
        else:
            return False
    elif type == "V":
        if isfalling(left_leg) and isrising(right_leg):
            return True
        else:
            return False
    else:
        print("Unknown type")
        return False

print(is_pivot(pole, 3))