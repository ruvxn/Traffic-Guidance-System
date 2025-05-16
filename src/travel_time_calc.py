import math

def travel_time_calculator(traffic_flow, distance, const_delay=30):

#the goal of this function is to covert predicted traffic flow in to estimation of travel time
#the quadratic function is used to calculate the speed of the vehicle

    if traffic_flow <= 351:
            speed_kmh = 60
    else:

        a = 1.4648375
        b = -93.75
        c = traffic_flow

        disc = (b**2) - (4*a*c)
        

        if disc < 0:        # if the discriminant is negative, we cannot find real roots for the quadratic fucntion.
                            #this would be considered as worst case scenario where traffic is so congested that it is not possible to travel
                            #therefore we will set the speed very low to simulate this
                            #speed will be set to 5km/h to simulate very low speed
            speed_kmh = 5
            

        else:
            sqrt_disc = math.sqrt(disc)
            speed_root_1 = (-b + sqrt_disc) / (2 * a)
            speed_root_2 = (-b - sqrt_disc) / (2 * a)

    #according to Traffic Flow to Travel Time Conversion v1.0.pdf one of the assumptions made is that 
    # "The traffic at each segment is under capacity"
    #this means the roads are not congested and we are on the free-flow side of the qudratic curve
    # therefore speed is higher and hence we take the maximum of the two roots of the function
            speed_kmh = max(speed_root_1, speed_root_2)

    # travel time in seconds
    travel_time =  (distance / speed_kmh) * 3600

    total_travel_time = travel_time + const_delay

    return round(total_travel_time,2)
