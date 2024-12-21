import matplotlib.pyplot as plt
import random

# ПАРАМЕТРЫ ЗАДАВАЕМЫЕ РАБОТОДАТЕЛЕМ
CNT_OF_BUS = 30  # к-во автобусов
T_GLOBAL_COURSE = 20 * 60  #время работы автобусов (если круглосуточно - устанавливаем значение 24*60)
START_TIME = 5 * 60  # время начала работы
T_SHIFT_CHANGE = 10  # передача дел другому водителю
T_WAY = 60  # время в пути от 0ой остановки до 0ой остановки
CNT_STOPS = 16  # к-во остановок без учёта 0ой
T_LUNCH_FOR_8 = 40  # длительность обеда для водителей I типа

#ПАРАМЕТРЫ ГЕНЕТИЧЕСКОГО АЛГОРИТМА
CNT_ITER = 100  #к-во поколений
SIZE_OF_POPULATION = 50  # размер популяции
BREED_PROBABILITY = 0.9  # шанс кроссинговера
MUTATION_PROBABILITY = 0.1  # шанс мутации
I_TYPE_PROBABILITY = (8*60)/T_GLOBAL_COURSE #вероятность наёма водителя I типа

# ПАРАМЕТРЫ ТРУДОВОГО КОДЕКСА
T_BREAK_12 = 10
CNT_OF_BREAK_12 = 3
ST_8_WORKING = 6 * 60
END_8_WORKING = 10 * 60
# RH - rush hour
RH_LONG = 2 * 60
RH_MORNING_START = 7 * 60
RH_EVENING_START = 17 * 60

ST_LUNCH = 13 * 60
END_LUNCH = 15 * 60


MIN_BUS_ON_WAY = 5  # минимальное к-во автобусов, которое должно быть не в часпиковое время


def generate_hex_color_compact():
    return '#' + ''.join(random.choices('0123456789abcdef', k=6))


