import matplotlib.pyplot as plt
import random

# ПАРАМЕТРЫ ЗАДАВАЕМЫЕ РАБОТОДАТЕЛЕМ
CNT_OF_BUS = 10  # к-во автобусов
T_GLOBAL_COURSE = 20 * 60  #время работы автобусов (если круглосуточно - устанавливаем значение 24*60)
START_TIME = 5 * 60  # время начала работы
T_SHIFT_CHANGE = 10  # передача дел другому водителю
T_WAY = 60  # время в пути от 0ой остановки до 0ой остановки
CNT_STOPS = 16  # к-во остановок без учёта 0ой
T_LUNCH_FOR_8 = 40  # длительность обеда для водителей I типа

MIN_BUS_ON_WAY = 5  # минимальное к-во автобусов, которое должно быть не в часпиковое время

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

drivers = []
I_lunch_times = []
zero_schedule = []
bus_n_drivers = [0] * CNT_OF_BUS


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


class Driver:
    last_dr_id = 0

    def __init__(self, start_time):
        self.id = Driver.last_dr_id + 1
        Driver.last_dr_id += 1
        self.dr_type = ""
        self.start_work_time = start_time
        self.end_work_time = 0
        self.zero_point_times = [start_time]
        self.lunch_times = []
        self.bus = 0
        for i in range(CNT_OF_BUS):
            if bus_n_drivers[i] == 0:
                bus_n_drivers[i] = self.id
                self.bus = i + 1
                break
            elif i == CNT_OF_BUS and bus_n_drivers[i] != 0:
                raise Exception(f"Автобусов не хватило. Водитель {self.id} остался без автобуса.")

    def pr_info(self):
        print(f"id:{self.id} автобус:{self.bus} {self.dr_type}   нач: {convert_min(self.start_work_time)}    "
              f"пересмена: {convert_min(self.end_work_time)}      обеды/перерывы:{[convert_min(m) for m in self.lunch_times]}      "
              f"прохождение 0ой остановки:{[convert_min(m) for m in self.zero_point_times]}")


def draw_driver_schedule(dr: Driver, ax):
    if dr.dr_type == "I":
        times_arr = [[i, i + T_WAY] for i in dr.zero_point_times] + [[j, j + T_LUNCH_FOR_8] for j in dr.lunch_times]
        way_arr = [[0, CNT_STOPS + 1] for _ in dr.zero_point_times] + [[CNT_STOPS + 1, CNT_STOPS + 1] for _ in
                                                                       dr.lunch_times]
    else:
        times_arr = [[i, i + T_WAY] for i in dr.zero_point_times] + [[j, j + T_BREAK_12] for j in dr.lunch_times]
        way_arr = [[0, CNT_STOPS + 1] for _ in dr.zero_point_times] + [[0, 0] for _ in dr.lunch_times]
    color = generate_hex_color_compact()
    ax.plot(times_arr[0], way_arr[0], color=color, label=f"{dr.dr_type} driver{dr.id}")
    for t in range(1, len(times_arr)):
        ax.plot(times_arr[t], way_arr[t], color=color)


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


class Driver12(Driver):
    def __init__(self, start_time):
        Driver.__init__(self, start_time)
        self.dr_type = "II"
        self.end_work_time += min(self.start_work_time + 12 * 60 + T_BREAK_12 * CNT_OF_BREAK_12,
                                  START_TIME + T_GLOBAL_COURSE)
        self.genre_zero_points()

    def genre_zero_points(self):
        cur_t = self.start_work_time + T_WAY  # +T_WAY because [start_time] already added
        period_btwn_lunches = (12 * 60) / (CNT_OF_BREAK_12 + 1)
        # zero points from start to first break start time
        while cur_t < self.start_work_time + period_btwn_lunches and cur_t < self.end_work_time:
            self.zero_point_times.append(cur_t)
            cur_t += T_WAY
        while len(self.lunch_times) < CNT_OF_BREAK_12 and cur_t < self.end_work_time:
            self.lunch_times.append(cur_t)
            cur_t += T_BREAK_12  # driver has ated
            while (cur_t < self.lunch_times[-1] + period_btwn_lunches) and cur_t < self.end_work_time:
                self.zero_point_times.append(cur_t)
                cur_t += T_WAY


def hire_first_driver():
    global drivers, zero_schedule
    if ST_8_WORKING <= START_TIME <= END_8_WORKING:
        drivers.append(Driver8(START_TIME))
        drivers[-1].add_lunch_time(ST_LUNCH)
        I_lunch_times.append(ST_LUNCH)
        drivers[-1].genre_last_zero_points()
    else:
        drivers.append(Driver12(START_TIME))
    zero_schedule += [int(t) for t in drivers[-1].zero_point_times]


