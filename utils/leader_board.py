import string
import csv


def store_result_of_user(name: string, time: int) -> None:
    with open('leaderboard.csv', 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow([name, time])


def get_n_sorted_users_with_min_time() -> list[tuple[str, int]]:  # tuple(name, time)
    leaders_list = []
    with open('leaderboard.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            leaders_list.append((row[0], int(row[1])))
    sorted_list = sorted(leaders_list, key=lambda tup: tup[1])
    first_ten_winners = sorted_list[:10]
    return first_ten_winners # tuple(name, time)