def convert_min(m):
    if (m // 60) % 24 < 10:
        h = "0" + str(int(m // 60) % 24)
    else:
        h = str(int(m // 60) % 24)
    if m % 60 < 10:
        mn = "0" + str(int(m % 60))
    else:
        mn = str(int(m % 60))
    return h + ":" + mn


def convert_min_arr(array):
    result = []
    for a in array:
        result.append(convert_min(a))
    return result


def how_much_action_drivers(drivers, time_: int):
    cnt = 0
    for dr in drivers:
        if dr.start_work_time <= time_ < dr.end_work_time:
            if dr.dr_type == "I" and not(dr.lunch_times[0] <= time_ <= dr.lunch_times[0]+T_LUNCH_FOR_8):
                cnt += 1
            elif dr.dr_type == "II":
                cnt += 1
    return cnt


def generate_random_driver():
    if random.random() < I_TYPE_PROBABILITY:
        t = random.randint(ST_8_WORKING, END_8_WORKING)
        return Driver8(t)
    t = random.randint(START_TIME + 1, START_TIME + T_GLOBAL_COURSE - 12*60)
    return Driver12(t)


def calc_rh_profit(drivers_array):
    rh_morning = 0
    rh_evening = 0
    period_btwn_stops = T_WAY / CNT_STOPS
    for dr in drivers_array:
        for t in dr.zero_point_times:
            for i in range(CNT_STOPS):
                if RH_MORNING_START <= t + i * period_btwn_stops <= RH_MORNING_START + RH_LONG:
                    rh_morning += 1
                elif RH_EVENING_START <= t + i * period_btwn_stops <= RH_EVENING_START + RH_LONG:
                    rh_evening += 1
    return min(rh_morning, rh_evening)


def calculate_fitness(drivers_array):
    fitness = calc_rh_profit(drivers_array)*5
    max_dr = 0
    st_dr = []
    for dr in drivers_array:
        if dr.start_work_time not in st_dr:
            st_dr.append(dr.start_work_time)
        else:
            fitness -= 100
    for t in range(START_TIME, START_TIME + T_GLOBAL_COURSE + 1):
        max_dr = max(max_dr, how_much_action_drivers(drivers_array, t))
        if RH_MORNING_START <= t <= RH_MORNING_START+RH_LONG or RH_EVENING_START <= t <= RH_EVENING_START+RH_LONG:
            if how_much_action_drivers(drivers_array, t) < CNT_OF_BUS:
                fitness -= 1
        elif how_much_action_drivers(drivers_array, t) > MIN_BUS_ON_WAY:
            fitness -= 1
        if max_dr > CNT_OF_BUS:
            fitness -= 10000
            break
    return fitness


class Driver:

    def __init__(self, start_time):
        self.dr_type = ""
        self.start_work_time = start_time
        self.end_work_time = 0
        self.zero_point_times = [start_time]
        self.lunch_times = []

    def pr_info(self):
        print(f"{self.dr_type}   "
              f"нач: {convert_min(self.start_work_time)}    "
              f"пересмена: {convert_min(self.end_work_time)}      "
              f"обеды/перерывы:{[convert_min(m) for m in self.lunch_times]}      "
              f"прохождение 0ой остановки:{[convert_min(m) for m in self.zero_point_times]}")


class Driver12(Driver):
    def __init__(self, start_time):
        Driver.__init__(self, start_time)
        self.dr_type = "II"
        self.end_work_time += min(self.start_work_time + 12 * 60 + T_BREAK_12 * CNT_OF_BREAK_12,
                                  START_TIME + T_GLOBAL_COURSE)
        self.genre_zero_points()

    def genre_zero_points(self):
        cur_t = self.start_work_time + T_WAY
        period_btwn_lunches = (12 * 60) / (CNT_OF_BREAK_12 + 1)
        while cur_t < self.start_work_time + period_btwn_lunches and cur_t < self.end_work_time:
            self.zero_point_times.append(cur_t)
            cur_t += T_WAY
        while len(self.lunch_times) < CNT_OF_BREAK_12 and cur_t < self.end_work_time:
            self.lunch_times.append(cur_t)
            cur_t += T_BREAK_12  # driver has ated
            while (cur_t < self.lunch_times[-1] + period_btwn_lunches) and cur_t < self.end_work_time:
                self.zero_point_times.append(cur_t)
                cur_t += T_WAY


class Driver8(Driver):
    def __init__(self, start_time):
        Driver.__init__(self, start_time)
        self.dr_type = "I"
        self.end_work_time += self.start_work_time + 8 * 60 + T_LUNCH_FOR_8
        self.genre_zero_points()

    def genre_zero_points(self):
        # zero points from start to lunch start time
        cur_t = self.start_work_time + T_WAY
        while cur_t < ST_LUNCH:
            self.zero_point_times.append(cur_t)
            cur_t += T_WAY

    def add_lunch_time(self, lunch_time):
        self.lunch_times.append(lunch_time)

    def genre_last_zero_points(self):
        if self.lunch_times:
            cur_t = self.lunch_times[0] + T_LUNCH_FOR_8
            while cur_t < self.end_work_time:
                self.zero_point_times.append(cur_t)
                cur_t += T_WAY


def book_lunch_time(drivers, t):
    I_lunch_times = []
    for dr in drivers:
        if dr.dr_type == "I":
            if dr.lunch_times:
                I_lunch_times.append(dr.lunch_times[0])
    l_cnt = 0
    for l_t in I_lunch_times:
        if l_t <= t <= l_t + T_LUNCH_FOR_8:
            l_cnt += 1
    if l_cnt <= CNT_OF_BUS // 4:
        return True
    return False


def set_lunch_times(drivers):
    for dr in drivers:
        if dr.dr_type == "I":
            for r in range(len(dr.zero_point_times)):
                if dr.zero_point_times[r] >= ST_LUNCH:
                    dr.zero_point_times = dr.zero_point_times[:r]
                    dr.lunch_times = []
                    break
            cur_t = dr.zero_point_times[-1] + T_WAY
            while cur_t <= END_LUNCH:
                if book_lunch_time(drivers, cur_t):
                    dr.add_lunch_time(cur_t)
                    dr.genre_last_zero_points()
                    break
                if cur_t + T_WAY > END_LUNCH:
                    dr.add_lunch_time(cur_t)
                    dr.genre_last_zero_points()
                    break
                dr.zero_point_times.append(cur_t)
                cur_t += T_WAY


def draw_driver_schedule(dr: Driver, ax):
    if dr.dr_type == "I":
        times_arr = [[i, i + T_WAY] for i in dr.zero_point_times] + [[j, j + T_LUNCH_FOR_8] for j in dr.lunch_times]
        way_arr = [[0, CNT_STOPS + 1] for _ in dr.zero_point_times] + [[CNT_STOPS + 1, CNT_STOPS + 1] for _ in
                                                                       dr.lunch_times]
    else:
        times_arr = [[i, i + T_WAY] for i in dr.zero_point_times] + [[j, j + T_BREAK_12] for j in dr.lunch_times]
        way_arr = [[0, CNT_STOPS + 1] for _ in dr.zero_point_times] + [[0, 0] for _ in dr.lunch_times]
    color = generate_hex_color_compact()
    ax.plot(times_arr[0], way_arr[0], color=color, label=f"{dr.dr_type} driver")
    for t in range(1, len(times_arr)):
        ax.plot(times_arr[t], way_arr[t], color=color)


def print_stop_shedule(zero_schedule, num_station: int):
    print(f"РАСПИСАНИЕ ОСТАНОВКИ №{num_station}")
    station_period = T_WAY / (CNT_STOPS + 1)
    result = []
    for t in zero_schedule:
        result.append(convert_min(int(t + station_period * num_station)))
    output_string = ""
    for i, item in enumerate(result):
        output_string += str(item) + " "
        if (i + 1) % 20 == 0:
            print(output_string.strip())
            output_string = ""
    if output_string:
        print(output_string.strip())


def print_12_mounth_schedule():
    print("            пн   вт   ср   чт   пт   сб   вс ")
    print("1ая неделя: -1-  -2-  -3-  -1-  -2-  -3-  -1-")
    print("2ая неделя: -2-  -3-  -1-  -2-  -3-  -1-  -2-")
    print("3ья неделя: -3-  -1-  -2-  -3-  -1-  -2-  -3-")
    print(". . . . . . . . . . . . . . . . . . . . . . .")


def tour_selection(schedules):
    selected_schedules = []
    for _ in range(len(schedules)):
        r1 = random.randint(0, len(schedules) - 1)
        r2 = random.randint(0, len(schedules) - 1)
        while r2 == r1:
            r2 = random.randint(0, len(schedules) - 1)
        r3 = random.randint(0, len(schedules) - 1)
        while r3 == r2 or r3 == r1:
            r3 = random.randint(0, len(schedules) - 1)
        s1 = schedules[r1]
        s2 = schedules[r2]
        s3 = schedules[r3]
        if s1["fit"] == max(s1["fit"], s2["fit"], s3["fit"]):
            selected_schedules.append(s1)
        elif s2["fit"] == max(s1["fit"], s2["fit"], s3["fit"]):
            selected_schedules.append(s2)
        else:
            selected_schedules.append(s3)
    return selected_schedules


def breed_n_mutate_time(schedules):
    for child1, child2 in zip(schedules[::2], schedules[1::2]):
        if random.random() < BREED_PROBABILITY:
            s = random.randint(2, CNT_OF_BUS - 2)
            ch_ = child2["sch"][s:]
            child2["sch"][s:] = child1["sch"][s:]
            child1["sch"][s:] = ch_
    for mutant in schedules:
        if random.random() < MUTATION_PROBABILITY:
            r = random.randint(2, CNT_OF_BUS - 1)
            mutant["sch"][r] = generate_random_driver()
    for sch in schedules:
        set_lunch_times(sch["sch"])


def print_statistic(drivers):
    cnt_8 = 0
    cnt_12 = 0
    for dr in drivers:
        if dr.dr_type == "I":
            cnt_8 += 1
        else:
            cnt_12 += 3
    print(f"Итого необходимо нанять 8-часовых водиителей: {cnt_8}")
    print(f"Итого необходимо нанять 12-часовых водиителей: {cnt_12}  (3 набора по {cnt_12 // 3} водителей, "
          f"расписание наборов смотри ниже)")
    print_12_mounth_schedule()


def genetic_main():
    fig, ax = plt.subplots(figsize=(18, 5))
    ax.add_patch(plt.Rectangle((RH_MORNING_START, 0), RH_LONG, CNT_STOPS + 1, color='gray', alpha=0.5))
    ax.add_patch(plt.Rectangle((RH_EVENING_START, 0), RH_LONG, CNT_STOPS + 1, color='gray', alpha=0.5))
    schedules = []
    num_of_iter = 0
    for ind in range(SIZE_OF_POPULATION):
        drivers = [Driver12(START_TIME),
                   Driver12(START_TIME + T_GLOBAL_COURSE - 12 * 60 - CNT_OF_BREAK_12 * T_BREAK_12)]
        for _ in range(CNT_OF_BUS - 2):
            drivers.append(generate_random_driver())
            set_lunch_times(drivers)
        fit = calculate_fitness(drivers)
        schedules.append({"sch": drivers, "fit": fit})
    while num_of_iter < CNT_ITER:
        schedules = tour_selection(schedules)
        breed_n_mutate_time(schedules)
        for sch in schedules:
            sch["fit"] = calculate_fitness(sch["sch"])
        num_of_iter += 1

    max_fit = -100000000000
    for sch in schedules:
        max_fit = max(max_fit, sch["fit"])
    z_p_sch = []

    for sch in schedules:
        if max_fit == sch["fit"]:
            sch["sch"].sort(key=lambda dr_: dr_.start_work_time)
            print_statistic(sch["sch"])
            for dr in sch["sch"]:
                z_p_sch += dr.zero_point_times
                draw_driver_schedule(dr, ax)
                dr.pr_info()
            print(f"Оптимальность лучшего алгоритма: {sch['fit']}")
            break
    z_p_sch.sort()
    print_stop_shedule(z_p_sch, 2)
    time_x_minutes = [30 * i for i in range(START_TIME // 30, (START_TIME + T_GLOBAL_COURSE) // 30 + 2)]
    y_stations = [i for i in range(CNT_STOPS + 2)]
    # Установка меток на оси X
    ax.set_xticks(time_x_minutes, [convert_min(m) for m in time_x_minutes], rotation=85,
                  ha="right")  # Поворачиваем подписи для удобства чтения
    ax.set_yticks(y_stations, ["Zero station"] + ["Station " + str(i) for i in range(1, CNT_STOPS + 1)] +
                  ["Zero station"])  # Поворачиваем подписи для удобства чтения
    ax.set_xlim(30 * (START_TIME // 30 - 1), 30 * ((START_TIME + T_GLOBAL_COURSE) // 30 + 2))
    ax.set_title("График работы водителей (ПН - ВС)")
    ax.grid(True)
    ax.legend()
    plt.show()


genetic_main()