def gener_st_time_of_first_group():
    f_t = [START_TIME]
    for i in range(CNT_OF_BUS - 1):
        f_t.append(f_t[-1] + T_WAY / CNT_OF_BUS)
    result = []
    if CNT_OF_BUS == MIN_BUS_ON_WAY:
        return f_t
    de_rh_period_time = round(T_WAY // (CNT_OF_BUS - MIN_BUS_ON_WAY), 0)
    b_act = START_TIME
    for i in range(CNT_OF_BUS):
        if i == 0 or CNT_OF_BUS <= MIN_BUS_ON_WAY:
            result.append(f_t[i])
        elif i != CNT_OF_BUS - 1:
            if f_t[i + 1] >= b_act + de_rh_period_time:
                b_act += de_rh_period_time
            else:
                result.append(f_t[i])
    return result


def how_much_action_drivers(time: int):
    global drivers
    cnt = 0
    for dr in drivers:
        if dr.start_work_time <= time < dr.end_work_time:
            if dr.dr_type == "II":
                cnt += 1
            elif dr.dr_type == "I":
                if len(dr.lunch_times) > 0 and not (dr.lunch_times[0] <= time < dr.lunch_times[0] + T_LUNCH_FOR_8):
                    cnt += 1
    return cnt


def book_lunch_time(t):
    global I_lunch_times, drivers
    l_cnt = 0
    for l_t in I_lunch_times:
        if l_t <= t <= l_t + T_LUNCH_FOR_8:
            l_cnt += 1
    if l_cnt <= CNT_OF_BUS // 4:
        return True
    return False


def hire_first_group():
    global drivers, zero_schedule
    st_times_arr = gener_st_time_of_first_group()
    if len(st_times_arr) > 1:
        st_times_arr2 = st_times_arr[1:]
        for st_t in st_times_arr2:
            if ST_8_WORKING <= st_t <= END_8_WORKING:
                drivers.append(Driver8(st_t))
            else:
                drivers.append(Driver12(st_t))
        for i in range(1, len(drivers)):
            dr = drivers[i]
            if dr.dr_type == "I":
                cur_t = dr.zero_point_times[-1] + T_WAY
                while cur_t <= END_LUNCH:
                    if book_lunch_time(cur_t):
                        dr.add_lunch_time(cur_t)
                        I_lunch_times.append(cur_t)
                        dr.genre_last_zero_points()
                        break

                    if cur_t + T_WAY > END_LUNCH:
                        dr.add_lunch_time(cur_t)
                        I_lunch_times.append(cur_t)
                        dr.genre_last_zero_points()
                        break
                    dr.zero_point_times.append(cur_t)
                    cur_t += T_WAY
            zero_schedule += [int(t) for t in dr.zero_point_times]


def hire_drivers_morning_RH():
    global zero_schedule
    zero_schedule.sort()
    rh_period = T_WAY / CNT_OF_BUS
    for i in range(len(zero_schedule) - 1):
        if len(drivers) == CNT_OF_BUS:
            break
        next_t = zero_schedule[i] + T_BREAK_12 * 1.1
        if RH_MORNING_START - rh_period <= next_t <= RH_MORNING_START + RH_LONG:
            if zero_schedule[i + 1] - zero_schedule[i] > rh_period * 1.5:
                if ST_8_WORKING <= next_t + rh_period <= END_8_WORKING:
                    drivers.append(Driver8(next_t + rh_period))
                else:
                    drivers.append(Driver12(next_t + rh_period))
                if drivers[-1].dr_type == "I":
                    cur_t = drivers[-1].zero_point_times[-1] + T_WAY
                    while cur_t <= END_LUNCH:
                        if book_lunch_time(cur_t):
                            drivers[-1].add_lunch_time(cur_t)
                            I_lunch_times.append(cur_t)
                            drivers[-1].genre_last_zero_points()
                            break
                        if cur_t + T_WAY > END_LUNCH:
                            drivers[-1].add_lunch_time(cur_t)
                            I_lunch_times.append(cur_t)
                            drivers[-1].genre_last_zero_points()
                            break
                        drivers[-1].zero_point_times.append(cur_t)
                        cur_t += T_WAY
                zero_schedule += [int(t) for t in drivers[-1].zero_point_times]
                zero_schedule.sort()


def hire_second_group():
    global drivers, zero_schedule, bus_n_drivers
    e_t = []
    for dr in drivers:
        e_t.append(dr.end_work_time)
    e_t.sort()
    for t in e_t:
        for dr in drivers:
            if dr.end_work_time == t:
                bus_n_drivers[dr.bus - 1] = 0
                break
        if RH_EVENING_START <= t + T_SHIFT_CHANGE < RH_EVENING_START + RH_LONG and how_much_action_drivers(
                t + T_SHIFT_CHANGE) < CNT_OF_BUS:
            if ST_8_WORKING <= t + T_SHIFT_CHANGE <= END_8_WORKING:
                drivers.append(Driver8(t + T_SHIFT_CHANGE))
            else:
                drivers.append(Driver12(t + T_SHIFT_CHANGE))
        elif RH_MORNING_START + RH_LONG < t + T_SHIFT_CHANGE < RH_EVENING_START and how_much_action_drivers(
                t + T_SHIFT_CHANGE) < MIN_BUS_ON_WAY:
            if ST_8_WORKING <= t + T_SHIFT_CHANGE <= END_8_WORKING:
                drivers.append(Driver8(t + T_SHIFT_CHANGE))
            else:
                drivers.append(Driver12(t + T_SHIFT_CHANGE))
        else:
            continue
        if drivers[-1].dr_type == "I":
            cur_t = drivers[-1].zero_point_times[-1] + T_WAY
            while cur_t <= END_LUNCH:
                if book_lunch_time(cur_t):
                    drivers[-1].add_lunch_time(cur_t)
                    I_lunch_times.append(cur_t)
                    drivers[-1].genre_last_zero_points()
                    break

                if cur_t + T_WAY > END_LUNCH:
                    drivers[-1].add_lunch_time(cur_t)
                    I_lunch_times.append(cur_t)
                    drivers[-1].genre_last_zero_points()
                    break
                drivers[-1].zero_point_times.append(cur_t)
                cur_t += T_WAY
        zero_schedule += [int(t) for t in drivers[-1].zero_point_times]
        zero_schedule.sort()


def refactor_evening_schedule():
    global drivers
    drivers2 = []
    z_p = []
    for dr in drivers:
        if dr.dr_type == "II":
            drivers2.append(dr)
            z_p += dr.zero_point_times
    z_p.sort()
    if z_p[0] == START_TIME and z_p[-1] + T_WAY >= START_TIME + T_GLOBAL_COURSE:
        return drivers2
    drivers2 = []
    cnt_12 = 0
    for dr in drivers:
        if dr.dr_type == "II":
            cnt_12 += 1
    f_t = []
    for i in range(cnt_12):
        f_t.append(START_TIME + i * (T_GLOBAL_COURSE - (12 * 60 + T_BREAK_12 * CNT_OF_BREAK_12)) / (cnt_12 - 1))
    for t in f_t:
        drivers2.append(Driver12(t))
    return drivers2


def print_stop_shedule(num_station: int):
    global zero_schedule
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


def print_statistic():
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


def main_function():
    global drivers, I_lunch_times, zero_schedule
    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(18, 10))  # Ширина 12 дюймов, высота 4 дюйма
    axes[0].add_patch(plt.Rectangle((RH_MORNING_START, 0), RH_LONG, CNT_STOPS + 1, color='gray', alpha=0.5))
    axes[0].add_patch(plt.Rectangle((RH_EVENING_START, 0), RH_LONG, CNT_STOPS + 1, color='gray', alpha=0.5))
    axes[0].add_patch(plt.Rectangle((ST_LUNCH, 0), END_LUNCH - ST_LUNCH, CNT_STOPS + 1, color='green', alpha=0.5))
    #random.seed(678)
    #random.seed(675)
    random.seed(673)
    # MAIN BODY########################################################################
    hire_first_driver()
    hire_first_group()
    hire_drivers_morning_RH()
    hire_second_group()
    print_statistic()
    print_stop_shedule(2)
    # END MAIN BODY####################################################################
    for dr in drivers:
        draw_driver_schedule(dr, axes[0])
        dr.pr_info()
    ###under that line code draw a graph  DONT TOUCH!!!###########################################
    time_x_minutes = [30 * i for i in range(START_TIME // 30, (START_TIME + T_GLOBAL_COURSE) // 30 + 2)]
    y_stations = [i for i in range(CNT_STOPS + 2)]
    axes[0].set_xticks(time_x_minutes, [convert_min(m) for m in time_x_minutes], rotation=85,
                       ha="right")  # Поворачиваем подписи для удобства чтения
    axes[0].set_yticks(y_stations, ["Zero station"] + ["Station " + str(i) for i in range(1, CNT_STOPS + 1)] +
                       ["Zero station"])  # Поворачиваем подписи для удобства чтения
    axes[0].set_xlim(30 * (START_TIME // 30 - 1), 30 * ((START_TIME + T_GLOBAL_COURSE) // 30 + 2))
    axes[0].set_title("График работы водителей (ПН - ПТ)")
    axes[0].grid(True)
    axes[0].legend()
    for dr in refactor_evening_schedule():
        draw_driver_schedule(dr, axes[1])
    axes[1].set_xticks(time_x_minutes, [convert_min(m) for m in time_x_minutes], rotation=85,
                       ha="right")  # Поворачиваем подписи для удобства чтения
    axes[1].set_yticks(y_stations, ["Zero station"] + ["Station " + str(i) for i in range(1, CNT_STOPS + 1)] +
                       ["Zero station"])  # Поворачиваем подписи для удобства чтения
    axes[1].set_xlim(30 * (START_TIME // 30 - 1), 30 * ((START_TIME + T_GLOBAL_COURSE) // 30 + 2))
    axes[1].set_title("График работы водителей (СБ, ВС)")
    axes[1].grid(True)
    axes[1].legend()
    plt.show()


main_function()
